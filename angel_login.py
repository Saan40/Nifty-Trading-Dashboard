# angel_login.py
import os
import pyotp
import pandas as pd
from SmartApi.smartConnect import SmartConnect
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Load credentials
api_key = os.getenv("ANGEL_API_KEY")
client_code = os.getenv("ANGEL_CLIENT_CODE")
password = os.getenv("ANGEL_PASSWORD")
totp_secret = os.getenv("ANGEL_TOTP_SECRET")

if not all([api_key, client_code, password, totp_secret]):
    raise Exception("Missing one or more required environment variables.")

# Login
totp = pyotp.TOTP(totp_secret).now()
smart_api = SmartConnect(api_key=api_key)
session = smart_api.generateSession(client_code, password, totp)

if not session.get("status") or session["status"] != True:
    raise Exception("Login failed:", session)

# Load instruments
instruments_df = pd.read_csv("instruments.csv")

# Utility: get nearest weekly expiry
def get_nearest_expiry(df, symbol):
    df = df[df["trading_symbol"].str.startswith(symbol)]
    df["expiry"] = pd.to_datetime(df["expiry"], errors="coerce")
    df = df[df["expiry"] >= pd.Timestamp(datetime.now())]
    return df.sort_values("expiry").iloc[0]["expiry"]

# Utility: ATM strike from LTP
def get_ltp(symbol, exch_seg="NSE"):
    row = instruments_df[(instruments_df["name"] == symbol) & (instruments_df["exch_seg"] == exch_seg)]
    if row.empty:
        return None
    token = row.iloc[0]["token"]
    data = smart_api.ltpData(exchange=exch_seg, tradingsymbol=row.iloc[0]["trading_symbol"], symboltoken=token)
    return float(data["data"]["ltp"])

# Utility: Get option token
def get_option_token(symbol, strike, option_type, expiry):
    strike = round(strike)
    option_strike = f"{symbol}{expiry.strftime('%d%b%y').upper()}{strike}{option_type}"
    match = instruments_df[instruments_df["trading_symbol"].str.startswith(option_strike)]
    if not match.empty:
        row = match.iloc[0]
        return row["token"], row["trading_symbol"]
    return None, None

# Utility: Historical candles
def get_historical_data(token, interval, from_date, to_date, exchange="NFO"):
    params = {
        "exchange": exchange,
        "symboltoken": str(token),
        "interval": interval,
        "fromdate": from_date.strftime('%Y-%m-%d %H:%M'),
        "todate": to_date.strftime('%Y-%m-%d %H:%M')
    }
    response = smart_api.getCandleData(params)
    return response["data"] if "data" in response else []
