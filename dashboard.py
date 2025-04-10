import streamlit as st
import pandas as pd
import plotly.graph_objs as go
from datetime import datetime, timedelta
from angel_login import obj, instruments_df, get_instrument_token
from utils import get_signal, calculate_tp_sl, fetch_historical_data

st.set_page_config(page_title="FnO Signal Dashboard", layout="wide")
st.title("Live FnO Trading Signal Dashboard")

# UI
symbol = st.selectbox("Select Instrument", ["NIFTY", "BANKNIFTY"])
timeframe = st.selectbox("Select Timeframe", ["5minute", "15minute"])
refresh = st.button("Refresh")

# Time window (last 1 day)
to_date = datetime.now()
from_date = to_date - timedelta(days=1)

# Get token
try:
    token_info = get_instrument_token(symbol, instruments_df)
    if not token_info:
        st.error("Instrument token not found.")
        st.stop()
    token = token_info["token"]
    exch_seg = token_info["exch_seg"]
except Exception as e:
    st.error(f"Token Error: {e}")
    st.stop()

# Fetch data
with st.spinner("Fetching data..."):
    df = fetch_historical_data(obj, token, interval=timeframe, from_date=from_date, to_date=to_date, exchange=exch_seg)
    if df.empty:
        st.error("Data error: No candle data received.")
        st.stop()

# Generate signal
signal = get_signal(df)
entry, tp, sl = calculate_tp_sl(df, signal)

# Display metrics
st.subheader(f"Signal: **{signal}**")
st.metric("Entry", value=entry)
st.metric("Target (TP)", value=tp)
st.metric("Stop Loss (SL)", value=sl)

# Candlestick chart with indicators and TP/SL
fig = go.Figure(data=[go.Candlestick(
    x=df['datetime'],
    open=df['open'], high=df['high'],
    low=df['low'], close=df['close'],
    name="Candles"
)])

# Add EMA lines
fig.add_trace(go.Scatter(x=df['datetime'], y=df['close'].ewm(span=5).mean(), name='EMA 5', line=dict(color='green')))
fig.add_trace(go.Scatter(x=df['datetime'], y=df['close'].ewm(span=20).mean(), name='EMA 20', line=dict(color='red')))

# Add TP/SL markers
if signal in ["BUY", "SELL"]:
    fig.add_hline(y=tp, line=dict(color="blue", dash="dash"), annotation_text="TP", annotation_position="top left")
    fig.add_hline(y=sl, line=dict(color="orange", dash="dash"), annotation_text="SL", annotation_position="bottom left")
    fig.add_hline(y=entry, line=dict(color="black", dash="dot"), annotation_text="Entry", annotation_position="bottom right")

fig.update_layout(title="Price Chart with EMA & Signals", xaxis_rangeslider_visible=False, height=600)
st.plotly_chart(fig, use_container_width=True)

# Optional: Show last 10 rows
st.dataframe(df.tail(10))
