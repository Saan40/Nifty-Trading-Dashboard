import os
from dotenv import load_dotenv
from smartapi import SmartConnect
import pyotp

# Load environment variables from .env file
load_dotenv()

def angel_login():
    api_key = os.getenv("ANGEL_API_KEY")
    client_id = os.getenv("ANGEL_CLIENT_ID")
    password = os.getenv("ANGEL_PASSWORD")
    totp_secret = os.getenv("ANGEL_TOTP")

    try:
        obj = SmartConnect(api_key=api_key)

        # Generate TOTP
        totp = pyotp.TOTP(totp_secret).now()

        # Generate session and get token
        session_data = obj.generateSession(client_id, password, totp)
        return obj, session_data

    except Exception as e:
        print("Login failed:", e)
        return None, None
