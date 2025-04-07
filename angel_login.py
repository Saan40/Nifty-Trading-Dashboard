import os
from SmartApi import SmartConnect
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("ANGEL_API_KEY")
CLIENT_CODE = os.getenv("ANGEL_CLIENT_ID")
PASSWORD = os.getenv("ANGEL_PASSWORD")
TOTP = os.getenv("ANGEL_TOTP")

obj = SmartConnect(api_key=API_KEY)
data = obj.generateSession(CLIENT_CODE, PASSWORD, TOTP)
auth_token = data['data']['jwtToken']

def get_instrument_token(symbol: str, exchange: str = "NSE") -> str:
    instruments = obj.getProfile()
    # For simplicity, returning a fake token — update with real token logic
    return "101"  # Replace with actual lookup logic

def get_ltp(symbol: str, exchange: str = "NSE") -> float:
    data = obj.ltpData(exchange, symbol, symbol)
    return data["data"]["ltp"]

def get_historical_data(token, interval, from_date, to_date):
    params = {
        "exchange": "NSE",
        "symboltoken": token,
        "interval": interval,
        "fromdate": from_date,
        "todate": to_date
    }
    return obj.getCandleData(params)
