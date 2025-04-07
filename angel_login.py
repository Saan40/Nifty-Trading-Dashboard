import os
import pyotp
import pandas as pd
from SmartApi.smartConnect import SmartConnect
from dotenv import load_dotenv
from datetime import datetime, timedelta

# Load .env environment variables
load_dotenv()

# Load credentials from environment
API_KEY = os.getenv("API_KEY")
CLIENT_CODE = os.getenv("CLIENT_CODE")
PASSWORD = os.getenv("PASSWORD")
TOTP_SECRET = os.getenv("TOTP_SECRET")  # This must be the 26-character base32 secret

if not all([API_KEY, CLIENT_CODE, PASSWORD, TOTP_SECRET]):
    raise ValueError("Missing one or more environment variables. Check your .env or Render settings.")

# Generate TOTP from secret
totp = pyotp.TOTP(TOTP_SECRET).now()

# Login to Angel One SmartAPI
obj = SmartConnect(api_key=API_KEY)
data = obj.generateSession(client_code=CLIENT_CODE, password=PASSWORD, totp=totp)

# Get instrument list
instruments_df = pd.read_csv("instruments.csv")

def get_instrument_token(df, symbol):
    match = df[df['symbol'].str.contains(symbol, case=False, na=False)]
    if not match.empty:
        return int(match.iloc[0]['token'])
    raise ValueError(f"Token not found for symbol: {symbol}")

def get_historical_data(instrument_token, interval="5minute", days=5):
    end_time = datetime.now()
    start_time = end_time - timedelta(days=days)

    params = {
        "exchange": "NSE",
        "symboltoken": str(instrument_token),
        "interval": interval,
        "fromdate": start_time.strftime('%Y-%m-%d %H:%M'),
        "todate": end_time.strftime('%Y-%m-%d %H:%M')
    }

    response = obj.getCandleData(params)
    data = response.get("data", [])

    df = pd.DataFrame(data, columns=["timestamp", "open", "high", "low", "close", "volume"])
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values("timestamp")
    return df

def get_ltp(instrument_token):
    ltp_data = obj.ltpData("NSE", "NIFTY", str(instrument_token))
    return ltp_data.get("data", {}).get("ltp", 0.0)
