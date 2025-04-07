angel_login.py

import os import pyotp import pandas as pd from SmartApi.smartConnect import SmartConnect from dotenv import load_dotenv

load_dotenv()

Load environment variables

API_KEY = os.getenv("API_KEY") CLIENT_CODE = os.getenv("CLIENT_CODE") PASSWORD = os.getenv("PASSWORD") TOTP_SECRET = os.getenv("TOTP_SECRET")

if not all([API_KEY, CLIENT_CODE, PASSWORD, TOTP_SECRET]): raise ValueError("Missing one or more environment variables.")

Generate TOTP

totp = pyotp.TOTP(TOTP_SECRET).now()

Login to Angel One

obj = SmartConnect(api_key=API_KEY) data = obj.generateSession(CLIENT_CODE, PASSWORD, totp) refreshToken = data["data"]["refreshToken"] feedToken = obj.getfeedToken()

Load instrument data

instruments_df = pd.read_csv("instruments.csv")

Utility Functions

def get_instrument_token(df, symbol): try: token = df[df["symbol"] == symbol]["token"].values[0] return token except IndexError: raise ValueError(f"Token for symbol '{symbol}' not found in instruments.csv")

def get_historical_data(token, interval="5minute", duration="1", exchange="NSE"): to_date = pd.Timestamp.now() from_date = to_date - pd.Timedelta(days=int(duration))

params = {
    "exchange": exchange,
    "symboltoken": str(token),
    "interval": interval,
    "fromdate": from_date.strftime("%Y-%m-%d %H:%M"),
    "todate": to_date.strftime("%Y-%m-%d %H:%M")
}

response = obj.getCandleData(params)
candles = response["data"]
df = pd.DataFrame(candles, columns=["timestamp", "open", "high", "low", "close", "volume"])
df["timestamp"] = pd.to_datetime(df["timestamp"])
return df

def get_ltp(token, exchange="NSE"): ltp_data = obj.ltpData(exchange, "OPTIDX", str(token)) return ltp_data["data"]["ltp"]

