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
totp_secret = os.getenv("ANGEL_TOTP_SECRET")

if not all([api_key, client_code, password, totp_secret]):
    raise Exception("Missing one or more required environment variables")

# Generate TOTP
totp = pyotp.TOTP(totp_secret).now()

# Login
obj = SmartConnect(api_key=api_key)
session = obj.generateSession(client_code, password, totp)

if not session or 'status' not in session or session['status'] != True:
    raise Exception(f"Angel One login failed: {session}")

auth_token = session['data']['jwtToken']
refresh_token = session['data']['refreshToken']
feed_token = obj.getfeedToken()

# Load instrument list
instruments_df = pd.read_csv("instruments.csv")

# Token fetcher (auto-weekly expiry)
def get_instrument_token(symbol):
    today = datetime.now().date()
    df = instruments_df.copy()

    df['expiry'] = pd.to_datetime(df['expiry'], errors='coerce').dt.date
    df = df[(df['symbol'].str.startswith(symbol)) & (df['exch_seg'] == 'NFO')]

    upcoming = df[df['expiry'] >= today]
    if upcoming.empty:
        raise Exception(f"No weekly expiry found for {symbol}")

    nearest = upcoming.sort_values('expiry').iloc[0]
    return {
        'token': str(nearest['token']),
        'symbol': nearest['symbol'],
        'exch_seg': nearest['exch_seg']
    }

# LTP Fetcher
def get_ltp(token_info):
    try:
        ltp_data = obj.ltpData(
            exchange=token_info['exch_seg'],
            tradingsymbol=token_info['symbol'],
            symboltoken=token_info['token']
        )
        return float(ltp_data['data']['ltp'])
    except Exception as e:
        print("LTP fetch error:", e)
        return None

# Historical Data Fetcher
def get_historical_data(token_info, interval, from_date, to_date):
    try:
        params = {
            "exchange": token_info['exch_seg'],
            "symboltoken": token_info['token'],
            "interval": interval,
            "fromdate": from_date.strftime('%Y-%m-%d %H:%M'),
            "todate": to_date.strftime('%Y-%m-%d %H:%M')
        }
        data = obj.getCandleData(params)
        candles = data.get("data", [])
        if not candles:
            raise Exception("No candle data received.")
        df = pd.DataFrame(candles, columns=["datetime", "open", "high", "low", "close", "volume"])
        df["datetime"] = pd.to_datetime(df["datetime"])
        return df
    except Exception as e:
        print("Historical data error:", e)
        return None
