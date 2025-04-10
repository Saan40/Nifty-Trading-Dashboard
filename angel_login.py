import os
import pandas as pd
import pyotp
import logging
from SmartApi.smartConnect import SmartConnect
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Logger
logging.basicConfig(level=logging.INFO)

client_code = os.getenv("CLIENT_CODE")
password = os.getenv("PASSWORD")
totp_secret = os.getenv("TOTP_SECRET")
api_key = os.getenv("API_KEY")

# Create SmartConnect object
smart_api = SmartConnect(api_key)

# TOTP
totp = pyotp.TOTP(totp_secret).now()
data = smart_api.generateSession(client_code, password, totp)

# Load instruments.csv
instruments_df = pd.read_csv("instruments.csv")

# Utility to get LTP
def get_ltp(exchange, token):
    try:
        ltp_data = smart_api.ltpData(exchange=exchange, tradingsymbol=None, symboltoken=str(token))
        return float(ltp_data["data"]["ltp"])
    except Exception as e:
        logging.error(f"LTP fetch failed: {e}")
        return None

# Utility to get historical candles
def get_historical_candles(exchange, token, interval, from_date, to_date):
    try:
        data = smart_api.getCandleData(
            token=str(token),
            interval=interval,
            fromdate=from_date.strftime('%Y-%m-%d %H:%M'),
            todate=to_date.strftime('%Y-%m-%d %H:%M')
        )
        candles = data['data']
        if not candles:
            logging.warning("No candles returned from API.")
            return None

        df = pd.DataFrame(candles, columns=["timestamp", "open", "high", "low", "close", "volume"])
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df.set_index('timestamp', inplace=True)
        return df

    except Exception as e:
        logging.error(f"Error fetching historical data: {e}")
        return None
