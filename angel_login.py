# angel_login.py (Final)
import os
import pyotp
import pandas as pd
from datetime import datetime
from SmartApi.smartConnect import SmartConnect

# Load environment variables
api_key = os.getenv("ANGEL_API_KEY")
client_code = os.getenv("ANGEL_CLIENT_CODE")
password = os.getenv("ANGEL_PASSWORD")
totp_secret = os.getenv("ANGEL_TOTP_SECRET")

# Validate env vars
if not all([api_key, client_code, password, totp_secret]):
    raise Exception("Missing one or more required environment variables.")

# Create TOTP token
totp = pyotp.TOTP(totp_secret).now()

# Angel One API object and login
obj = SmartConnect(api_key=api_key)
session = obj.generateSession(client_code, password, totp)

if not session or session.get("status") != True:
    raise Exception(f"Angel One login failed! Response: {session}")

# Store tokens
auth_token = session['data']['jwtToken']
refresh_token = session['data']['refreshToken']
feed_token = obj.getfeedToken()

# Load instruments
instruments_df = pd.read_csv("instruments.csv")

# Utility: Auto-select current weekly expiry token for NIFTY/BANKNIFTY

def get_weekly_token(symbol):
    today = datetime.now().date()
    this_week = instruments_df[
        (instruments_df['name'] == symbol)
        & (instruments_df['exch_seg'] == 'NFO')
        & (instruments_df['instrumenttype'] == 'OPTIDX')
    ].copy()
    
    this_week['expiry'] = pd.to_datetime(this_week['expiry'], errors='coerce')
    this_week = this_week[this_week['expiry'].dt.date >= today]
    
    if this_week.empty:
        raise Exception(f"No weekly expiry found for {symbol}")

    # Sort by expiry and pick nearest
    nearest = this_week.sort_values('expiry').iloc[0]
    return str(nearest['token'])

# Utility: Get historical data
def get_historical_data(token, interval, from_date, to_date, exchange="NFO"):
    params = {
        "exchange": exchange,
        "symboltoken": str(token),
        "interval": interval,
        "fromdate": from_date.strftime('%Y-%m-%d %H:%M'),
        "todate": to_date.strftime('%Y-%m-%d %H:%M')
    }
    return obj.getCandleData(params)['data']

# Utility: Get LTP
def get_ltp(symbol, exchange="NFO"):
    try:
        token = get_weekly_token(symbol)
        ltp_data = obj.ltpData(exchange=exchange, tradingsymbol=symbol, symboltoken=token)
        return float(ltp_data['data']['ltp'])
    except Exception as e:
        print(f"Error fetching LTP for {symbol}: {e}")
        return None
