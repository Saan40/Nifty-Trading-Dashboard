import streamlit as st
from angel_login import get_instrument_token, get_historical_data, get_ltp, instruments_df
from datetime import datetime, timedelta
import pandas as pd

st.set_page_config(page_title="FnO Signal Dashboard", layout="wide")
st.title("Live FnO Trading Signal Dashboard")

symbol = st.selectbox("Select Symbol", ["NIFTY", "BANKNIFTY"])
interval = st.selectbox("Select Interval", ["FIFTEEN_MINUTE", "FIVE_MINUTE"])

# Pick correct exch_seg (we're working with NFO for options/futures)
exch_seg = "NFO"

# Lookup instrument token
token = get_instrument_token(instruments_df, symbol, exch_seg)
if not token:
    st.error("Instrument token not found.")
    st.stop()

# Get date range
to_date = datetime.now()
from_date = to_date - timedelta(days=1)

# Load historical data
with st.spinner("Loading historical data..."):
    df = get_historical_data(token, interval, from_date, to_date)
    if df.empty:
        st.error("No data received.")
        st.stop()

# Indicators (no TA-Lib)
df["EMA_5"] = df["close"].ewm(span=5).mean()
df["EMA_20"] = df["close"].ewm(span=20).mean()
df["Signal"] = df.apply(lambda x: "BUY" if x["EMA_5"] > x["EMA_20"] else "SELL", axis=1)

ltp = get_ltp(symbol, exch_seg)

# Display
st.metric("LTP", value=ltp)
st.subheader(f"Signal: {df.iloc[-1]['Signal']}")
st.line_chart(df.set_index("datetime")[["close", "EMA_5", "EMA_20"]])
st.dataframe(df.tail(10)[["datetime", "open", "high", "low", "close", "Signal"]])
