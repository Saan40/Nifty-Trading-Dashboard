import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.graph_objs as go
from angel_login import get_instrument_token, get_historical_data, get_ltp

st.set_page_config(page_title="FnO Dashboard", layout="wide")
st.title("Live FnO Trading Signal Dashboard")

# Sidebar selection
symbol = st.selectbox("Select Symbol", ["NIFTY", "BANKNIFTY"])
timeframe = st.selectbox("Select Timeframe", ["5minute", "15minute"])

# Calculate time range
to_date = datetime.now()
from_date = to_date - timedelta(days=1)

# Fetch token
try:
    instrument_token = get_instrument_token(symbol)
except Exception as e:
    st.error(f"Token Error: {e}")
    st.stop()

# Fetch candle data
with st.spinner("Loading chart data..."):
    try:
        df = get_historical_data(instrument_token, timeframe, from_date, to_date)
    except Exception as e:
        st.error(f"Data error: {e}")
        st.stop()

# Simple indicators
df['EMA5'] = df['close'].ewm(span=5).mean()
df['EMA20'] = df['close'].ewm(span=20).mean()
df['Signal'] = df.apply(lambda row: "BUY" if row['EMA5'] > row['EMA20'] else "SELL", axis=1)
latest_signal = df.iloc[-1]['Signal']
entry = df.iloc[-1]['close']
tp = round(entry * 1.01, 2)
sl = round(entry * 0.99, 2)

# Plot chart
fig = go.Figure()
fig.add_trace(go.Candlestick(x=df['datetime'], open=df['open'], high=df['high'], low=df['low'], close=df['close'], name='Candle'))
fig.add_trace(go.Scatter(x=df['datetime'], y=df['EMA5'], line=dict(color='blue'), name='EMA5'))
fig.add_trace(go.Scatter(x=df['datetime'], y=df['EMA20'], line=dict(color='orange'), name='EMA20'))
fig.update_layout(title=f"{symbol} | {timeframe} | Signal: {latest_signal}", xaxis_rangeslider_visible=False)

# Display chart and signal
st.plotly_chart(fig, use_container_width=True)
st.subheader(f"Signal: **{latest_signal}**")
st.metric("Entry Price", entry)
st.metric("Target (TP)", tp)
st.metric("Stop Loss (SL)", sl)
st.dataframe(df.tail(10)[['datetime', 'open', 'high', 'low', 'close', 'EMA5', 'EMA20', 'Signal']])
