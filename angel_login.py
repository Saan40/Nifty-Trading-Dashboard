from SmartApi import SmartConnect
from dotenv import load_dotenv
import os
import pyotp

load_dotenv()

# Load environment variables
API_KEY = os.getenv("API_KEY")
CLIENT_CODE = os.getenv("CLIENT_CODE")
PASSWORD = os.getenv("PASSWORD")
TOTP_SECRET = os.getenv("TOTP")

# Debug print
print("DEBUG - API_KEY:", API_KEY)
print("DEBUG - CLIENT_CODE:", CLIENT_CODE)
print("DEBUG - PASSWORD:", PASSWORD)
print("DEBUG - TOTP_SECRET:", TOTP_SECRET)

# Validate env vars
if not all([API_KEY, CLIENT_CODE, PASSWORD, TOTP_SECRET]):
    raise ValueError("Missing one or more environment variables.")

# Generate 6-digit TOTP
totp = pyotp.TOTP(TOTP_SECRET)
TOTP = totp.now()
print("DEBUG - Generated 6-digit TOTP:", TOTP)

# Create connection object
obj = SmartConnect(api_key=API_KEY)

# Try login
try:
    data = obj.generateSession(CLIENT_CODE, PASSWORD, TOTP)
except Exception as e:
    raise Exception(f"Login failed: {e}")

# Validate response
if not data or not isinstance(data, dict):
    raise Exception(f"Login returned invalid response: {data}")

# Get tokens
try:
    auth_token = data['data']['jwtToken']
    refresh_token = data['data']['refreshToken']
    feed_token = obj.getfeedToken()
except (KeyError, TypeError):
    raise Exception(f"Token fields missing in login response: {data}")
