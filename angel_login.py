# --- angel_login.py ---
import os
import pyotp
import pandas as pd
from SmartApi.smartConnect import SmartConnect
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

# Load environment variables
api_key = os.getenv("ANGEL_API_KEY")
client_code = os.getenv("ANGEL_CLIENT_CODE")
password = os.getenv("ANGEL_PASSWORD")
totp_secret = os.getenv("ANGEL_TOTP_SECRET")  # 26-char secret

# Validate env variables
if not all([api_key, client_code, password, totp_secret]):
    raise Exception("Missing one or more required environment variables: ANGEL_API_KEY, ANGEL_CLIENT_CODE, ANGEL_PASSWORD, ANGEL_TOTP_SECRET")

# Generate TOTP
totp = pyotp.TOTP(totp_secret).now()

# Login to Smart API
obj = SmartConnect(api_key=api_key)
session = obj.generateSession(client_code, password, totp)

if not session or 'status' not in session or session['status'] != True:
    raise Exception(f"Angel One login failed! Response: {session}")

auth_token = session['data']['jwtToken']
refresh_token = session['data']['refreshToken']
feed_token = obj.getfeedToken()

# Load instrument list
instruments_df = pd.read_csv("instruments.csv")

# --- Utility Functions ---
def get_instrument_token(symbol, exchange="NFO"):
    try:
        row = instruments_df[
            (instruments_df["name"] == symbol) & (instruments_df["exch_seg"] == exchange)
        ].iloc[0]
        return str(row["token"])
    except Exception as e:
        print(f"Token not found for {symbol} on {exchange}: {e}")
        return None

def get_historical_data(token, interval, from_date, to_date, exchange="NFO"):
    params = {
        "exchange": exchange,
        "symboltoken": str(token),
        "interval": interval,
        "fromdate": from_date.strftime('%Y-%m-%d %H:%M'),
        "todate": to_date.strftime('%Y-%m-%d %H:%M')
    }
    try:
        response = obj.getCandleData(params)
        candles = response['data']
        df = pd.DataFrame(candles, columns=['datetime', 'open', 'high', 'low', 'close', 'volume'])
        df['datetime'] = pd.to_datetime(df['datetime'])
        df[['open', 'high', 'low', 'close', 'volume']] = df[['open', 'high', 'low', 'close', 'volume']].astype(float)
        return df
    except Exception as e:
        print(f"Error fetching historical data: {e}")
        return pd.DataFrame()

def get_ltp(symbol, exchange="NFO"):
    token = get_instrument_token(symbol, exchange)
    if not token:
        return None
    try:
        response = obj.ltpData(exchange=exchange, tradingsymbol=symbol, symboltoken=token)
        return float(response['data']['ltp'])
    except Exception as e:
        print(f"Error getting LTP for {symbol}: {e}")
        return None
