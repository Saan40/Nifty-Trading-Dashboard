import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

from angel_login import (
    instruments_df,
    get_option_token,
    get_historical_data,
    get_ltp
)
from utils import calculate_indicators, generate_signal, calculate_tp_sl

st.set_page_config(page_title="Live FnO Signal Dashboard", layout="wide")
st.title("Live FnO Trading Signal Dashboard")

# Dropdown for symbol and timeframe
symbol = st.selectbox("Select Instrument", ["NIFTY", "BANKNIFTY"])
timeframe = st.selectbox("Select Timeframe", ["5minute", "15minute"])

# Set date range for historical data
to_date = datetime.now()
from_date = to_date - timedelta(days=1)

# Get ATM option token
option_data = get_option_token(symbol)
if not option_data:
    st.error("Token Error: instrument not found")
    st.stop()

token = option_data['token']
option_symbol = option_data['trading_symbol']
exchange = option_data['exch_seg']

# Fetch historical data
with st.spinner("Loading historical data..."):
    df = get_historical_data(token, exchange, timeframe, from_date, to_date)
    if df is None or df.empty:
        st.error("Data error: No candle data received.")
        st.stop()

    df = calculate_indicators(df)
    signal = generate_signal(df)
    ltp = get_ltp(option_symbol, exchange)
    entry, tp, sl = calculate_tp_sl(df, signal, ltp)

# Display signal
st.markdown(f"### Signal: **{signal}**")
st.metric("LTP", value=ltp)
st.metric("Entry", value=entry)
st.metric("Target (TP)", value=tp)
st.metric("Stop Loss (SL)", value=sl)

# Plot chart
fig = go.Figure()
fig.add_trace(go.Candlestick(
    x=df['datetime'], open=df['open'], high=df['high'],
    low=df['low'], close=df['close'], name='Candles'))
fig.add_trace(go.Scatter(x=df['datetime'], y=df['EMA_5'], name='EMA 5', line=dict(color='blue')))
fig.add_trace(go.Scatter(x=df['datetime'], y=df['EMA_20'], name='EMA 20', line=dict(color='orange')))
fig.update_layout(title=f"{symbol} {option_symbol} - {timeframe} Chart", xaxis_title="Time", yaxis_title="Price")
st.plotly_chart(fig, use_container_width=True)

# Display recent data
display_cols = ["datetime", "open", "high", "low", "close", "EMA_5", "EMA_20", "Signal"]
st.dataframe(df[display_cols].tail(10))

# Auto-refresh
st_autorefresh = st.experimental_rerun
