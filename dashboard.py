import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.graph_objs as go

from angel_login import smart_api, instruments_df, get_option_token
from utils import calculate_indicators, generate_signal, calculate_tp_sl

st.set_page_config("FnO Signal Dashboard", layout="wide")

st.title("Live FnO Options Signal Dashboard")

# User selections
symbol = st.selectbox("Select Instrument", ["NIFTY", "BANKNIFTY"])
timeframe = st.selectbox("Select Timeframe", ["5minute", "15minute"])

# Get latest expiry option token
option_info = get_option_token(symbol)
if not option_info:
    st.error("Token Error: instrument not found")
    st.stop()

token = option_info["token"]
exchange = option_info["exch_seg"]
tradingsymbol = option_info["symbol"]

# Date range: last 2 days
to_date = datetime.now()
from_date = to_date - timedelta(days=2)

# Fetch data
params = {
    "exchange": exchange,
    "symboltoken": str(token),
    "interval": timeframe.upper(),
    "fromdate": from_date.strftime("%Y-%m-%d %H:%M"),
    "todate": to_date.strftime("%Y-%m-%d %H:%M"),
}

try:
    raw_data = smart_api.getCandleData(params)
    candles = raw_data.get("data", [])
    if not candles:
        st.error("Data error: No candle data received.")
        st.stop()

    df = pd.DataFrame(candles, columns=["datetime", "open", "high", "low", "close", "volume"])
    df["datetime"] = pd.to_datetime(df["datetime"])
    df = calculate_indicators(df)
except Exception as e:
    st.error(f"Data Fetch Error: {e}")
    st.stop()

# Generate signal
signal = generate_signal(df)
ltp = df.iloc[-1]["close"]
tp, sl = calculate_tp_sl(df, ltp, signal)

# Display
st.subheader(f"Signal: **{signal}**")
st.metric("LTP", round(ltp, 2))
st.metric("TP", tp)
st.metric("SL", sl)

# Plot chart with annotations
fig = go.Figure()

fig.add_trace(go.Candlestick(
    x=df["datetime"],
    open=df["open"], high=df["high"],
    low=df["low"], close=df["close"],
    name="Candles"
))

fig.add_trace(go.Scatter(
    x=df["datetime"], y=df["EMA_9"],
    mode="lines", name="EMA 9", line=dict(color="blue")
))
fig.add_trace(go.Scatter(
    x=df["datetime"], y=df["EMA_21"],
    mode="lines", name="EMA 21", line=dict(color="orange")
))

# Add signal marker
fig.add_trace(go.Scatter(
    x=[df.iloc[-1]["datetime"]],
    y=[ltp],
    mode="markers+text",
    marker=dict(size=12, color="green" if signal == "CALL" else "red"),
    text=[f"{signal}"],
    textposition="top center",
    name="Signal"
))

fig.update_layout(height=600, title="Live Candle Chart with Signal", xaxis_rangeslider_visible=False)
st.plotly_chart(fig, use_container_width=True)

# Refresh every 30 seconds
st.experimental_rerun()
