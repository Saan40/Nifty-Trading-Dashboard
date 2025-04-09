import os
import pyotp
import pandas as pd
from SmartApi.smartConnect import SmartConnect
from datetime import datetime, timedelta

# Load environment variables
api_key = os.getenv("ANGEL_API_KEY")
client_code = os.getenv("ANGEL_CLIENT_CODE")
password = os.getenv("ANGEL_PASSWORD")
totp_secret = os.getenv("ANGEL_TOTP_SECRET")  # 26-char secret

if not all([api_key, client_code, password, totp_secret]):
    raise Exception("Missing one or more required environment variables.")

# Generate TOTP
totp = pyotp.TOTP(totp_secret).now()

# Login
obj = SmartConnect(api_key=api_key)
session = obj.generateSession(client_code, password, totp)

if not session or 'status' not in session or session['status'] is not True:
    raise Exception(f"Login failed. Full response: {session}")

# Save tokens
auth_token = session['data']['jwtToken']
refresh_token = session['data']['refreshToken']
feed_token = obj.getfeedToken()

# Load instruments CSV
instruments_df = pd.read_csv("instruments.csv")

# Utility to get token
def get_instrument_token(df, symbol, exch_seg):
    try:
        row = df[(df['trading_symbol'].str.contains(symbol)) & (df['exch_seg'] == exch_seg)].iloc[0]
        return str(row["token"])
    except Exception as e:
        print(f"Token lookup failed for {symbol} on {exch_seg}: {e}")
        return None

# Utility to get LTP
def get_ltp(symbol, exch_seg):
    token = get_instrument_token(instruments_df, symbol, exch_seg)
    if not token:
        return None
    try:
        data = obj.ltpData(exchange=exch_seg, tradingsymbol=symbol, symboltoken=token)
        return float(data["data"]["ltp"])
    except Exception as e:
        print(f"LTP fetch failed: {e}")
        return None

# Historical data
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
        data = candles['data']
        df = pd.DataFrame(data, columns=["datetime", "open", "high", "low", "close", "volume"])
        df["datetime"] = pd.to_datetime(df["datetime"])
        return df
    except Exception as e:
        print(f"Historical fetch failed: {e}")
        return pd.DataFrame()
