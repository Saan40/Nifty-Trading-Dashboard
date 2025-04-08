import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

from angel_login import (
    get_instrument_token,
    get_historical_data,
    get_ltp,
    instruments_df
)

st.set_page_config(page_title="FnO Signal Dashboard", layout="wide")
st.title("Live FnO Trading Signal Dashboard")

# Sidebar
instrument = st.selectbox("Select Instrument", ["NIFTY", "BANKNIFTY"])
timeframe = st.selectbox("Select Timeframe", ["ONE_MINUTE", "FIVE_MINUTE", "FIFTEEN_MINUTE"])

# Dates for historical data
to_date = datetime.now()
from_date = to_date - timedelta(days=1)

# Get instrument token
token = get_instrument_token(instrument)
if not token:
    st.error("Instrument token not found.")
    st.stop()

# Fetch historical data
with st.spinner("Fetching data..."):
    df = get_historical_data(token, timeframe, from_date, to_date)
    if df.empty:
        st.error("No data fetched. Please check symbol or time range.")
        st.stop()

# Calculate indicators
df['EMA_5'] = df['close'].ewm(span=5).mean()
df['EMA_20'] = df['close'].ewm(span=20).mean()
df['Signal'] = df.apply(
    lambda row: "BUY" if row['EMA_5'] > row['EMA_20'] else "SELL", axis=1
)

# Get LTP
ltp = get_ltp(instrument)

# Show signal
latest_signal = df.iloc[-1]["Signal"]
st.subheader(f"Signal: **{latest_signal}**")
st.metric("LTP", value=ltp)

# Plot & Table
st.line_chart(df.set_index("datetime")[["close", "EMA_5", "EMA_20"]])
st.dataframe(df.tail(10)[["datetime", "open", "high", "low", "close", "EMA_5", "EMA_20", "Signal"]])
