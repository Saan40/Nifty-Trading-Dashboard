from SmartApi import SmartConnect
from dotenv import load_dotenv
import os

# Load .env if running locally (not used on Render, but safe to keep)
load_dotenv()

# Load environment variables
API_KEY = os.getenv("API_KEY")
CLIENT_CODE = os.getenv("CLIENT_CODE")
PASSWORD = os.getenv("PASSWORD")
TOTP = os.getenv("TOTP")

# Debug print to verify env vars (will be visible in Render logs)
print("DEBUG - API_KEY:", API_KEY)
print("DEBUG - CLIENT_CODE:", CLIENT_CODE)
print("DEBUG - PASSWORD:", PASSWORD)
print("DEBUG - TOTP:", TOTP)

# Validate env vars
if not all([API_KEY, CLIENT_CODE, PASSWORD, TOTP]):
    raise ValueError("Missing one or more environment variables.")

# Create connection object
obj = SmartConnect(api_key=API_KEY)

# Try login
try:
    data = obj.generateSession(CLIENT_CODE, PASSWORD, TOTP)
    print("DEBUG - Login response:", data)
except Exception as e:
    raise Exception(f"Login failed: {e}")

# Validate login response
if not data or not isinstance(data, dict) or 'data' not in data:
    raise Exception(f"Login returned invalid response: {data}")

# Check and extract tokens
try:
    auth_token = data['data']['jwtToken']
    refresh_token = data['data']['refreshToken']
    feed_token = obj.getfeedToken()
except (KeyError, TypeError):
    raise Exception(f"Token fields missing in login response: {data}")

# Define helper functions (used by dashboard.py)
def get_instrument_token(instrument_list, symbol):
    for instrument in instrument_list:
        if instrument['symbol'] == symbol:
            return instrument['token']
    return None

def get_historical_data(token, interval, from_date, to_date):
    try:
        params = {
            "exchange": "NSE",
            "symboltoken": token,
            "interval": interval,
            "fromdate": from_date,
            "todate": to_date
        }
        data = obj.getCandleData(params)
        return data['data']
    except Exception as e:
        print("Error fetching historical data:", e)
        return []

def get_ltp(exchange, symboltoken, symbolname):
    try:
        params = {
            "exchange": exchange,
            "symboltoken": symboltoken,
            "tradingsymbol": symbolname
        }
        data = obj.ltpData(params)
        return data['data']['ltp']
    except Exception as e:
        print("Error fetching LTP:", e)
        return None
