# angel_login.py (FINAL)
import os
import pyotp
import pandas as pd
from SmartApi.smartConnect import SmartConnect
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
api_key = os.getenv("ANGEL_API_KEY")
client_code = os.getenv("ANGEL_CLIENT_CODE")
password = os.getenv("ANGEL_PASSWORD")
totp_secret = os.getenv("ANGEL_TOTP_SECRET")

# Validate environment variables
if not all([api_key, client_code, password, totp_secret]):
    raise Exception("Missing one or more required environment variables: ANGEL_API_KEY, ANGEL_CLIENT_CODE, ANGEL_PASSWORD, ANGEL_TOTP_SECRET")

# Generate TOTP
totp = pyotp.TOTP(totp_secret).now()

# Login
obj = SmartConnect(api_key=api_key)
session = obj.generateSession(client_code, password, totp)
if not session or 'status' not in session or session['status'] != True:
    raise Exception(f"Angel One login failed! Response: {session}")

# Tokens
auth_token = session['data']['jwtToken']
refresh_token = session['data']['refreshToken']
feed_token = obj.getfeedToken()

# Load instruments file
instruments_df = pd.read_csv("instruments.csv")

# Get instrument token
def get_instrument_token(symbol, df, expiry="17-Apr-25", instrument_type="OPTIDX"):
    try:
        row = df[
            (df['name'] == symbol) &
            (df['expiry'] == expiry) &
            (df['instrumenttype'] == instrument_type)
        ].iloc[0]
        return str(row['token'])
    except Exception as e:
        print(f"Token fetch error for {symbol}: {e}")
        return None

# Get historical data
from datetime import datetime

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
        return pd.DataFrame(response['data'], columns=['datetime', 'open', 'high', 'low', 'close', 'volume'])
    except Exception as e:
        print(f"Historical data error: {e}")
        return pd.DataFrame()

# Get LTP
def get_ltp(symbol, df, exchange="NFO"):
    token = get_instrument_token(symbol, df)
    if not token:
        return None
    try:
        response = obj.ltpData(exchange=exchange, tradingsymbol=symbol, symboltoken=token)
        return float(response['data']['ltp'])
    except Exception as e:
        print(f"LTP fetch error: {e}")
        return None
