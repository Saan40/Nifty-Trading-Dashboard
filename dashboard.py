import streamlit as st
import pandas as pd
from angel_login import get_instrument_token, get_historical_data, get_ltp, instruments_df
from utils import calculate_indicators, identify_candlestick_patterns, generate_signal
from datetime import datetime

# Streamlit page setup
st.set_page_config(page_title="FnO Signal Dashboard", layout="wide")
st.title("Live FnO Trading Signal Dashboard")

# Sidebar options
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

# Calculate indicators and patterns
df = calculate_indicators(df)
df = identify_candlestick_patterns(df)
signal = generate_signal(df)

# Get latest price
ltp = get_ltp(instrument_token)
latest_close = df.iloc[-1]["close"]

# Display dashboard
st.subheader(f"Signal: **{signal}**")
st.metric("LTP", value=ltp)
st.line_chart(df.set_index("datetime")[["close", "EMA_9", "EMA_21", "MACD", "MACD_signal"]])
st.dataframe(df.tail(10)[[
    "datetime", "open", "high", "low", "close",
    "EMA_9", "EMA_21", "RSI", "MACD", "MACD_signal", "ATR",
    "bullish_engulfing", "bearish_engulfing"
]])
