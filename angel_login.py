# angel_login.py (final with auto expiry logic)
import os
import pyotp
import pandas as pd
from datetime import datetime, timedelta
from SmartApi.smartConnect import SmartConnect
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
api_key = os.getenv("ANGEL_API_KEY")
client_code = os.getenv("ANGEL_CLIENT_CODE")
password = os.getenv("ANGEL_PASSWORD")
totp_secret = os.getenv("ANGEL_TOTP_SECRET")

if not all([api_key, client_code, password, totp_secret]):
    raise Exception("Missing one or more required environment variables: ANGEL_API_KEY, ANGEL_CLIENT_CODE, ANGEL_PASSWORD, ANGEL_TOTP_SECRET")

totp = pyotp.TOTP(totp_secret).now()
obj = SmartConnect(api_key=api_key)
session = obj.generateSession(client_code, password, totp)

if not session or 'status' not in session or session['status'] != True:
    raise Exception(f"Angel One login failed! Response: {session}")

auth_token = session['data']['jwtToken']
refresh_token = session['data']['refreshToken']
feed_token = obj.getfeedToken()

# Load instrument data
instruments_df = pd.read_csv("instruments.csv")

# Get nearest weekly expiry for NIFTY/BANKNIFTY
def get_latest_expiry_token(symbol):
    now = datetime.now()
    weekly_options = instruments_df[
        (instruments_df['trading_symbol'].str.startswith(symbol)) &
        (instruments_df['exch_seg'] == 'NFO') &
        (instruments_df['trading_symbol'].str.contains("CE") | instruments_df['trading_symbol'].str.contains("PE"))
    ]
    weekly_options = weekly_options.copy()
    weekly_options['expiry'] = pd.to_datetime(weekly_options['trading_symbol'].str.extract(r"(\d{2}[A-Z]{3}\d{2})")[0], format="%d%b%y", errors='coerce')
    weekly_options = weekly_options.dropna(subset=['expiry'])
    weekly_options = weekly_options[weekly_options['expiry'] >= now]
    weekly_options = weekly_options.sort_values('expiry')
    if weekly_options.empty:
        raise Exception(f"No upcoming expiry found for {symbol}")
    first = weekly_options.iloc[0]
    return str(first['token']), first['trading_symbol'], first['expiry'].strftime('%d-%b-%Y')

def get_ltp(symbol, token):
    try:
        response = obj.ltpData(exchange="NFO", tradingsymbol=symbol, symboltoken=str(token))
        return float(response['data']['ltp'])
    except Exception as e:
        print(f"LTP error: {e}")
        return None

def get_historical_data(token, interval, from_date, to_date):
    try:
        params = {
            "exchange": "NFO",
            "symboltoken": str(token),
            "interval": interval,
            "fromdate": from_date.strftime('%Y-%m-%d %H:%M'),
            "todate": to_date.strftime('%Y-%m-%d %H:%M')
        }
        response = obj.getCandleData(params)
        df = pd.DataFrame(response['data'], columns=["datetime", "open", "high", "low", "close", "volume"])
        df["datetime"] = pd.to_datetime(df["datetime"])
        df[["open", "high", "low", "close"]] = df[["open", "high", "low", "close"]].astype(float)
        return df
    except Exception as e:
        print(f"Historical data error: {e}")
        return pd.DataFrame()
