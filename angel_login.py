import os
import pyotp
import pandas as pd
from datetime import datetime, timedelta
from SmartApi.smartConnect import SmartConnect

# Load environment variables
api_key = os.getenv("ANGEL_API_KEY")
client_code = os.getenv("ANGEL_CLIENT_CODE")
password = os.getenv("ANGEL_PASSWORD")
totp_secret = os.getenv("ANGEL_TOTP_SECRET")

if not all([api_key, client_code, password, totp_secret]):
    raise Exception("Missing one or more required environment variables")

# Generate TOTP and login
totp = pyotp.TOTP(totp_secret).now()
obj = SmartConnect(api_key=api_key)
session = obj.generateSession(client_code, password, totp)

if not session or 'status' not in session or session['status'] != True:
    raise Exception(f"Angel login failed: {session}")

auth_token = session['data']['jwtToken']
refresh_token = session['data']['refreshToken']
feed_token = obj.getfeedToken()

# Load instruments.csv
instruments_df = pd.read_csv("instruments.csv")

# Auto-token selection for current week expiry
def get_weekly_token(symbol):
    df = instruments_df.copy()
    df = df[df['exch_seg'] == 'NFO']
    df = df[df['name'] == symbol]
    df['expiry'] = pd.to_datetime(df['expiry'], errors='coerce')
    today = pd.Timestamp.today()
    df = df[df['expiry'] >= today]

    if df.empty:
        raise Exception(f"No future contracts found for {symbol}")

    nearest = df.sort_values('expiry').iloc[0]
    return str(nearest['token'])

# Historical data fetcher
def get_historical_data(token, interval, from_date, to_date, exchange="NFO"):
    params = {
        "exchange": exchange,
        "symboltoken": str(token),
        "interval": interval,
        "fromdate": from_date.strftime('%Y-%m-%d %H:%M'),
        "todate": to_date.strftime('%Y-%m-%d %H:%M')
    }
    response = obj.getCandleData(params)
    candles = response.get('data')
    if not candles:
        raise Exception("No candle data received.")
    df = pd.DataFrame(candles, columns=["datetime", "open", "high", "low", "close", "volume"])
    df["datetime"] = pd.to_datetime(df["datetime"])
    return df

# LTP fetcher
def get_ltp(symbol, exchange="NFO"):
    token = get_weekly_token(symbol)
    try:
        response = obj.ltpData(
            exchange=exchange,
            tradingsymbol=symbol,
            symboltoken=token
        )
        return float(response['data']['ltp'])
    except Exception as e:
        print(f"LTP error for {symbol}: {e}")
        return None
