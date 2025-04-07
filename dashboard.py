import streamlit as st
import pandas as pd
from angel_login import get_instrument_token, get_historical_data, get_ltp, instruments_df
from datetime import datetime

st.set_page_config(page_title="FnO Signal Dashboard", layout="wide")
st.title("Live FnO Trading Signal Dashboard")

# Sidebar
instrument = st.selectbox("Select Instrument", ["NIFTY", "BANKNIFTY"])
timeframe = st.selectbox("Select Timeframe", ["5minute", "15minute"])

# Get instrument token
try:
    instrument_token = get_instrument_token(instruments_df, instrument)
except Exception as e:
    st.error(f"Token error: {e}")
    st.stop()

# Fetch historical data
with st.spinner("Fetching live data..."):
    try:
        df = get_historical_data(instrument_token, interval=timeframe)
    except Exception as e:
        st.error(f"Data error: {e}")
        st.stop()

# Simple indicator logic (no TA-Lib)
df['EMA_5'] = df['close'].ewm(span=5).mean()
df['EMA_20'] = df['close'].ewm(span=20).mean()
df['Signal'] = df.apply(
    lambda row: "BUY" if row['EMA_5'] > row['EMA_20'] else "SELL", axis=1
)

# Latest signal
latest_signal = df.iloc[-1]["Signal"]
latest_close = df.iloc[-1]["close"]
ltp = get_ltp(instrument_token)

# Display results
st.subheader(f"Signal: **{latest_signal}**")
st.metric("LTP", value=ltp)
st.line_chart(df.set_index("datetime")[["close", "EMA_5", "EMA_20"]])
st.dataframe(df.tail(10)[["datetime", "open", "high", "low", "close", "EMA_5", "EMA_20", "Signal"]])
