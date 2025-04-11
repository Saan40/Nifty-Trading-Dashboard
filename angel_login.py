# angel_login.py
import os
import pyotp
import pandas as pd
from dotenv import load_dotenv
from SmartApi.smartConnect import SmartConnect

load_dotenv()

# Load environment variables
api_key = os.getenv("ANGEL_API_KEY")
client_code = os.getenv("ANGEL_CLIENT_CODE")
password = os.getenv("ANGEL_PASSWORD")
totp_secret = os.getenv("ANGEL_TOTP_SECRET")  # 26-character TOTP secret

# Validate all required env vars are set
if not all([api_key, client_code, password, totp_secret]):
    raise Exception("Missing one or more required environment variables: ANGEL_API_KEY, ANGEL_CLIENT_CODE, ANGEL_PASSWORD, ANGEL_TOTP_SECRET")

# Generate TOTP and login
totp = pyotp.TOTP(totp_secret).now()
smart_api = SmartConnect(api_key=api_key)
session = smart_api.generateSession(client_code, password, totp)

if not session or session.get("status") != True:
    raise Exception(f"Login failed! Response: {session}")

# Tokens
feed_token = smart_api.getfeedToken()
auth_token = session["data"]["jwtToken"]

# Load instruments
instruments_df = pd.read_csv("instruments.csv")

# Clean & standardize columns
instruments_df.columns = instruments_df.columns.str.strip().str.lower()

# Auto-select latest weekly expiry instrument token (NIFTY/BANKNIFTY)
def get_instrument_token(symbol):
    df = instruments_df.copy()
    df = df[df['exch_seg'] == 'NFO']
    df = df[df['name'] == symbol]
    df['expiry'] = pd.to_datetime(df['expiry'], errors='coerce')
    df = df[df['expiry'] >= pd.Timestamp.today()]
    df = df.sort_values('expiry')

    if df.empty:
        raise Exception("Instrument token not found.")

    atm = df.iloc[len(df)//2]  # pick a mid strike option
    return {
        "token": str(atm['token']),
        "symbol": atm['trading_symbol'],
        "exchange": atm['exch_seg']
    }

# Get historical candle data
def get_historical_data(token, interval, from_date, to_date, exchange="NFO"):
    params = {
        "exchange": exchange,
        "symboltoken": token,
        "interval": interval,
        "fromdate": from_date.strftime('%Y-%m-%d %H:%M'),
        "todate": to_date.strftime('%Y-%m-%d %H:%M')
    }
    response = smart_api.getCandleData(params)
    return response['data'] if 'data' in response else None

# Get LTP
def get_ltp(symbol, exchange="NFO"):
    try:
        df = instruments_df[(instruments_df['trading_symbol'] == symbol) & (instruments_df['exch_seg'] == exchange)]
        if df.empty:
            return None
        token = str(df.iloc[0]['token'])
        ltp_response = smart_api.ltpData(exchange=exchange, tradingsymbol=symbol, symboltoken=token)
        return float(ltp_response['data']['ltp'])
    except:
        return None
