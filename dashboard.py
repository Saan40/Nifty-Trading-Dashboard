# dashboard.py
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from angel_login import (
    instruments_df,
    get_instrument_token,
    get_historical_data,
    get_ltp
)

st.set_page_config(page_title="FnO Signal Dashboard", layout="wide")
st.title("Live FnO Trading Signal Dashboard")

# User input
symbol = st.selectbox("Select Symbol", ["NIFTY", "BANKNIFTY"])
timeframe = st.selectbox("Select Timeframe", ["ONE_MINUTE", "FIFTEEN_MINUTE", "FIVE_MINUTE"])

# Get token
instrument_token = get_instrument_token(instruments_df, symbol, exchange="NFO")
if not instrument_token:
    st.error("Instrument token not found.")
    st.stop()

# Date range
to_date = datetime.now()
from_date = to_date - timedelta(days=1)

# Get historical data
df = get_historical_data(instrument_token, timeframe, from_date, to_date, exchange="NFO")
if df is None or 'data' not in df:
    st.error("Failed to fetch historical data.")
    st.stop()

# Format data
candles = df['data']
df = pd.DataFrame(candles, columns=["datetime", "open", "high", "low", "close", "volume"])
df["datetime"] = pd.to_datetime(df["datetime"])
df.set_index("datetime", inplace=True)
df = df.astype(float)

# Simple strategy
df['EMA_5'] = df['close'].ewm(span=5).mean()
df['EMA_20'] = df['close'].ewm(span=20).mean()
df['Signal'] = df.apply(
    lambda row: "BUY" if row['EMA_5'] > row['EMA_20'] else "SELL", axis=1
)

# Display
ltp = get_ltp(symbol, exchange="NFO")
st.subheader(f"Signal: {df.iloc[-1]['Signal']}")
st.metric("LTP", value=ltp)
st.line_chart(df[["close", "EMA_5", "EMA_20"]])
st.dataframe(df.tail(10)[["open", "high", "low", "close", "EMA_5", "EMA_20", "Signal"]])
