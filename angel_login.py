from SmartApi import SmartConnect
from dotenv import load_dotenv
import os

load_dotenv()

API_KEY = os.getenv("API_KEY")
CLIENT_CODE = os.getenv("CLIENT_CODE")
PASSWORD = os.getenv("PASSWORD")
TOTP = os.getenv("TOTP")

if not all([API_KEY, CLIENT_CODE, PASSWORD, TOTP]):
    raise Exception("One or more environment variables are missing.")

obj = SmartConnect(api_key=API_KEY)

try:
    data = obj.generateSession(CLIENT_CODE, PASSWORD, TOTP)
except Exception as e:
    raise Exception(f"Login failed: {e}")

# Validate response structure
if not isinstance(data, dict) or 'data' not in data or 'jwtToken' not in data['data']:
    raise Exception(f"Invalid login response: {data}")

auth_token = data['data']['jwtToken']
refresh_token = data['data']['refreshToken']
feed_token = obj.getfeedToken()
