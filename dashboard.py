import streamlit as st
import pandas as pd
import plotly.graph_objs as go
import time
from utils import get_signal, calculate_tp_sl, fetch_historical_data
from angel_login import api, instruments_df, get_instrument_token

st.set_page_config(layout="wide")

st.title("FnO Signal Dashboard - NIFTY/BANKNIFTY")

# Sidebar selections
symbol = st.sidebar.selectbox("Select Symbol", ["NIFTY", "BANKNIFTY"])
timeframe = st.sidebar.selectbox("Timeframe", ["5minute", "15minute"])

# Token lookup
token_data = get_instrument_token(symbol, instruments_df)
if not token_data:
    st.error("Instrument token not found. Check instruments.csv or symbol format.")
    st.stop()

# Get historical data
data = fetch_historical_data(api, token_data['token'], token_data['exch_seg'], timeframe)
if data is None or data.empty:
    st.error("No historical data returned.")
    st.stop()

# Get signals
data = get_signal(data)

# Calculate TP/SL for signals
data = calculate_tp_sl(data)

# Filter to last 50 candles
data = data.tail(50)

# Plotly chart setup
fig = go.Figure()

# Candlestick
fig.add_trace(go.Candlestick(
    x=data['datetime'],
    open=data['open'],
    high=data['high'],
    low=data['low'],
    close=data['close'],
    name='Price'))

# Plot signals
for i, row in data.iterrows():
    if row['signal'] == 'BUY':
        fig.add_trace(go.Scatter(
            x=[row['datetime']], y=[row['close']],
            mode='markers+text',
            marker=dict(color='green', size=10, symbol='triangle-up'),
            text=["BUY"], textposition="bottom center",
            name='Buy'))

        # TP & SL lines
        fig.add_trace(go.Scatter(x=[row['datetime']], y=[row['tp']], mode='markers+text', marker=dict(color='blue'), text=["TP"], name='TP'))
        fig.add_trace(go.Scatter(x=[row['datetime']], y=[row['sl']], mode='markers+text', marker=dict(color='red'), text=["SL"], name='SL'))

    elif row['signal'] == 'SELL':
        fig.add_trace(go.Scatter(
            x=[row['datetime']], y=[row['close']],
            mode='markers+text',
            marker=dict(color='red', size=10, symbol='triangle-down'),
            text=["SELL"], textposition="top center",
            name='Sell'))

        # TP & SL lines
        fig.add_trace(go.Scatter(x=[row['datetime']], y=[row['tp']], mode='markers+text', marker=dict(color='blue'), text=["TP"], name='TP'))
        fig.add_trace(go.Scatter(x=[row['datetime']], y=[row['sl']], mode='markers+text', marker=dict(color='red'), text=["SL"], name='SL'))

fig.update_layout(
    xaxis_rangeslider_visible=False,
    title=f"{symbol} {timeframe} Chart with Signals",
    yaxis_title="Price",
    xaxis_title="Time",
    height=700
)

st.plotly_chart(fig, use_container_width=True)

# Auto-refresh info
st.info("Auto-refreshing every 60 seconds...")
time.sleep(60)
st.experimental_rerun()
