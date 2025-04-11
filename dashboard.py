# dashboard.py
import streamlit as st
import pandas as pd
import plotly.graph_objs as go
from datetime import datetime, timedelta
from angel_login import smart_api, instruments_df, get_instrument_token, get_option_token, get_ltp, get_historical_data

st.set_page_config(page_title="FnO Signal Dashboard", layout="wide")
st.title("Live FnO Trading Signal Dashboard")

symbol = st.selectbox("Select Instrument", ["NIFTY", "BANKNIFTY"])
timeframe = st.selectbox("Select Timeframe", ["5minute", "15minute"])

# Get instrument token (ATM strike option auto selection)
try:
    spot_ltp = get_ltp(symbol)
    spot_price = round(int(spot_ltp), -2)  # round to nearest 100
    token_row = get_instrument_token(symbol)
    expiry = token_row['expiry']
    ce_token = get_option_token(symbol, spot_price, 'CE', expiry)
    pe_token = get_option_token(symbol, spot_price, 'PE', expiry)
except Exception as e:
    st.error(f"Token Error: {e}")
    st.stop()

# Fetch historical data
from_date = datetime.now() - timedelta(days=1)
to_date = datetime.now()

try:
    ce_df = get_historical_data(ce_token, timeframe, from_date, to_date)
    pe_df = get_historical_data(pe_token, timeframe, from_date, to_date)
except Exception as e:
    st.error(f"Data error: {e}")
    st.stop()

# Signal logic (simple EMA-based example)
ce_df['EMA_5'] = ce_df['close'].ewm(span=5).mean()
ce_df['EMA_20'] = ce_df['close'].ewm(span=20).mean()
ce_df['Signal'] = ce_df.apply(lambda row: 'BUY' if row['EMA_5'] > row['EMA_20'] else 'SELL', axis=1)

signal = ce_df.iloc[-1]['Signal']
entry = ce_df.iloc[-1]['close']
tp = round(entry * 1.01, 2)
sl = round(entry * 0.99, 2)

# Display
st.subheader(f"**{symbol}** - Signal: {signal}")
st.metric("Entry", value=entry)
st.metric("Target (TP)", value=tp)
st.metric("Stop Loss (SL)", value=sl)

# Chart
fig = go.Figure()
fig.add_trace(go.Candlestick(x=ce_df['datetime'],
                open=ce_df['open'], high=ce_df['high'],
                low=ce_df['low'], close=ce_df['close'], name='CE Candle'))
fig.add_trace(go.Scatter(x=ce_df['datetime'], y=ce_df['EMA_5'], name='EMA 5', line=dict(color='blue')))
fig.add_trace(go.Scatter(x=ce_df['datetime'], y=ce_df['EMA_20'], name='EMA 20', line=dict(color='orange')))

fig.update_layout(title="ATM CE Candlestick Chart", xaxis_rangeslider_visible=False, height=500)
st.plotly_chart(fig, use_container_width=True)

st.dataframe(ce_df.tail(10)[["datetime", "open", "high", "low", "close", "EMA_5", "EMA_20", "Signal"]])
