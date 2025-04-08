import os
import pyotp
import pandas as pd
from SmartApi.smartConnect import SmartConnect
from datetime import datetime, timedelta

# Load environment variables
api_key = os.getenv("ANGEL_API_KEY")
client_code = os.getenv("ANGEL_CLIENT_CODE")
password = os.getenv("ANGEL_PASSWORD")
totp_secret = os.getenv("ANGEL_TOTP_SECRET")

# Validate env variables
if not all([api_key, client_code, password, totp_secret]):
    raise Exception("Missing one or more required environment variables: ANGEL_API_KEY, ANGEL_CLIENT_CODE, ANGEL_PASSWORD, ANGEL_TOTP_SECRET")

# Generate OTP
totp = pyotp.TOTP(totp_secret).now()

# Login
obj = SmartConnect(api_key=api_key)
session = obj.generateSession(client_code, password, totp)
if not session or 'status' not in session or session['status'] != True:
    raise Exception(f"Angel One login failed: {session}")

# Tokens
auth_token = session['data']['jwtToken']
refresh_token = session['data']['refreshToken']
feed_token = obj.getfeedToken()

# Load instruments.csv
instruments_df = pd.read_csv("instruments.csv")

# Utility: Get token by symbol
def get_instrument_token(symbol):
    try:
        row = instruments_df[
            (instruments_df["symbol"].str.upper() == symbol.upper()) &
            (instruments_df["exch_seg"] == "NSE")
        ].iloc[0]
        return str(row["token"])
    except Exception as e:
        print(f"Token error for {symbol}: {e}")
        return None

# Utility: Historical data
def get_historical_data(token, interval, from_date, to_date, exchange="NSE"):
    params = {
        "exchange": exchange,
        "symboltoken": str(token),
        "interval": interval,
        "fromdate": from_date.strftime('%Y-%m-%d %H:%M'),
        "todate": to_date.strftime('%Y-%m-%d %H:%M')
    }
    try:
        candles = obj.getCandleData(params)
        df = pd.DataFrame(candles['data'], columns=["datetime", "open", "high", "low", "close", "volume"])
        df["datetime"] = pd.to_datetime(df["datetime"])
        df[["open", "high", "low", "close", "volume"]] = df[["open", "high", "low", "close", "volume"]].astype(float)
        return df
    except Exception as e:
        print(f"Error fetching data: {e}")
        return None

# Utility: Get LTP
def get_ltp(symbol, exchange="NSE"):
    token = get_instrument_token(symbol)
    if not token:
        return None
    try:
        response = obj.ltpData(exchange=exchange, tradingsymbol=symbol, symboltoken=token)
        return float(response['data']['ltp'])
    except Exception as e:
        print(f"LTP error for {symbol}: {e}")
        return None
