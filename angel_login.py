import os
import pandas as pd
from SmartApi.smartConnect import SmartConnect

# Load credentials from environment variables
api_key = os.getenv("ANGEL_API_KEY")
client_code = os.getenv("ANGEL_CLIENT_CODE")
password = os.getenv("ANGEL_PASSWORD")
totp = os.getenv("ANGEL_TOTP")

# Create SmartConnect object
obj = SmartConnect(api_key=api_key)

# Generate session and handle errors gracefully
session = obj.generateSession(client_code, password, totp)

if 'status' not in session:
    print("Login failed! Response:", session)
    raise Exception("Angel One login failed. Check credentials or API key.")

if session['status'] != True:
    print("Login unsuccessful. Full response:", session)
    raise Exception("Angel One login returned unsuccessful status.")

# Fetch user profile (optional)
user_profile = obj.getProfile(session["data"]["refreshToken"])

# Load instruments.csv
instruments_df = pd.read_csv("instruments.csv")

# Utility: Get token for symbol
def get_instrument_token(symbol: str) -> str:
    token_row = instruments_df[instruments_df['tradingsymbol'] == symbol]
    return str(token_row['token'].values[0]) if not token_row.empty else None

# Utility: Get LTP
def get_ltp(symbol: str, exchange: str = "NSE") -> float:
    token = get_instrument_token(symbol)
    if not token:
        return None
    try:
        ltp_data = obj.ltpData(exchange=exchange, tradingsymbol=symbol, symboltoken=token)
        return ltp_data["data"]["ltp"]
    except Exception as e:
        print(f"LTP fetch error for {symbol}: {e}")
        return None

# Utility: Get historical data (5min, 15min etc.)
def get_historical_data(symbol, interval="FIFTEEN_MINUTE", days=1, exchange="NSE"):
    token = get_instrument_token(symbol)
    if not token:
        return []
    params = {
        "exchange": exchange,
        "symboltoken": token,
        "interval": interval,
        "fromdate": pd.Timestamp.now() - pd.Timedelta(days=days),
        "todate": pd.Timestamp.now(),
        "tradingsymbol": symbol
    }
    try:
        data = obj.getCandleData(params)
        return data["data"]
    except Exception as e:
        print(f"Historical data fetch error for {symbol}: {e}")
        return []
