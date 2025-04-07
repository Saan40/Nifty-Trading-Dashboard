from SmartApi import SmartConnect
from dotenv import load_dotenv
import os

load_dotenv()

API_KEY = os.getenv("API_KEY")
CLIENT_CODE = os.getenv("CLIENT_CODE")
PASSWORD = os.getenv("PASSWORD")
TOTP = os.getenv("TOTP")

# Validate env vars
if not all([API_KEY, CLIENT_CODE, PASSWORD, TOTP]):
    raise ValueError("Missing one or more environment variables.")

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

# Check token
try:
    auth_token = data['data']['jwtToken']
    refresh_token = data['data']['refreshToken']
    feed_token = obj.getfeedToken()
except (KeyError, TypeError):
    raise Exception(f"Token fields missing in login response: {data}")
