import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from angel_login import get_instrument_token, get_historical_data, get_ltp, instruments_df

st.set_page_config(page_title="FnO Signal Dashboard", layout="wide")
st.title("Live FnO Trading Signal Dashboard")

# Sidebar options
symbol = st.selectbox("Select Instrument", ["NIFTY", "BANKNIFTY"])
timeframe = st.selectbox("Select Timeframe", ["ONE_MINUTE", "FIVE_MINUTE", "FIFTEEN_MINUTE"])

# Token lookup
instrument_token = get_instrument_token(instruments_df, symbol, exchange="NFO")
if not instrument_token:
    st.error("Instrument token not found.")
    st.stop()

# Date range for historical data
from_date = datetime.now() - timedelta(days=1)
to_date = datetime.now()

# Fetch historical data
st.subheader(f"Showing Signals for {symbol} ({timeframe})")
with st.spinner("Fetching historical data..."):
    df = get_historical_data(instrument_token, timeframe, from_date, to_date, exchange="NFO")

    if df is None or not isinstance(df, dict) or 'data' not in df:
        st.error("No data received or response invalid.")
        st.stop()

    df = pd.DataFrame(df['data'], columns=['datetime', 'open', 'high', 'low', 'close', 'volume'])
    df['datetime'] = pd.to_datetime(df['datetime'])
    df[['open', 'high', 'low', 'close', 'volume']] = df[['open', 'high', 'low', 'close', 'volume']].astype(float)

# Add basic indicator logic (EMA-based)
df['EMA_5'] = df['close'].ewm(span=5).mean()
df['EMA_20'] = df['close'].ewm(span=20).mean()
df['Signal'] = df.apply(lambda row: "BUY" if row['EMA_5'] > row['EMA_20'] else "SELL", axis=1)

# Get latest values
latest_signal = df.iloc[-1]['Signal']
latest_close = df.iloc[-1]['close']
ltp = get_ltp(symbol, exchange="NFO")

# Display
st.metric("Live LTP", value=ltp)
st.subheader(f"Latest Signal: {latest_signal}")
st.line_chart(df.set_index("datetime")[['close', 'EMA_5', 'EMA_20']])
st.dataframe(df.tail(10))
