import os
import pandas as pd
from SmartApi.smartConnect import SmartConnect

# Load credentials from Render environment variables
api_key = os.getenv("ANGEL_API_KEY")
client_code = os.getenv("ANGEL_CLIENT_CODE")
password = os.getenv("ANGEL_PASSWORD")
totp = os.getenv("ANGEL_TOTP")

# Check if any variable is missing
if not all([api_key, client_code, password, totp]):
    raise Exception("Missing one or more required environment variables (ANGEL_API_KEY, CLIENT_CODE, PASSWORD, TOTP).")

# Create SmartConnect object
obj = SmartConnect(api_key=api_key)

# Try to login and validate response
try:
    session = obj.generateSession(client_code, password, totp)
    if not isinstance(session, dict) or 'status' not in session:
        raise Exception(f"Invalid login response: {session}")
    if session['status'] != True:
        raise Exception(f"Login failed with message: {session.get('message', 'No message')}")
except Exception as e:
    raise Exception(f"Angel One login error: {e}")

# (Optional) fetch profile
user_profile = obj.getProfile(session["data"]["refreshToken"])

# Load instrument file
instruments_df = pd.read_csv("instruments.csv")

# Utility: Token from symbol
def get_instrument_token(symbol: str) -> str:
    row = instruments_df[instruments_df['tradingsymbol'] == symbol]
    return str(row['token'].values[0]) if not row.empty else None

# Utility: LTP
def get_ltp(symbol: str, exchange: str = "NSE") -> float:
    token = get_instrument_token(symbol)
    if not token:
        return None
    try:
        ltp_data = obj.ltpData(exchange=exchange, tradingsymbol=symbol, symboltoken=token)
        return ltp_data["data"]["ltp"]
    except Exception as e:
        print(f"LTP fetch error: {e}")
        return None

# Utility: Historical data
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
        candles = obj.getCandleData(params)
        return candles.get("data", [])
    except Exception as e:
        print(f"Historical fetch error: {e}")
        return []
