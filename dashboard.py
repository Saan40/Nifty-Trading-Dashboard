# dashboard.py
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from angel_login import get_weekly_token, get_historical_data, get_ltp

st.set_page_config(page_title="FnO Signal Dashboard", layout="wide")
st.title("Live FnO Trading Signal Dashboard")

symbol = st.selectbox("Select Instrument", ["NIFTY", "BANKNIFTY"])
timeframe = st.selectbox("Select Timeframe", ["ONE_MINUTE", "FIFTEEN_MINUTE"])

# Token fetch
try:
    token, trading_symbol = get_weekly_token(symbol)
except Exception as e:
    st.error(f"Token Error: {e}")
    st.stop()

# Date range
from_date = datetime.now() - timedelta(days=1)
to_date = datetime.now()

# Historical data
with st.spinner("Fetching data..."):
    try:
        candles = get_historical_data(token, timeframe, from_date, to_date)
        df = pd.DataFrame(candles, columns=["datetime", "open", "high", "low", "close", "volume"])
        df["datetime"] = pd.to_datetime(df["datetime"])
        df["EMA_5"] = df["close"].ewm(span=5).mean()
        df["EMA_20"] = df["close"].ewm(span=20).mean()
        df["Signal"] = df.apply(lambda row: "BUY" if row["EMA_5"] > row["EMA_20"] else "SELL", axis=1)
    except Exception as e:
        st.error(f"Data Error: {e}")
        st.stop()

# LTP
ltp = get_ltp(token)

# Display
st.subheader(f"Trading Symbol: {trading_symbol}")
st.metric("LTP", value=ltp)
st.subheader(f"Signal: {df.iloc[-1]['Signal']}")
st.line_chart(df.set_index("datetime")[["close", "EMA_5", "EMA_20"]])
st.dataframe(df.tail(10))
