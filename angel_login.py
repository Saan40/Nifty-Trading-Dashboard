# angel_login.py
import os
import pyotp
import pandas as pd
from datetime import datetime
from SmartApi.smartConnect import SmartConnect

# Environment variables
api_key = os.getenv("ANGEL_API_KEY")
client_code = os.getenv("ANGEL_CLIENT_CODE")
password = os.getenv("ANGEL_PASSWORD")
totp_secret = os.getenv("ANGEL_TOTP_SECRET")

# Check all environment variables
if not all([api_key, client_code, password, totp_secret]):
    raise Exception("Missing one or more required environment variables.")

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

# ---- Weekly Token Fetcher ----
def get_weekly_token(symbol):
    today = datetime.now().date()
    instruments_df['expiry'] = pd.to_datetime(instruments_df['expiry'], errors='coerce').dt.date
    filtered = instruments_df[
        (instruments_df['name'] == symbol) &
        (instruments_df['exch_seg'] == 'NFO') &
        (instruments_df['expiry'] >= today)
    ]
    if filtered.empty:
        raise Exception(f"No weekly expiry token found for {symbol}")
    nearest = filtered.sort_values(by="expiry").iloc[0]
    return str(nearest["token"]), nearest["trading_symbol"]

# ---- Historical Data ----
def get_historical_data(token, interval, from_date, to_date, exchange="NFO"):
    params = {
        "exchange": exchange,
        "symboltoken": str(token),
        "interval": interval,
        "fromdate": from_date.strftime('%Y-%m-%d %H:%M'),
        "todate": to_date.strftime('%Y-%m-%d %H:%M')
    }
    return obj.getCandleData(params)["data"]

# ---- LTP ----
def get_ltp(token, exchange="NFO"):
    try:
        return float(obj.ltpData(exchange=exchange, symboltoken=str(token))["data"]["ltp"])
    except:
        return None
