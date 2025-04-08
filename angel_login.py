import os
import pyotp
import pandas as pd
from SmartApi.smartConnect import SmartConnect
from datetime import datetime, timedelta

# Load environment variables
api_key = os.getenv("ANGEL_API_KEY")
client_code = os.getenv("ANGEL_CLIENT_CODE")
password = os.getenv("ANGEL_PASSWORD")
totp_secret = os.getenv("ANGEL_TOTP_SECRET")  # 26-character TOTP secret

# Validate environment
if not all([api_key, client_code, password, totp_secret]):
    raise Exception("Missing one or more required environment variables.")

# Generate TOTP
totp = pyotp.TOTP(totp_secret).now()

# Login
obj = SmartConnect(api_key=api_key)
session = obj.generateSession(client_code, password, totp)

if not session or 'status' not in session or session['status'] != True:
    raise Exception(f"Angel One login failed: {session}")

# Save tokens
auth_token = session['data']['jwtToken']
feed_token = obj.getfeedToken()

# Load instruments
instruments_df = pd.read_csv("instruments.csv")

# Get token from instrument CSV
def get_instrument_token(df, symbol, exch_seg="NFO"):
    try:
        row = df[(df["trading_symbol"].str.startswith(symbol)) & (df["exch_seg"] == exch_seg)].iloc[0]
        return str(row["token"])
    except Exception as e:
        print(f"Error finding token for {symbol}: {e}")
        return None

# Get historical candle data
def get_historical_data(token, interval, from_date, to_date, exchange="NFO"):
    params = {
        "exchange": exchange,
        "symboltoken": str(token),
        "interval": interval,
        "fromdate": from_date.strftime('%Y-%m-%d %H:%M'),
        "todate": to_date.strftime('%Y-%m-%d %H:%M')
    }
    try:
        data = obj.getCandleData(params)
        candles = data["data"]
        df = pd.DataFrame(candles, columns=["datetime", "open", "high", "low", "close", "volume"])
        df["datetime"] = pd.to_datetime(df["datetime"])
        df[["open", "high", "low", "close", "volume"]] = df[["open", "high", "low", "close", "volume"]].astype(float)
        return df
    except Exception as e:
        raise Exception(f"Error fetching historical data: {e}")

# Get LTP
def get_ltp(symbol, exch_seg="NFO"):
    token = get_instrument_token(instruments_df, symbol, exch_seg)
    if not token:
        return None
    try:
        res = obj.ltpData(exchange=exch_seg, tradingsymbol=symbol, symboltoken=token)
        return float(res["data"]["ltp"])
    except Exception as e:
        print(f"LTP fetch error: {e}")
        return None
