# dashboard.py
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from angel_login import smart_api, instruments_df, get_ltp, get_option_token, get_nearest_expiry, get_historical_data
import plotly.graph_objs as go

st.set_page_config(page_title="FnO Signal Dashboard", layout="wide")

st.title("Live FnO Option Signal Dashboard")

symbol = st.selectbox("Select Instrument", ["NIFTY", "BANKNIFTY"])
interval = st.selectbox("Timeframe", ["5minute", "15minute"])

ltp = get_ltp(symbol, exch_seg="NSE")
if not ltp:
    st.error("LTP fetch failed.")
    st.stop()

expiry = get_nearest_expiry(instruments_df, symbol)
atm_strike = round(ltp / 50) * 50

option_type = st.radio("Select Option Type", ["CE", "PE"])
strike_type = "CE" if option_type == "CE" else "PE"

option_token, trading_symbol = get_option_token(symbol, atm_strike, strike_type, expiry)

if not option_token:
    st.error("ATM option token not found.")
    st.stop()

from_date = datetime.now() - timedelta(days=2)
to_date = datetime.now()

raw = get_historical_data(option_token, interval, from_date, to_date)
if not raw:
    st.error("No candle data received.")
    st.stop()

df = pd.DataFrame(raw, columns=["datetime", "open", "high", "low", "close", "volume"])
df["datetime"] = pd.to_datetime(df["datetime"])

# Simple EMA-based signal
df["EMA5"] = df["close"].ewm(span=5).mean()
df["EMA20"] = df["close"].ewm(span=20).mean()
df["Signal"] = df.apply(lambda row: "BUY" if row["EMA5"] > row["EMA20"] else "SELL", axis=1)

# Display
fig = go.Figure()
fig.add_trace(go.Candlestick(x=df["datetime"], open=df["open"], high=df["high"],
                             low=df["low"], close=df["close"], name="Candles"))
fig.add_trace(go.Scatter(x=df["datetime"], y=df["EMA5"], mode="lines", name="EMA5"))
fig.add_trace(go.Scatter(x=df["datetime"], y=df["EMA20"], mode="lines", name="EMA20"))
fig.update_layout(title=f"{symbol} {trading_symbol} - {interval}", xaxis_rangeslider_visible=False)

st.plotly_chart(fig, use_container_width=True)

latest = df.iloc[-1]
st.metric("Signal", latest["Signal"])
st.metric("LTP", round(latest["close"], 2))
st.write(df.tail(10))
