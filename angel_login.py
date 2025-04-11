# --- angel_login.py ---
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

# Validate environment
if not all([api_key, client_code, password, totp_secret]):
    raise Exception("Missing one or more required environment variables.")

# Generate TOTP
totp = pyotp.TOTP(totp_secret).now()
smart_api = SmartConnect(api_key=api_key)
session = smart_api.generateSession(client_code, password, totp)

if 'status' not in session or not session['status']:
    raise Exception(f"Login failed: {session}")

auth_token = session['data']['jwtToken']
feed_token = smart_api.getfeedToken()

instruments_df = pd.read_csv("instruments.csv")

# Get nearest expiry token for NIFTY/BANKNIFTY

def get_instrument_token(symbol):
    today = datetime.today()
    df = instruments_df[
        (instruments_df['name'] == symbol)
        & (instruments_df['exch_seg'] == 'NFO')
        & (instruments_df['instrumenttype'] == 'OPTIDX')
    ].copy()

    df['expiry'] = pd.to_datetime(df['expiry'], errors='coerce')
    df = df[df['expiry'] >= today]

    if df.empty:
        raise ValueError("No valid expiry found for given symbol")

    nearest = df.sort_values('expiry').iloc[0]
    return {
        'symbol': nearest['symbol'],
        'token': nearest['token'],
        'expiry': nearest['expiry'],
        'strike': nearest['strike'] / 100,
        'exch_seg': nearest['exch_seg']
    }

# Get ATM Option Token for CALL/PUT
def get_option_token(symbol, strike, option_type, expiry):
    opt_symbol = f"{symbol}{expiry.strftime('%d%b%y').upper()}{int(strike)}{option_type}"
    row = instruments_df[(instruments_df['symbol'] == opt_symbol)]
    if not row.empty:
        return row.iloc[0]['token']
    return None

# Get historical OHLC data
def get_historical_data(token, interval, from_date, to_date):
    params = {
        "exchange": "NFO",
        "symboltoken": str(token),
        "interval": interval,
        "fromdate": from_date.strftime('%Y-%m-%d %H:%M'),
        "todate": to_date.strftime('%Y-%m-%d %H:%M')
    }
    response = smart_api.getCandleData(params)
    candles = response.get("data")
    if not candles:
        raise Exception("No candle data received.")

    df = pd.DataFrame(candles, columns=["datetime", "open", "high", "low", "close", "volume"])
    df["datetime"] = pd.to_datetime(df["datetime"])
    return df

# Get LTP
def get_ltp(symbol, token):
    try:
        data = smart_api.ltpData("NFO", symbol, str(token))
        return float(data['data']['ltp'])
    except:
        return None
