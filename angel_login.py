import os
import pyotp
import pandas as pd
from SmartApi.smartConnect import SmartConnect
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

api_key = os.getenv("ANGEL_API_KEY")
client_code = os.getenv("ANGEL_CLIENT_CODE")
password = os.getenv("ANGEL_PASSWORD")
totp_secret = os.getenv("ANGEL_TOTP_SECRET")

if not all([api_key, client_code, password, totp_secret]):
    raise Exception("Missing one or more required environment variables.")

# Generate TOTP
totp = pyotp.TOTP(totp_secret).now()

# Authenticate session
smart_api = SmartConnect(api_key=api_key)
session = smart_api.generateSession(client_code, password, totp)

if not session.get("status"):
    raise Exception(f"Angel login failed: {session}")

# Load instrument master
instruments_df = pd.read_csv("instruments.csv")

def get_instrument_token(symbol):
    df = instruments_df[instruments_df["trading_symbol"].str.contains(symbol)]
    df = df[df["exch_seg"] == "NFO"]
    df["expiry_date"] = df["trading_symbol"].str.extract(r'(\d{2}[A-Z]{3}\d{2})')[0]
    df["expiry_date"] = pd.to_datetime(df["expiry_date"], format="%d%b%y", errors='coerce')
    df = df.dropna(subset=["expiry_date"])
    df = df[df["expiry_date"] >= pd.Timestamp.today()]
    if df.empty:
        raise Exception("Instrument not found")
    nearest = df.sort_values("expiry_date").iloc[0]
    return str(nearest["token"])

def get_option_token(symbol, strike, option_type, expiry):
    formatted_strike = f"{int(strike)}"
    match = instruments_df[
        (instruments_df["trading_symbol"].str.startswith(symbol)) &
        (instruments_df["trading_symbol"].str.contains(formatted_strike)) &
        (instruments_df["trading_symbol"].str.endswith(option_type)) &
        (instruments_df["exch_seg"] == "NFO") &
        (instruments_df["trading_symbol"].str.contains(expiry))
    ]
    if match.empty:
        raise Exception("Option token not found.")
    return {
        "token": str(match.iloc[0]["token"]),
        "exch_seg": match.iloc[0]["exch_seg"]
    }

def get_ltp(symbol, exch_seg="NSE"):
    match = instruments_df[
        (instruments_df["trading_symbol"].str.startswith(symbol)) &
        (instruments_df["exch_seg"] == exch_seg)
    ]
    if match.empty:
        raise Exception("LTP lookup failed.")
    token = str(match.iloc[0]["token"])
    try:
        data = smart_api.ltpData(exchange=exch_seg, tradingsymbol=symbol, symboltoken=token)
        return float(data["data"]["ltp"])
    except (KeyError, TypeError, ValueError):
        raise Exception("LTP fetch failed or malformed response.")

def get_historical_data(token, interval, from_date, to_date, exchange="NFO"):
    params = {
        "exchange": exchange,
        "symboltoken": str(token),
        "interval": interval,
        "fromdate": from_date.strftime('%Y-%m-%d %H:%M'),
        "todate": to_date.strftime('%Y-%m-%d %H:%M')
    }
    candles = smart_api.getCandleData(params)
    if not candles.get("data"):
        raise Exception("No candle data received.")
    df = pd.DataFrame(candles["data"], columns=["datetime", "open", "high", "low", "close", "volume"])
    df["datetime"] = pd.to_datetime(df["datetime"])
    return df
