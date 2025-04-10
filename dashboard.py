import streamlit as st
import pandas as pd
import datetime
from utils import get_instrument_token
from angel_login import smart_api, instruments_df, get_ltp, get_historical_candles

st.set_page_config(layout="wide", page_title="FnO Signal Dashboard")

st.title("FnO Signal Dashboard")

symbol = st.selectbox("Select Symbol", ["NIFTY", "BANKNIFTY"])
interval = st.selectbox("Select Interval", ["FIVE_MINUTE", "FIFTEEN_MINUTE", "ONE_HOUR", "ONE_DAY"])

# Calculate expiry and get token
token_info = get_instrument_token(symbol, instruments_df)
if not token_info:
    st.error("Instrument token not found for symbol.")
    st.stop()

token = token_info['token']
exchange = token_info['exch_seg']

# Define historical time range
now = datetime.datetime.now()
if interval == "ONE_DAY":
    from_date = now - datetime.timedelta(days=60)
elif interval == "ONE_HOUR":
    from_date = now - datetime.timedelta(days=15)
elif interval == "FIFTEEN_MINUTE":
    from_date = now - datetime.timedelta(days=7)
elif interval == "FIVE_MINUTE":
    from_date = now - datetime.timedelta(days=2)
else:
    from_date = now - datetime.timedelta(days=1)

to_date = now

# Fetch historical data
df = get_historical_candles(exchange, token, interval, from_date, to_date)

if df is None or df.empty:
    st.error("No candle data received. Please check token or date range.")
    st.stop()

if len(df) < 10:
    st.warning(f"Only {len(df)} candles received. Not enough for signal generation.")
    st.dataframe(df)
    st.stop()

# Calculate EMAs
df['EMA_5'] = df['close'].ewm(span=5, adjust=False).mean()
df['EMA_20'] = df['close'].ewm(span=20, adjust=False).mean()

# Generate signal
if df['EMA_5'].iloc[-1] > df['EMA_20'].iloc[-1]:
    signal = "BUY"
elif df['EMA_5'].iloc[-1] < df['EMA_20'].iloc[-1]:
    signal = "SELL"
else:
    signal = "HOLD"

ltp = get_ltp(exchange, token)

# Display results
st.header(f"Signal: {signal}")
st.subheader(f"LTP\n{ltp}")

# Line chart
chart_data = df[["close", "EMA_5", "EMA_20"]].dropna()
st.line_chart(chart_data)

# Show table
df['Signal'] = signal
st.dataframe(df.tail(1)[["high", "low", "close", "EMA_5", "EMA_20", "Signal"]])
