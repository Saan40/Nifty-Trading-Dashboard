import os
import pyotp
import pandas as pd
from SmartApi import SmartConnect
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_KEY")
CLIENT_CODE = os.getenv("CLIENT_CODE")
PASSWORD = os.getenv("PASSWORD")
TOTP_SECRET = os.getenv("TOTP_SECRET")

if not all([API_KEY, CLIENT_CODE, PASSWORD, TOTP_SECRET]):
    raise ValueError("Missing one or more environment variables (API_KEY, CLIENT_CODE, PASSWORD, TOTP_SECRET).")

# Generate 6-digit TOTP from 26-digit secret
totp = pyotp.TOTP(TOTP_SECRET).now()

obj = SmartConnect(api_key=API_KEY)

# Login session
data = obj.generateSession(CLIENT_CODE, PASSWORD, totp)

if not data or 'data' not in data or 'jwtToken' not in data['data']:
    raise Exception(f"Token fields missing in login response: {data}")

auth_token = data['data']['jwtToken']
refresh_token = data['data']['refreshToken']
feed_token = obj.getfeedToken()

# Load instruments file
instruments_df = pd.read_csv("instruments.csv")

# Get token for symbol
def get_instrument_token(df, symbol):
    row = df[df['tradingsymbol'].str.upper() == symbol.upper()]
    if not row.empty:
        return int(row.iloc[0]['token'])
    raise ValueError(f"Token not found for symbol: {symbol}")

# Get LTP
def get_ltp(token):
    try:
        ltp_data = obj.ltpData("NSE", "NIFTY", token)
        return ltp_data['data']['ltp']
    except Exception as e:
        return f"Error: {e}"

# Get historical data
def get_historical_data(token, interval="5minute", days=2):
    from datetime import datetime, timedelta
    end = datetime.now()
    start = end - timedelta(days=days)
    try:
        historical_params = {
            "exchange": "NSE",
            "symboltoken": str(token),
            "interval": interval,
            "fromdate": start.strftime('%Y-%m-%d %H:%M'),
            "todate": end.strftime('%Y-%m-%d %H:%M')
        }
        data = obj.getCandleData(historical_params)
        df = pd.DataFrame(data['data'], columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        return df
    except Exception as e:
        return pd.DataFrame()
