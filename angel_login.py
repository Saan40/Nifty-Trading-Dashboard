# angel_login.py
import os
import pyotp
import pandas as pd
from SmartApi.smartConnect import SmartConnect
from datetime import datetime

# Load environment variables
api_key = os.getenv("ANGEL_API_KEY")
client_code = os.getenv("ANGEL_CLIENT_CODE")
password = os.getenv("ANGEL_PASSWORD")
totp_secret = os.getenv("ANGEL_TOTP_SECRET")  # 26-character secret

# Validate all required env vars are set
if not all([api_key, client_code, password, totp_secret]):
    raise Exception("Missing one or more required environment variables: ANGEL_API_KEY, ANGEL_CLIENT_CODE, ANGEL_PASSWORD, ANGEL_TOTP_SECRET")

# Generate TOTP
totp = pyotp.TOTP(totp_secret).now()

# Create API object and login
obj = SmartConnect(api_key=api_key)
session = obj.generateSession(client_code, password, totp)

if not session or 'status' not in session or session['status'] != True:
    raise Exception(f"Angel One login failed! Response: {session}")

# Save tokens
auth_token = session['data']['jwtToken']
refresh_token = session['data']['refreshToken']
feed_token = obj.getfeedToken()

# Load instrument master
instruments_df = pd.read_csv("instruments.csv")

# Utility: Get latest weekly token for NIFTY or BANKNIFTY
def get_instrument_token(symbol):
    df = instruments_df[(instruments_df['exch_seg'] == 'NFO') & (instruments_df['name'] == symbol)]
    df['expiry'] = pd.to_datetime(df['expiry'], errors='coerce')
    df = df[df['expiry'] >= pd.Timestamp(datetime.now().date())]
    if df.empty:
        raise Exception("No matching instruments found.")
    nearest = df.sort_values(by='expiry').iloc[0]
    return {
        'token': str(nearest['token']),
        'symbol': nearest['trading_symbol'],
        'exchange': nearest['exch_seg']
    }

# Utility: Get LTP
def get_ltp(token_info):
    try:
        response = obj.ltpData(
            exchange=token_info['exchange'],
            tradingsymbol=token_info['symbol'],
            symboltoken=token_info['token']
        )
        return float(response['data']['ltp'])
    except Exception as e:
        print(f"LTP fetch error: {e}")
        return None

# Utility: Get historical candle data
def get_historical_data(token_info, interval, from_date, to_date):
    params = {
        "exchange": token_info['exchange'],
        "symboltoken": token_info['token'],
        "interval": interval,
        "fromdate": from_date.strftime('%Y-%m-%d %H:%M'),
        "todate": to_date.strftime('%Y-%m-%d %H:%M')
    }
    try:
        candles = obj.getCandleData(params)
        if not candles['data']:
            raise Exception("No candle data received.")
        df = pd.DataFrame(candles['data'], columns=["datetime", "open", "high", "low", "close", "volume"])
        df['datetime'] = pd.to_datetime(df['datetime'])
        return df
    except Exception as e:
        raise Exception(f"Candle fetch error: {e}")
