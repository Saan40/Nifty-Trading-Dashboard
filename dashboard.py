import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from angel_login import get_instrument_token, get_historical_data, get_ltp, instruments_df

st.set_page_config(page_title="FnO Signal Dashboard", layout="wide")
st.title("Live FnO Trading Signal Dashboard")

# Sidebar selections
symbol = st.selectbox("Select Instrument", ["NIFTY", "BANKNIFTY"])
timeframe = st.selectbox("Select Timeframe", ["ONE_MINUTE", "FIVE_MINUTE", "FIFTEEN_MINUTE", "ONE_HOUR"])

# Get token
instrument_token = get_instrument_token(instruments_df, symbol)
if not instrument_token:
    st.error("Instrument token not found.")
    st.stop()

# Get historical data
from_date = datetime.now() - timedelta(days=1)
to_date = datetime.now()
df = get_historical_data(instrument_token, timeframe, from_date, to_date)

if df is None or df.empty:
    st.error("Failed to retrieve historical data.")
    st.stop()

# Calculate simple indicators
df['EMA_5'] = df['close'].ewm(span=5).mean()
df['EMA_20'] = df['close'].ewm(span=20).mean()
df['Signal'] = df.apply(
    lambda row: "BUY" if row['EMA_5'] > row['EMA_20'] else "SELL", axis=1
)

# Display outputs
ltp = get_ltp(symbol)
latest_signal = df.iloc[-1]['Signal']

st.subheader(f"Latest Signal: {latest_signal}")
st.metric("LTP", value=ltp)
st.line_chart(df.set_index("datetime")[['close', 'EMA_5', 'EMA_20']])
st.dataframe(df.tail(10)[['datetime', 'open', 'high', 'low', 'close', 'EMA_5', 'EMA_20', 'Signal']])
