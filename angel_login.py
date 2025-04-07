import os
import pyotp
import pandas as pd
from SmartApi.smartConnect import SmartConnect
from dotenv import load_dotenv
from datetime import datetime, timedelta

# Load environment variables
load_dotenv()

CLIENT_CODE = os.getenv("CLIENT_CODE")
PASSWORD = os.getenv("PASSWORD")
TOTP_SECRET = os.getenv("TOTP_SECRET")
API_KEY = os.getenv("API_KEY")

if not all([CLIENT_CODE, PASSWORD, TOTP_SECRET, API_KEY]):
    raise ValueError("Missing one or more environment variables.")

# Login to Angel One API
obj = SmartConnect(api_key=API_KEY)
token = pyotp.TOTP(TOTP_SECRET).now()
data = obj.generateSession(CLIENT_CODE, PASSWORD, token)

# Download instrument list if not already present
if not os.path.exists("instruments.csv"):
    instrument_url = "https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json"
    df = pd.read_json(instrument_url)
    df = df[df['exchange'] == 'NSE']
    df.to_csv("instruments.csv", index=False)

instruments_df = pd.read_csv("instruments.csv")

def get_instrument_token(df, symbol):
    row = df[df['symbol'].str.upper() == symbol.upper()]
    if not row.empty:
        return int(row.iloc[0]['token'])
    else:
        raise ValueError(f"Instrument token for {symbol} not found.")

def get_historical_data(token, interval="5minute", days=5):
    to_date = datetime.now()
    from_date = to_date - timedelta(days=days)

    params = {
        "exchange": "NSE",
        "symboltoken": str(token),
        "interval": interval,
        "fromdate": from_date.strftime('%Y-%m-%d %H:%M'),
        "todate": to_date.strftime('%Y-%m-%d %H:%M')
    }

    response = obj.getCandleData(params)
    candles = response.get("data")

    if not candles:
        raise ValueError("No historical data found.")

    df = pd.DataFrame(candles, columns=["datetime", "open", "high", "low", "close", "volume"])
    df["datetime"] = pd.to_datetime(df["datetime"])
    return df

def get_ltp(token):
    params = {
        "exchange": "NSE",
        "symboltoken": str(token),
        "tradingsymbol": "",
        "symbolname": "",
        "instrumenttype": "",
        "producttype": "",
        "expirydate": "",
        "strikeprice": "",
        "optiontype": ""
    }
    ltp_data = obj.ltpData("NSE", str(token), "")
    return ltp_data.get("data", {}).get("ltp", "N/A")
