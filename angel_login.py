import os
import pyotp
import pandas as pd
from datetime import datetime, timedelta
from SmartApi.smartConnect import SmartConnect

# Load environment variables
api_key = os.getenv("ANGEL_API_KEY")
client_code = os.getenv("ANGEL_CLIENT_CODE")
password = os.getenv("ANGEL_PASSWORD")
totp_secret = os.getenv("ANGEL_TOTP_SECRET")

# Validate environment variables
if not all([api_key, client_code, password, totp_secret]):
    raise Exception("Missing one or more required environment variables.")

# Generate TOTP and login
totp = pyotp.TOTP(totp_secret).now()
obj = SmartConnect(api_key=api_key)
session = obj.generateSession(client_code, password, totp)

if not session or 'status' not in session or session['status'] is not True:
    raise Exception(f"Angel login failed. Response: {session}")

auth_token = session['data']['jwtToken']
refresh_token = session['data']['refreshToken']
feed_token = obj.getfeedToken()

# Load instruments file
instruments_df = pd.read_csv("instruments.csv")

# --- Auto Weekly Token Lookup ---
def get_weekly_token(symbol, instruments_df):
    today = datetime.now().date()
    next_thursday = today + timedelta((3 - today.weekday()) % 7)
    date_strs = [next_thursday.strftime('%d-%b-%y'), (next_thursday + timedelta(days=7)).strftime('%d-%b-%y')]

    filtered = instruments_df[
        (instruments_df['exch_seg'] == 'NFO') &
        (instruments_df['trading_symbol'].str.contains(symbol)) &
        (instruments_df['trading_symbol'].str.contains('|'.join(date_strs)))
    ]
    if filtered.empty:
        raise Exception(f"No weekly token found for {symbol}")
    selected = filtered.iloc[0]
    print(f"Auto-selected: {selected['trading_symbol']}")
    return str(selected['token'])

# --- Get Historical Data ---
def get_historical_data(token, interval, from_date, to_date, exchange="NFO"):
    params = {
        "exchange": exchange,
        "symboltoken": str(token),
        "interval": interval,
        "fromdate": from_date.strftime('%Y-%m-%d %H:%M'),
        "todate": to_date.strftime('%Y-%m-%d %H:%M')
    }
    try:
        response = obj.getCandleData(params)
        if not response or 'data' not in response or not response['data']:
            raise Exception("No candle data received.")
        df = pd.DataFrame(response['data'], columns=["datetime", "open", "high", "low", "close", "volume"])
        df["datetime"] = pd.to_datetime(df["datetime"])
        return df
    except Exception as e:
        print(f"Error fetching historical data: {e}")
        raise

# --- Get LTP ---
def get_ltp(symbol, exchange="NFO"):
    try:
        token = get_weekly_token(symbol, instruments_df)
        response = obj.ltpData(exchange=exchange, tradingsymbol=symbol, symboltoken=token)
        return float(response['data']['ltp'])
    except Exception as e:
        print(f"Error fetching LTP for {symbol}: {e}")
        return None
