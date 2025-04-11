import os
import pyotp
import pandas as pd
from SmartApi.smartConnect import SmartConnect
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

# Load credentials
api_key = os.getenv("ANGEL_API_KEY")
client_code = os.getenv("ANGEL_CLIENT_CODE")
password = os.getenv("ANGEL_PASSWORD")
totp_secret = os.getenv("ANGEL_TOTP_SECRET")

# Validate
if not all([api_key, client_code, password, totp_secret]):
    raise Exception("Missing one or more required environment variables.")

# Generate TOTP
totp = pyotp.TOTP(totp_secret).now()
smart_api = SmartConnect(api_key=api_key)
session = smart_api.generateSession(client_code, password, totp)

if not session.get("status"):
    raise Exception(f"Login failed: {session}")

# Load instruments
instruments_df = pd.read_csv("instruments.csv")

# Function: get option token by ATM strike
def get_option_token(symbol, strike, option_type, expiry):
    filtered = instruments_df[(instruments_df["name"] == symbol) &
                               (instruments_df["exch_seg"] == "NFO") &
                               (instruments_df["symbol"].str.endswith(option_type)) &
                               (instruments_df["expiry"] == expiry)]
    filtered["strike"] = filtered["strike"].astype(float)
    closest = filtered.iloc[(filtered["strike"] - strike).abs().argsort()[:1]]
    if not closest.empty:
        return {
            "token": str(closest.iloc[0]["token"]),
            "trading_symbol": closest.iloc[0]["symbol"],
            "exch_seg": closest.iloc[0]["exch_seg"]
        }
    return None

# Function: get weekly expiry
def get_latest_expiry(symbol):
    df = instruments_df[(instruments_df["name"] == symbol) & (instruments_df["exch_seg"] == "NFO")]
    expiries = pd.to_datetime(df["expiry"], errors='coerce')
    valid = expiries[expiries >= pd.Timestamp.today()]
    return valid.sort_values().iloc[0].strftime("%d-%b-%Y") if not valid.empty else None

# Function: get instrument token for future
def get_futures_token(symbol):
    df = instruments_df[(instruments_df["name"] == symbol) & (instruments_df["exch_seg"] == "NFO") &
                        (instruments_df["instrumenttype"] == "FUTIDX")]
    df["expiry"] = pd.to_datetime(df["expiry"], errors='coerce')
    df = df[df["expiry"] >= pd.Timestamp.today()]
    df = df.sort_values("expiry")
    if not df.empty:
        return {
            "token": str(df.iloc[0]["token"]),
            "trading_symbol": df.iloc[0]["symbol"],
            "exch_seg": df.iloc[0]["exch_seg"]
        }
    return None

# Function: get historical data
def get_historical_data(token, interval, from_date, to_date, exch_seg="NFO"):
    params = {
        "exchange": exch_seg,
        "symboltoken": token,
        "interval": interval,
        "fromdate": from_date.strftime("%Y-%m-%d %H:%M"),
        "todate": to_date.strftime("%Y-%m-%d %H:%M")
    }
    response = smart_api.getCandleData(params)
    data = response.get("data")
    if not data:
        return None
    df = pd.DataFrame(data, columns=["datetime", "open", "high", "low", "close", "volume"])
    df["datetime"] = pd.to_datetime(df["datetime"])
    return df

# Function: get LTP
def get_ltp(symbol, exch_seg="NSE"):
    row = instruments_df[(instruments_df["name"] == symbol) & (instruments_df["exch_seg"] == exch_seg)]
    if row.empty:
        return None
    token = str(row.iloc[0]["token"])
    data = smart_api.ltpData(exchange=exch_seg, tradingsymbol=row.iloc[0]["symbol"], symboltoken=token)
    return data['data']['ltp'] if 'data' in data else None
