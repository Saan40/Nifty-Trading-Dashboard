import os
import pyotp
import pandas as pd
from SmartApi.smartConnect import SmartConnect
from datetime import datetime, timedelta

# ========== Load Environment Variables ==========
api_key = os.getenv("ANGEL_API_KEY")
client_code = os.getenv("ANGEL_CLIENT_CODE")
password = os.getenv("ANGEL_PASSWORD")
totp_secret = os.getenv("ANGEL_TOTP_SECRET")  # 26-char secret key

# ========== Validate ==========
if not all([api_key, client_code, password, totp_secret]):
    raise Exception("Missing one or more required environment variables.")

# ========== Generate TOTP and Login ==========
totp = pyotp.TOTP(totp_secret).now()
obj = SmartConnect(api_key=api_key)
session = obj.generateSession(client_code, password, totp)

if not session or session.get("status") != True:
    raise Exception(f"Login failed! Response: {session}")

auth_token = session['data']['jwtToken']
refresh_token = session['data']['refreshToken']
feed_token = obj.getfeedToken()

# ========== Load instruments.csv ==========
try:
    instruments_df = pd.read_csv("instruments.csv")
except Exception as e:
    raise Exception(f"Error reading instruments.csv: {e}")

# ========== Token Lookup ==========
def get_instrument_token(df, symbol, exchange="NSE"):
    try:
        df = df.astype(str)
        match = df[(df["name"] == symbol) & (df["exchange"] == exchange)]
        if match.empty:
            print(f"[ERROR] Token not found for symbol: {symbol}, exchange: {exchange}")
            print("Available symbols:", df["name"].unique()[:10])
            return None
        return str(match.iloc[0]["token"])
    except Exception as e:
        print(f"[ERROR] Failed to get token for {symbol}: {e}")
        return None

# ========== Fetch Historical Data ==========
def get_historical_data(token, interval, from_date, to_date, exchange="NSE"):
    params = {
        "exchange": exchange,
        "symboltoken": str(token),
        "interval": interval,
        "fromdate": from_date.strftime('%Y-%m-%d %H:%M'),
        "todate": to_date.strftime('%Y-%m-%d %H:%M')
    }
    try:
        data = obj.getCandleData(params)
        candles = data['data']
        df = pd.DataFrame(candles, columns=["datetime", "open", "high", "low", "close", "volume"])
        df["datetime"] = pd.to_datetime(df["datetime"])
        df[["open", "high", "low", "close", "volume"]] = df[["open", "high", "low", "close", "volume"]].astype(float)
        return df
    except Exception as e:
        print(f"[ERROR] Historical data fetch failed: {e}")
        return pd.DataFrame()

# ========== Get LTP ==========
def get_ltp(symbol, exchange="NSE"):
    token = get_instrument_token(instruments_df, symbol, exchange)
    if not token:
        return None
    try:
        response = obj.ltpData(exchange=exchange, tradingsymbol=symbol, symboltoken=token)
        return float(response['data']['ltp'])
    except Exception as e:
        print(f"[ERROR] Failed to get LTP for {symbol}: {e}")
        return None
