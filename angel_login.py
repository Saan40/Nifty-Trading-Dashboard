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

# Validate env variables
if not all([api_key, client_code, password, totp_secret]):
    raise Exception("Missing one or more required environment variables: ANGEL_API_KEY, ANGEL_CLIENT_CODE, ANGEL_PASSWORD, ANGEL_TOTP_SECRET")

# Generate TOTP
totp = pyotp.TOTP(totp_secret).now()

# Login
obj = SmartConnect(api_key=api_key)
session = obj.generateSession(client_code, password, totp)

if not session or 'status' not in session or session['status'] != True:
    raise Exception(f"Login failed: {session}")

auth_token = session['data']['jwtToken']
refresh_token = session['data']['refreshToken']
feed_token = obj.getfeedToken()

# Load instrument data
instruments_df = pd.read_csv("instruments.csv")

# Final token getter using weekly expiry logic
def get_instrument_token(symbol):
    df = instruments_df.copy()
    df = df[df['exch_seg'] == 'NFO']
    df = df[df['name'] == symbol]
    df['expiry_date'] = df['trading_symbol'].str.extract(r'(\d{2}[A-Z]{3}\d{2})')[0]
    df['expiry_date'] = pd.to_datetime(df['expiry_date'], format='%d%b%y', errors='coerce')
    df = df.dropna(subset=['expiry_date'])
    today = pd.Timestamp(datetime.now().date())
    df = df[df['expiry_date'] >= today]
    if df.empty:
        raise Exception(f"No upcoming expiry found for {symbol}")
    nearest = df.sort_values('expiry_date').iloc[0]
    return str(nearest['token'])

# Fetch historical data
def get_historical_data(token, interval, from_date, to_date, exchange="NFO"):
    params = {
        "exchange": exchange,
        "symboltoken": token,
        "interval": interval,
        "fromdate": from_date.strftime('%Y-%m-%d %H:%M'),
        "todate": to_date.strftime('%Y-%m-%d %H:%M')
    }
    candles = obj.getCandleData(params)
    if not candles or 'data' not in candles:
        raise Exception("No candle data received.")
    df = pd.DataFrame(candles['data'], columns=['datetime', 'open', 'high', 'low', 'close', 'volume'])
    df['datetime'] = pd.to_datetime(df['datetime'])
    return df

# Get LTP
def get_ltp(symbol):
    token = get_instrument_token(symbol)
    try:
        response = obj.ltpData(exchange="NFO", tradingsymbol=symbol, symboltoken=token)
        return float(response['data']['ltp'])
    except Exception as e:
        print(f"LTP error: {e}")
        return None
