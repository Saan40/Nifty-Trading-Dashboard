# dashboard.py
import streamlit as st
from datetime import datetime, timedelta
from angel_login import get_instrument_token, get_ltp, get_historical_data

st.set_page_config("FnO Signal Dashboard", layout="wide")
st.title("Live FnO Signal Dashboard")

# UI
symbol = st.selectbox("Choose Symbol", ["NIFTY", "BANKNIFTY"])
interval = st.selectbox("Select Timeframe", ["FIVE_MINUTE", "FIFTEEN_MINUTE"])

# Token Fetch
try:
    token_info = get_instrument_token(symbol)
except Exception as e:
    st.error(f"Token Error: {e}")
    st.stop()

# Historical Data
from_date = datetime.now() - timedelta(days=1)
to_date = datetime.now()

with st.spinner("Fetching data..."):
    df = get_historical_data(token_info, interval, from_date, to_date)

if df is None or df.empty:
    st.error("No candle data received.")
    st.stop()

# EMA Strategy
df["EMA5"] = df["close"].ewm(span=5).mean()
df["EMA20"] = df["close"].ewm(span=20).mean()
df["Signal"] = df.apply(lambda row: "BUY" if row["EMA5"] > row["EMA20"] else "SELL", axis=1)

# LTP & Signal
latest = df.iloc[-1]
ltp = get_ltp(token_info)

st.subheader(f"Signal: {latest['Signal']}")
st.metric("LTP", value=ltp)
st.line_chart(df.set_index("datetime")[["close", "EMA5", "EMA20"]])
st.dataframe(df.tail(10)[["datetime", "open", "high", "low", "close", "EMA5", "EMA20", "Signal"]])
