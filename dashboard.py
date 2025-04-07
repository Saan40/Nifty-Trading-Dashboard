# dashboard.py
import streamlit as st
import pandas as pd
from utils import calculate_indicators, identify_candlestick_patterns, generate_signal
from angel_login import get_instrument_token, get_historical_data, get_ltp, instruments_df

st.set_page_config(page_title="FnO Signal Dashboard", layout="wide")
st.title("Live FnO Trading Signal Dashboard")

instrument = st.selectbox("Select Instrument", ["NIFTY", "BANKNIFTY"])
timeframe = st.selectbox("Select Timeframe", ["5minute", "15minute"])

instrument_token = get_instrument_token(instruments_df, instrument)

with st.spinner("Fetching live data..."):
    df = get_historical_data(instrument_token, interval=timeframe)
    df = calculate_indicators(df)
    df = identify_candlestick_patterns(df)
    signal = generate_signal(df)
    ltp = get_ltp(instrument_token)

st.subheader(f"Signal: **{signal}**")
st.metric("LTP", value=ltp)
st.dataframe(df.tail(10))
