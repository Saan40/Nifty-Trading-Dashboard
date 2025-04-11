import streamlit as st
import pandas as pd
import plotly.graph_objs as go
from datetime import datetime, timedelta
from angel_login import obj, instruments_df, get_instrument_token, get_ltp, get_historical_data
from utils import get_signal, calculate_tp_sl

st.set_page_config(page_title="FnO Signal Dashboard", layout="wide")
st.title("Live FnO Trading Signal Dashboard")

symbol = st.selectbox("Select Instrument", ["NIFTY", "BANKNIFTY"])
timeframe = st.selectbox("Select Timeframe", ["5minute", "15minute"])

# Get instrument token
token_info = get_instrument_token(symbol)
if not token_info:
    st.error("Token Error: Instrument token not found for the latest expiry")
    st.stop()

instrument_token = token_info['token']
exchange = token_info['exch_seg']

# Date range
to_date = datetime.now()
from_date = to_date - timedelta(days=1)

# Fetch historical data
data = get_historical_data(token=instrument_token, interval=timeframe, from_date=from_date, to_date=to_date, exchange=exchange)
if not data or 'data' not in data or not data['data']:
    st.error("Data error: No candle data received.")
    st.stop()

# Prepare DataFrame
df = pd.DataFrame(data['data'], columns=['datetime', 'open', 'high', 'low', 'close', 'volume'])
df['datetime'] = pd.to_datetime(df['datetime'])
df[['open', 'high', 'low', 'close', 'volume']] = df[['open', 'high', 'low', 'close', 'volume']].astype(float)
df = df.tail(50).copy()  # Keep last 50 candles

# Get signal and TP/SL
signal, entry, tp, sl = get_signal(df)
ltp = get_ltp(symbol)

# Show signal and chart
st.subheader(f"Signal: **{signal}**")
st.metric("LTP", value=ltp)
if signal in ["BUY", "SELL"]:
    st.write(f"**Entry**: {entry:.2f} | **Target (TP)**: {tp:.2f} | **Stop Loss (SL)**: {sl:.2f}")

# Plotting candlestick + signal + TP/SL
fig = go.Figure()
fig.add_trace(go.Candlestick(x=df['datetime'], open=df['open'], high=df['high'],
                             low=df['low'], close=df['close'], name='Candles'))

if signal == "BUY":
    fig.add_trace(go.Scatter(x=[df.iloc[-1]['datetime']], y=[entry], mode='markers+text', name='BUY',
                             marker=dict(color='green', size=12), text=['BUY'], textposition="top right"))
    fig.add_hline(y=tp, line_dash="dash", line_color="green", annotation_text="TP", annotation_position="top right")
    fig.add_hline(y=sl, line_dash="dash", line_color="red", annotation_text="SL", annotation_position="bottom right")
elif signal == "SELL":
    fig.add_trace(go.Scatter(x=[df.iloc[-1]['datetime']], y=[entry], mode='markers+text', name='SELL',
                             marker=dict(color='red', size=12), text=['SELL'], textposition="top right"))
    fig.add_hline(y=tp, line_dash="dash", line_color="red", annotation_text="TP", annotation_position="bottom right")
    fig.add_hline(y=sl, line_dash="dash", line_color="green", annotation_text="SL", annotation_position="top right")

fig.update_layout(title="Live Candlestick Chart", xaxis_title="Time", yaxis_title="Price",
                  xaxis_rangeslider_visible=False, template="plotly_dark")
st.plotly_chart(fig, use_container_width=True)

st.dataframe(df.tail(10))
