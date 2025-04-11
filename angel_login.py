import os
import pyotp
import pandas as pd
from SmartApi.smartConnect import SmartConnect
from datetime import datetime

# Load environment variables
api_key = os.getenv("ANGEL_API_KEY")
client_code = os.getenv("ANGEL_CLIENT_CODE")
password = os.getenv("ANGEL_PASSWORD")
totp_secret = os.getenv("ANGEL_TOTP_SECRET")

if not all([api_key, client_code, password, totp_secret]):
    raise Exception("Missing one or more environment variables")

# Generate TOTP
totp = pyotp.TOTP(totp_secret).now()

# Create session
obj = SmartConnect(api_key=api_key)
session = obj.generateSession(client_code, password, totp)
if not session or 'data' not in session or 'jwtToken' not in session['data']:
    raise Exception("Login failed or token missing: {}".format(session))

auth_token = session['data']['jwtToken']
feed_token = obj.getfeedToken()

# Load instruments
instruments_df = pd.read_csv("instruments.csv")

def get_instrument_token(symbol):
    try:
        df = instruments_df[
            (instruments_df['symbol'] == symbol) & 
            (instruments_df['exch_seg'] == 'NFO')
        ]
        df['expiry_date'] = df['symbol'].str.extract(r'(\d{2}[A-Z]{3}\d{2})')
        df['expiry_date'] = pd.to_datetime(df['expiry_date'], format='%d%b%y', errors='coerce')
        df = df.dropna(subset=['expiry_date'])
        upcoming = df[df['expiry_date'] >= pd.Timestamp(datetime.now())]
        nearest = upcoming.sort_values('expiry_date').iloc[0]
        return {
            "token": str(nearest['token']),
            "symbol": nearest['symbol'],
            "exch_seg": nearest['exch_seg']
        }
    except Exception as e:
        print(f"Token lookup failed: {e}")
        return None

def get_ltp(token_info):
    try:
        response = obj.ltpData(
            exchange=token_info['exch_seg'],
            tradingsymbol=token_info['symbol'],
            symboltoken=token_info['token']
        )
        return float(response['data']['ltp'])
    except Exception as e:
        print(f"LTP error: {e}")
        return None

def get_historical_data(token_info, interval, from_date, to_date):
    try:
        params = {
            "exchange": token_info['exch_seg'],
            "symboltoken": token_info['token'],
            "interval": interval,
            "fromdate": from_date.strftime('%Y-%m-%d %H:%M'),
            "todate": to_date.strftime('%Y-%m-%d %H:%M')
        }
        candles = obj.getCandleData(params)
        if candles['data'] is None:
            return None

        df = pd.DataFrame(candles['data'], columns=["datetime", "open", "high", "low", "close", "volume"])
        df["datetime"] = pd.to_datetime(df["datetime"])
        return df
    except Exception as e:
        print(f"Historical data error: {e}")
        return None
