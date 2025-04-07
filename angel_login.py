import os
import pyotp
import json
import pandas as pd
from datetime import datetime, timedelta
from SmartApi.smartConnect import SmartConnect
from dotenv import load_dotenv

load_dotenv()

# Load credentials from environment variables
API_KEY = os.getenv("API_KEY")
CLIENT_CODE = os.getenv("CLIENT_CODE")
PASSWORD = os.getenv("PASSWORD")
TOTP_SECRET = os.getenv("TOTP_SECRET")

if not all([API_KEY, CLIENT_CODE, PASSWORD, TOTP_SECRET]):
    raise ValueError("Missing one or more environment variables.")

# Login
obj = SmartConnect(api_key=API_KEY)
totp = pyotp.TOTP(TOTP_SECRET).now()
data = obj.generateSession(CLIENT_CODE, PASSWORD, totp)

# Load instruments
if not os.path.exists("instruments.csv"):
    raise FileNotFoundError("instruments.csv not found. Please upload it.")
instruments_df = pd.read_csv("instruments.csv")

def get_instrument_token(instruments_df, symbol):
    row = instruments_df[(instruments_df["symbol"].str.contains(symbol)) & 
                         (instruments_df["exchange"] == "NFO") &
                         (instruments_df["instrumenttype"] == "FUT")]
    if not row.empty:
        return int(row.iloc[0]["token"])
    else:
        raise ValueError(f"Instrument token not found for {symbol}")

def get_ltp(token):
    return obj.ltpData("NFO", token)["data"]["ltp"]

def get_historical_data(token, interval="5minute", days=5):
    end_time = datetime.now()
    start_time = end_time - timedelta(days=days)
    params = {
        "exchange": "NFO",
        "symboltoken": str(token),
        "interval": interval,
        "fromdate": start_time.strftime("%Y-%m-%d %H:%M"),
        "todate": end_time.strftime("%Y-%m-%d %H:%M")
    }
    # Fix: convert datetime to string before passing
    return pd.DataFrame(obj.getCandleData(params)["data"], columns=["timestamp", "open", "high", "low", "close", "volume"])
