import os
from SmartApi import SmartConnect
import pyotp
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Read env vars
API_KEY = os.getenv("API_KEY")
CLIENT_CODE = os.getenv("CLIENT_CODE")
PASSWORD = os.getenv("PASSWORD")
TOTP_SECRET = os.getenv("TOTP")

# Debugging (Optional: Remove in production)
print("API_KEY:", bool(API_KEY))
print("CLIENT_CODE:", bool(CLIENT_CODE))
print("PASSWORD:", bool(PASSWORD))
print("TOTP_SECRET:", bool(TOTP_SECRET))

# Check if all required env vars are present
if not all([API_KEY, CLIENT_CODE, PASSWORD, TOTP_SECRET]):
    raise ValueError("Missing one or more environment variables. Please check API_KEY, CLIENT_CODE, PASSWORD, or TOTP.")

# Generate 6-digit TOTP from 26-digit secret
totp = pyotp.TOTP(TOTP_SECRET).now()

# Create SmartAPI connection
obj = SmartConnect(api_key=API_KEY)

# Try to login
try:
    data = obj.generateSession(CLIENT_CODE, PASSWORD, totp)
except Exception as e:
    raise Exception(f"Login failed: {e}")

# Validate login response
if not data or not isinstance(data, dict):
    raise Exception(f"Login returned invalid response: {data}")

# Extract tokens
try:
    auth_token = data['data']['jwtToken']
    refresh_token = data['data']['refreshToken']
    feed_token = obj.getfeedToken()
except (KeyError, TypeError):
    raise Exception(f"Token fields missing in login response: {data}")

# Utility functions
def get_instrument_token(instruments_df, symbol):
    row = instruments_df[instruments_df['symbol'] == symbol]
    if not row.empty:
        return int(row.iloc[0]['token'])
    return None

def get_ltp(symbol, exchange="NSE", symbol_token=None):
    params = {
        "exchange": exchange,
        "tradingsymbol": symbol,
        "symboltoken": symbol_token
    }
    try:
        return obj.ltpData(params)
    except Exception as e:
        print(f"LTP fetch failed: {e}")
        return None

def get_historical_data(symbol_token, interval, from_date, to_date):
    params = {
        "exchange": "NSE",
        "symboltoken": symbol_token,
        "interval": interval,
        "fromdate": from_date,
        "todate": to_date
    }
    try:
        return obj.getCandleData(params)
    except Exception as e:
        print(f"Historical data fetch failed: {e}")
        return None
