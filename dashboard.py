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

# Sidebar selections
symbol = st.selectbox("Select Instrument", ["NIFTY", "BANKNIFTY"])
timeframe = st.selectbox("Select Timeframe", ["ONE_MINUTE", "FIVE_MINUTE", "FIFTEEN_MINUTE"])

# Dates
to_date = datetime.now()
from_date = to_date - timedelta(days=1)

# Get instrument token
instrument_token = get_instrument_token(instruments_df, symbol, exch_seg="NFO")

if not instrument_token:
    st.error("Instrument token not found.")
    st.stop()

# Fetch historical data
with st.spinner("Fetching historical data..."):
    candles = get_historical_data(token=instrument_token, interval=timeframe, from_date=from_date, to_date=to_date)

    if not candles:
        st.error("Failed to fetch historical data.")
        st.stop()

    df = pd.DataFrame(candles['data'], columns=["datetime", "open", "high", "low", "close", "volume"])
    df["datetime"] = pd.to_datetime(df["datetime"])
    df.set_index("datetime", inplace=True)

# Add indicators (basic EMA-based signal)
df["EMA_5"] = df["close"].ewm(span=5, adjust=False).mean()
df["EMA_20"] = df["close"].ewm(span=20, adjust=False).mean()
df["Signal"] = df.apply(lambda row: "BUY" if row["EMA_5"] > row["EMA_20"] else "SELL", axis=1)

# Get latest LTP
ltp = get_ltp(symbol, exch_seg="NFO")

# Display results
latest_signal = df.iloc[-1]["Signal"]

st.subheader(f"Signal: **{latest_signal}**")
st.metric("LTP", value=ltp)
st.line_chart(df[["close", "EMA_5", "EMA_20"]])
st.dataframe(df.tail(10))
