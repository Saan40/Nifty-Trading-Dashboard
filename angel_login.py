import os
import pyotp
import pandas as pd
from SmartApi.smartConnect import SmartConnect
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()  # Load .env variables

# Load environment variables
api_key = os.getenv("ANGEL_API_KEY")
client_code = os.getenv("ANGEL_CLIENT_CODE")
password = os.getenv("ANGEL_PASSWORD")
totp_secret = os.getenv("ANGEL_TOTP_SECRET")  # 26-character TOTP secret

# Validate environment
if not all([api_key, client_code, password, totp_secret]):
    raise Exception("Missing one or more required environment variables: ANGEL_API_KEY, ANGEL_CLIENT_CODE, ANGEL_PASSWORD, ANGEL_TOTP_SECRET")

# Generate TOTP
totp = pyotp.TOTP(totp_secret).now()

# Create session
obj = SmartConnect(api_key=api_key)
session = obj.generateSession(client_code, password, totp)

if not session or 'status' not in session or session['status'] != True:
    raise Exception(f"Angel One login failed! Response: {session}")

# Tokens
auth_token = session['data']['jwtToken']
refresh_token = session['data']['refreshToken']
feed_token = obj.getfeedToken()

# Load instruments
instruments_df = pd.read_csv("instruments.csv")

# === Utility: Get Instrument Token ===
def get_instrument_token(symbol, exchange="NSE"):
    try:
        row = instruments_df[
            (instruments_df["name"] == symbol) & (instruments_df["exchange"] == exchange)
        ].iloc[0]
        return str(row["token"])
    except Exception as e:
        print(f"Error getting token for {symbol}: {e}")
        return None

# === Utility: Get Historical Data ===
def get_historical_data(token, interval, from_date, to_date, exchange="NSE"):
    params = {
        "exchange": exchange,
        "symboltoken": str(token),
        "interval": interval,
        "fromdate": from_date.strftime('%Y-%m-%d %H:%M'),
        "todate": to_date.strftime('%Y-%m-%d %H:%M')
    }
    try:
        response = obj.getCandleData(params)
        candles = response['data']
        df = pd.DataFrame(candles, columns=["datetime", "open", "high", "low", "close", "volume"])
        df["datetime"] = pd.to_datetime(df["datetime"])
        df[["open", "high", "low", "close", "volume"]] = df[["open", "high", "low", "close", "volume"]].astype(float)
        return df
    except Exception as e:
        print(f"Error fetching historical data: {e}")
        return pd.DataFrame()

# === Utility: Get Latest LTP ===
def get_ltp(symbol, exchange="NSE"):
    token = get_instrument_token(symbol, exchange)
    if not token:
        print(f"Token not found for {symbol} on {exchange}")
        return None
    try:
        response = obj.ltpData(
            exchange=exchange,
            tradingsymbol=symbol,
            symboltoken=token
        )
        return float(response['data']['ltp'])
    except Exception as e:
        print(f"Error getting LTP for {symbol}: {e}")
        return None
