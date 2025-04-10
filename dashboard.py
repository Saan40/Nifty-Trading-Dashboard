import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

from angel_login import get_weekly_token, get_historical_data, get_ltp

st.set_page_config(page_title="FnO Signal Dashboard", layout="wide")
st.title("Live FnO Trading Signal Dashboard")

# Sidebar controls
symbol = st.selectbox("Select Instrument", ["NIFTY", "BANKNIFTY"])
timeframe = st.selectbox("Select Timeframe", ["ONE_MINUTE", "FIVE_MINUTE", "FIFTEEN_MINUTE"])

# Get token for current weekly expiry
instrument_token = get_weekly_token(symbol)

if not instrument_token:
    st.error("Instrument token not found.")
    st.stop()

# Define date range for historical data
from_date = datetime.now() - timedelta(days=1)
to_date = datetime.now()

# Fetch historical data
with st.spinner("Fetching historical data..."):
    try:
        candles = get_historical_data(instrument_token, timeframe, from_date, to_date, exchange="NFO")
        if not candles or 'data' not in candles:
            raise ValueError("No candle data received.")

        df = pd.DataFrame(candles['data'], columns=["datetime", "open", "high", "low", "close", "volume"])
        df["datetime"] = pd.to_datetime(df["datetime"])
        df.set_index("datetime", inplace=True)

        # Add simple EMA strategy
        df["EMA_5"] = df["close"].ewm(span=5).mean()
        df["EMA_20"] = df["close"].ewm(span=20).mean()
        df["Signal"] = df.apply(lambda row: "BUY" if row["EMA_5"] > row["EMA_20"] else "SELL", axis=1)

        latest_signal = df.iloc[-1]["Signal"]
        latest_ltp = get_ltp(symbol, exchange="NFO")

        st.subheader(f"Signal: **{latest_signal}**")
        st.metric("LTP", value=latest_ltp)

        st.line_chart(df[["close", "EMA_5", "EMA_20"]])
        st.dataframe(df.tail(10))

    except Exception as e:
        st.error(f"Data error: {e}")
