import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from angel_login import get_instrument_token, get_historical_data, get_ltp, instruments_df

st.set_page_config(page_title="FnO Signal Dashboard", layout="wide")
st.title("Live FnO Trading Signal Dashboard")

# Select instrument
symbol = st.selectbox("Select Instrument", ["NIFTY", "BANKNIFTY"])
interval = st.selectbox("Select Timeframe", ["ONE_MINUTE", "FIFTEEN_MINUTE"])

# Get instrument token
instrument_token = get_instrument_token(instruments_df, symbol)
if not instrument_token:
    st.error("Instrument token not found.")
    st.stop()

# Define from/to dates
from_date = datetime.now() - timedelta(days=1)
to_date = datetime.now()

# Load data
try:
    df = get_historical_data(instrument_token, interval, from_date, to_date)
except Exception as e:
    st.error(f"Data error: {e}")
    st.stop()

# Indicators
df["EMA_5"] = df["close"].ewm(span=5).mean()
df["EMA_20"] = df["close"].ewm(span=20).mean()
df["Signal"] = df.apply(lambda x: "BUY" if x["EMA_5"] > x["EMA_20"] else "SELL", axis=1)

# Display results
ltp = get_ltp(symbol)
signal = df.iloc[-1]["Signal"]
st.subheader(f"Signal: **{signal}**")
st.metric("LTP", value=ltp)
st.line_chart(df.set_index("datetime")[["close", "EMA_5", "EMA_20"]])
st.dataframe(df.tail(10)[["datetime", "open", "high", "low", "close", "EMA_5", "EMA_20", "Signal"]])
