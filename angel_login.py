from SmartApi import SmartConnect
from dotenv import load_dotenv
import pyotp
import os

# Load .env if running locally
load_dotenv()

# Load environment variables
API_KEY = os.getenv("API_KEY")
CLIENT_CODE = os.getenv("CLIENT_CODE")
PASSWORD = os.getenv("PASSWORD")
TOTP_SECRET = os.getenv("TOTP")  # 26-character secret

# Debug print (optional: comment out in production)
print("DEBUG - API_KEY:", API_KEY)
print("DEBUG - CLIENT_CODE:", CLIENT_CODE)
print("DEBUG - PASSWORD:", PASSWORD)
print("DEBUG - TOTP_SECRET:", TOTP_SECRET)

# Validate env vars
if not all([API_KEY, CLIENT_CODE, PASSWORD, TOTP_SECRET]):
    raise ValueError("Missing one or more environment variables.")

# Generate 6-digit TOTP from 26-digit secret
totp = pyotp.TOTP(TOTP_SECRET).now()

# Create connection object
obj = SmartConnect(api_key=API_KEY)

# Try login
try:
    data = obj.generateSession(CLIENT_CODE, PASSWORD, totp)
except Exception as e:
    raise Exception(f"Login failed: {e}")

# Validate login response
if not isinstance(data, dict) or 'data' not in data or 'jwtToken' not in data['data']:
    raise Exception(f"Token fields missing in login response: {data}")

# Extract tokens
auth_token = data['data']['jwtToken']
refresh_token = data['data']['refreshToken']
feed_token = obj.getfeedToken()

# You can now use these tokens
print("Login successful!")

# Optional helper functions (you can modify as needed)
def get_ltp(symbol_token, exchange):
    return obj.ltpData(exchange=exchange, tradingsymbol=symbol_token, symboltoken=symbol_token)

def get_instrument_token(symbol):
    # Load your instruments.csv or use Angel One API lookup here
    pass

def get_historical_data():
    # Optional: historical data logic
    pass
