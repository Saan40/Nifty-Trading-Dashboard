from SmartApi import SmartConnect
from dotenv import load_dotenv
import pandas as pd
import pyotp
import os
import requests

load_dotenv()

# Environment Variables
API_KEY = os.getenv("API_KEY")
CLIENT_CODE = os.getenv("CLIENT_CODE")
PASSWORD = os.getenv("PASSWORD")
TOTP_SECRET = os.getenv("TOTP_SECRET")

# Validate
if not all([API_KEY, CLIENT_CODE, PASSWORD, TOTP_SECRET]):
    raise ValueError("Missing one or more environment variables.")

# Create SmartConnect object
obj = SmartConnect(api_key=API_KEY)

# Generate TOTP
totp = pyotp.TOTP(TOTP_SECRET).now()

# Login
try:
    data = obj.generateSession(CLIENT_CODE, PASSWORD, totp)
except Exception as e:
    raise Exception(f"Login failed: {e}")

# Get tokens
try:
    auth_token = data["data"]["jwtToken"]
    refresh_token = data["data"]["refreshToken"]
    feed_token = obj.getfeedToken()
except Exception as e:
    raise Exception("Token extraction failed: " + str(e))

# Download instruments.csv if not exists
if not os.path.exists("instruments.csv"):
    print("Downloading instruments.csv...")
    url = "https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json"
    response = requests.get(url)
    instruments = response.json()
    df = pd.DataFrame(instruments)
    df.to_csv("instruments.csv", index=False)
    print("Saved instruments.csv")

# Load instruments
instruments_df = pd.read_csv("instruments.csv")

# Token fetch
def get_instrument_token(df, symbol):
    symbol_row = df[df["symbol"] == symbol]
    if not symbol_row.empty:
        return int(symbol_row.iloc[0]["token"])
    raise Exception(f"Token not found for symbol: {symbol}")

# Historical data
def get_historical_data(token, interval="5minute", duration="1", exchange="NSE"):
    params = {
        "exchange": exchange,
        "symboltoken": str(token),
        "interval": interval,
        "fromdate": pd.Timestamp.now() - pd.Timedelta(days=int(duration)),
        "todate": pd.Timestamp.now()
    }
    response = obj.getCandleData(params)
    candles = response["data"]
    df = pd.DataFrame(candles, columns=["timestamp", "open", "high", "low", "close", "volume"])
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df

# LTP
def get_ltp(token, exchange="NSE", symbol="NIFTY"):
    params = {
        "exchange": exchange,
        "symboltoken": str(token),
        "symbol": symbol
    }
    response = obj.ltpData(params)
    return response["data"]["ltp"]
