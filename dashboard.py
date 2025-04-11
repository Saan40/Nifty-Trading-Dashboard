import streamlit as st
import pandas as pd
import plotly.graph_objs as go
from datetime import datetime, timedelta
from angel_login import (
    smart_api,
    instruments_df,
    get_option_token,
    get_ltp,
    get_historical_data
)
from utils import calculate_indicators, generate_signal, calculate_tp_sl

st.set_page_config(page_title="FnO Signal Dashboard", layout="wide")
st.title("Live FnO Trading Signal Dashboard")

symbol = st.selectbox("Select Instrument", ["NIFTY", "BANKNIFTY"])
timeframe = st.selectbox("Select Timeframe", ["5minute", "15minute"])

to_date = datetime.now()
from_date = to_date - timedelta(days=1)

ltp = get_ltp(symbol, exch_seg="NFO")
if not ltp:
    st.error("LTP fetch failed.")
    st.stop()

strike = round(ltp / 50) * 50
expiry = instruments_df[instruments_df['name'] == symbol]['expiry'].min()

call_option = get_option_token(symbol, strike, "CE", expiry)
put_option = get_option_token(symbol, strike, "PE", expiry)

if not call_option or not put_option:
    st.error("Option token not found.")
    st.stop()

option_type = st.selectbox("Option Type", ["CALL", "PUT"])
option_info = call_option if option_type == "CALL" else put_option

df = get_historical_data(
    token=option_info["token"],
    interval=timeframe,
    from_date=from_date,
    to_date=to_date,
    exchange=option_info["exch_seg"]
)

if df is None or df.empty:
    st.error("Data error: No candle data received.")
    st.stop()

df = calculate_indicators(df)
signal = generate_signal(df)
tp, sl = calculate_tp_sl(ltp, df["ATR"].iloc[-1])

fig = go.Figure()
fig.add_trace(go.Candlestick(
    x=df['datetime'],
    open=df['open'],
    high=df['high'],
    low=df['low'],
    close=df['close'],
    name='Candles'
))
fig.add_trace(go.Scatter(x=df['datetime'], y=df['EMA_9'], line=dict(color='blue'), name='EMA 9'))
fig.add_trace(go.Scatter(x=df['datetime'], y=df['EMA_21'], line=dict(color='orange'), name='EMA 21'))
fig.update_layout(title=f"{symbol} {option_type} | Signal: {signal}", xaxis_rangeslider_visible=False)

st.subheader(f"Signal: **{signal}**")
st.metric("LTP", value=ltp)
st.metric("Strike", value=strike)
st.metric("TP", value=tp)
st.metric("SL", value=sl)

st.plotly_chart(fig, use_container_width=True)
st.dataframe(df.tail(10)[["datetime", "open", "high", "low", "close", "EMA_9", "EMA_21", "Signal"]])
