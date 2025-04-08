# angel_login.py
import os
import pyotp
import pandas as pd
from SmartApi.smartConnect import SmartConnect
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()

# Load environment variables
api_key = os.getenv("ANGEL_API_KEY")
client_code = os.getenv("ANGEL_CLIENT_CODE")
password = os.getenv("ANGEL_PASSWORD")
totp_secret = os.getenv("ANGEL_TOTP_SECRET")

# Validate env vars
if not all([api_key, client_code, password, totp_secret]):
    raise Exception("Missing one or more required environment variables.")

# Login
totp = pyotp.TOTP(totp_secret).now()
obj = SmartConnect(api_key=api_key)
session = obj.generateSession(client_code, password, totp)

if not session or 'status' not in session or session['status'] != True:
    raise Exception(f"Angel One login failed: {session}")

auth_token = session['data']['jwtToken']
refresh_token = session['data']['refreshToken']
feed_token = obj.getfeedToken()

# Load instruments
instruments_df = pd.read_csv("instruments.csv")

# Token Lookup
def get_instrument_token(df, symbol, exch_seg="NFO"):
    try:
        row = df[
            (df["trading_symbol"].str.startswith(symbol)) &
            (df["exch_seg"] == exch_seg)
        ].iloc[0]
        return str(row["token"])
    except Exception as e:
        print(f"Error finding token for {symbol}: {e}")
        return None

# Historical data fetcher
def get_historical_data(token, interval, from_date, to_date, exchange="NFO"):
    params = {
        "exchange": exchange,
        "symboltoken": str(token),
        "interval": interval,
        "fromdate": from_date.strftime('%Y-%m-%d %H:%M'),
        "todate": to_date.strftime('%Y-%m-%d %H:%M')
    }
    try:
        candles = obj.getCandleData(params)
        data = candles.get("data", [])
        df = pd.DataFrame(data, columns=["datetime", "open", "high", "low", "close", "volume"])
        df["datetime"] = pd.to_datetime(df["datetime"])
        df[["open", "high", "low", "close", "volume"]] = df[["open", "high", "low", "close", "volume"]].astype(float)
        return df
    except Exception as e:
        print(f"Error getting historical data: {e}")
        return pd.DataFrame()

# LTP fetcher
def get_ltp(symbol, exch_seg="NFO"):
    token = get_instrument_token(instruments_df, symbol, exch_seg)
    if not token:
        return None
    try:
        response = obj.ltpData(exchange=exch_seg, tradingsymbol=symbol, symboltoken=token)
        return float(response['data']['ltp'])
    except Exception as e:
        print(f"LTP fetch failed: {e}")
        return None
