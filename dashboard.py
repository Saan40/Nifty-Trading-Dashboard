import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from angel_login import get_instrument_token, get_historical_data, get_ltp, instruments_df

st.set_page_config(page_title="FnO Signal Dashboard", layout="wide")
st.title("Live FnO Trading Signal Dashboard")

# Sidebar selections
symbol = st.selectbox("Select Instrument", ["NIFTY", "BANKNIFTY"])
interval = st.selectbox("Select Timeframe", ["ONE_MINUTE", "FIVE_MINUTE", "FIFTEEN_MINUTE"])

# Token lookup
instrument_token = get_instrument_token(instruments_df, symbol, exchange="NSE")
if not instrument_token:
    st.error("Instrument token not found.")
    st.stop()

# Date range
from_date = datetime.now() - timedelta(days=1)
to_date = datetime.now()

# Get data
with st.spinner("Fetching live data..."):
    data = get_historical_data(instrument_token, interval, from_date, to_date)
    if not data or "data" not in data:
        st.error("Failed to fetch historical data.")
        st.stop()
    df = pd.DataFrame(data["data"], columns=["datetime", "open", "high", "low", "close", "volume"])
    df["datetime"] = pd.to_datetime(df["datetime"])
    df[["open", "high", "low", "close", "volume"]] = df[["open", "high", "low", "close", "volume"]].astype(float)

# Simple EMA strategy
df["EMA_5"] = df["close"].ewm(span=5).mean()
df["EMA_20"] = df["close"].ewm(span=20).mean()
df["Signal"] = df.apply(lambda x: "BUY" if x["EMA_5"] > x["EMA_20"] else "SELL", axis=1)

# LTP
ltp = get_ltp(symbol)

# Display
latest_signal = df.iloc[-1]["Signal"]
st.metric("LTP", value=ltp)
st.subheader(f"Signal: **{latest_signal}**")

st.line_chart(df.set_index("datetime")[["close", "EMA_5", "EMA_20"]])
st.dataframe(df.tail(10)[["datetime", "open", "high", "low", "close", "EMA_5", "EMA_20", "Signal"]])
