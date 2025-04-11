import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from angel_login import get_instrument_token, get_historical_data, get_ltp

st.set_page_config("FnO Dashboard", layout="wide")
st.title("Live FnO Signal Dashboard")

symbol = st.selectbox("Select Instrument", ["NIFTY", "BANKNIFTY"])
interval = st.selectbox("Select Timeframe", ["5minute", "15minute"])

token_info = get_instrument_token(symbol)
if not token_info:
    st.error("Token Error: instrument not found")
    st.stop()

from_date = datetime.now() - timedelta(days=1)
to_date = datetime.now()

df = get_historical_data(token_info, interval, from_date, to_date)
if df is None or df.empty:
    st.error("Data error: No candle data received.")
    st.stop()

# Simple EMA logic
df['EMA5'] = df['close'].ewm(span=5).mean()
df['EMA20'] = df['close'].ewm(span=20).mean()
df['Signal'] = df.apply(lambda row: "BUY" if row['EMA5'] > row['EMA20'] else "SELL", axis=1)

ltp = get_ltp(token_info)
signal = df.iloc[-1]["Signal"]

st.metric("Signal", value=signal)
st.metric("LTP", value=ltp)

st.line_chart(df.set_index("datetime")[["close", "EMA5", "EMA20"]])
st.dataframe(df.tail(10))
