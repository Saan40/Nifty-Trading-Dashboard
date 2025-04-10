import os
import pyotp
import pandas as pd
from SmartApi.smartConnect import SmartConnect
from datetime import datetime

# Print environment variable values for debugging
print("DEBUG: ANGEL_API_KEY =", os.getenv("ANGEL_API_KEY"))
print("DEBUG: ANGEL_CLIENT_CODE =", os.getenv("ANGEL_CLIENT_CODE"))
print("DEBUG: ANGEL_PASSWORD =", os.getenv("ANGEL_PASSWORD"))
print("DEBUG: ANGEL_TOTP_SECRET =", os.getenv("ANGEL_TOTP_SECRET"))

# Load environment variables
api_key = os.getenv("ANGEL_API_KEY")
client_code = os.getenv("ANGEL_CLIENT_CODE")
password = os.getenv("ANGEL_PASSWORD")
totp_secret = os.getenv("ANGEL_TOTP_SECRET")  # must be 26-character string

# Validate env vars
if not all([api_key, client_code, password, totp_secret]):
    raise Exception("Missing one or more environment variables. Check ANGEL_API_KEY, ANGEL_CLIENT_CODE, ANGEL_PASSWORD, ANGEL_TOTP_SECRET")

# Generate TOTP
try:
    totp = pyotp.TOTP(totp_secret).now()
    print("DEBUG: Generated TOTP:", totp)
except Exception as e:
    raise Exception(f"Error generating TOTP from secret: {e}")

# Angel One SmartConnect login
obj = SmartConnect(api_key=api_key)
session = obj.generateSession(client_code, password, totp)

if not session or 'status' not in session or session['status'] != True:
    raise Exception(f"Login failed! Full response: {session}")

auth_token = session['data']['jwtToken']
refresh_token = session['data']['refreshToken']
feed_token = obj.getfeedToken()

# Load instrument data
try:
    instruments_df = pd.read_csv("instruments.csv")
except Exception as e:
    raise Exception(f"Error loading instruments.csv: {e}")

# Utility to get latest weekly expiry token
def get_instrument_token(symbol):
    today = datetime.today().date()

    df = instruments_df[
        (instruments_df['trading_symbol'].str.startswith(symbol)) &
        (instruments_df['exch_seg'] == 'NFO')
    ].copy()

    df['expiry'] = pd.to_datetime(df['trading_symbol'].str.extract(r'(\d{2}[A-Z]{3}\d{2})')[0], format='%d%b%y', errors='coerce')
    df = df.dropna(subset=['expiry'])
    df = df[df['expiry'].dt.date >= today]

    if df.empty:
        print("DEBUG: No matching expiry found for symbol:", symbol)
        return None

    nearest = df.sort_values('expiry').iloc[0]
    return str(nearest['token'])

# Utility to get LTP
def get_ltp(symbol):
    token = get_instrument_token(symbol)
    if not token:
        return None
    try:
        response = obj.ltpData(exchange='NFO', tradingsymbol=symbol, symboltoken=token)
        return float(response['data']['ltp'])
    except Exception as e:
        print(f"Error fetching LTP for {symbol}: {e}")
        return None

# Utility to get historical data
def get_historical_data(token, interval, from_date, to_date):
    try:
        params = {
            "exchange": "NFO",
            "symboltoken": token,
            "interval": interval,
            "fromdate": from_date.strftime('%Y-%m-%d %H:%M'),
            "todate": to_date.strftime('%Y-%m-%d %H:%M')
        }
        response = obj.getCandleData(params)
        candles = response.get("data")
        if not candles:
            raise Exception("No candle data received.")
        df = pd.DataFrame(candles, columns=["datetime", "open", "high", "low", "close", "volume"])
        df["datetime"] = pd.to_datetime(df["datetime"])
        return df
    except Exception as e:
        raise Exception(f"Error fetching historical data: {e}")
