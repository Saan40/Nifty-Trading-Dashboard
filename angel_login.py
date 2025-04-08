import os
import pyotp
import pandas as pd
from SmartApi.smartConnect import SmartConnect
from datetime import datetime, timedelta

# Load environment variables
api_key = os.getenv("ANGEL_API_KEY")
client_code = os.getenv("ANGEL_CLIENT_CODE")
password = os.getenv("ANGEL_PASSWORD")
totp_secret = os.getenv("ANGEL_TOTP_SECRET")  # 26-character secret

# Validate all required env vars are set
if not all([api_key, client_code, password, totp_secret]):
    raise Exception("Missing one or more required environment variables: ANGEL_API_KEY, ANGEL_CLIENT_CODE, ANGEL_PASSWORD, ANGEL_TOTP_SECRET")

# Generate TOTP from 26-digit secret
totp = pyotp.TOTP(totp_secret).now()

# Create API object and login
obj = SmartConnect(api_key=api_key)
session = obj.generateSession(client_code, password, totp)

if not session or 'status' not in session or session['status'] != True:
    raise Exception(f"Angel One login failed! Response: {session}")

# Save tokens
auth_token = session['data']['jwtToken']
refresh_token = session['data']['refreshToken']
feed_token = obj.getfeedToken()

# Load instruments CSV (must be in same directory or give correct path)
instruments_df = pd.read_csv("instruments.csv")

# Utility: Get token by symbol and exchange
def get_instrument_token(symbol, exchange):
    try:
        row = instruments_df[
            (instruments_df["name"] == symbol) & (instruments_df["exchange"] == exchange)
        ].iloc[0]
        return str(row["token"])
    except Exception as e:
        print(f"Error getting token for {symbol}: {e}")
        return None

# Utility: Get historical candle data
def get_historical_data(symbol, exchange, interval="FIVE_MINUTE", days=5):
    token = get_instrument_token(symbol, exchange)
    if not token:
        return []

    to_date = datetime.now()
    from_date = to_date - timedelta(days=days)

    params = {
        "exchange": exchange,
        "symboltoken": token,
        "interval": interval,
        "fromdate": from_date.strftime('%Y-%m-%d %H:%M'),
        "todate": to_date.strftime('%Y-%m-%d %H:%M')
    }

    try:
        data = obj.getCandleData(params)
        return data['data']
    except Exception as e:
        print(f"Error fetching historical data: {e}")
        return []

# Utility: Get LTP
def get_ltp(symbol, exchange):
    token = get_instrument_token(symbol, exchange)
    if not token:
        return None

    params = {
        "exchange": exchange,
        "tradingsymbol": symbol,
        "symboltoken": token
    }

    try:
        ltp_data = obj.ltpData(params)
        return float(ltp_data['data']['ltp'])
    except Exception as e:
        print(f"Error fetching LTP: {e}")
        return None
