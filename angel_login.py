import os
from SmartApi.smartConnect import SmartConnect
import pandas as pd

client_code = os.getenv("ANGEL_CLIENT_CODE")
password = os.getenv("ANGEL_PASSWORD")
totp = os.getenv("ANGEL_TOTP")

obj = SmartConnect(api_key=os.getenv("ANGEL_API_KEY"))
session = obj.generateSession(client_code, password, totp)
refresh_token = session['refreshToken']
auth_token = session['data']['jwtToken']

obj.setAccessToken(auth_token)

instruments_df = pd.read_csv("instruments.csv")

def get_instrument_token(df, symbol):
    row = df[df['name'] == symbol]
    return int(row.iloc[0]['token'])

def get_historical_data(token, interval="5minute", days=2):
    from datetime import datetime, timedelta
    to_date = datetime.now()
    from_date = to_date - timedelta(days=days)
    return pd.DataFrame(obj.getCandleData(token, interval, from_date.strftime('%Y-%m-%d %H:%M'), to_date.strftime('%Y-%m-%d %H:%M'))['data'],
                        columns=['datetime', 'open', 'high', 'low', 'close', 'volume'])

def get_ltp(token):
    data = obj.ltpData('NSE', 'NIFTY', token)
    return data['data']['ltp']
