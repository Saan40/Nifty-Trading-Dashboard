import streamlit as st
from datetime import datetime, timedelta
from angel_login import get_weekly_token, get_historical_data, get_ltp

st.set_page_config(page_title="FnO Signal Dashboard", layout="wide")
st.title("Live FnO Trading Signal Dashboard")

symbol = st.selectbox("Select Instrument", ["NIFTY", "BANKNIFTY"])
timeframe = st.selectbox("Select Timeframe", ["ONE_MINUTE", "FIVE_MINUTE", "FIFTEEN_MINUTE"])

# Get instrument token
try:
    instrument_token = get_weekly_token(symbol)
except Exception as e:
    st.error(f"Token Error: {e}")
    st.stop()

# Set date range for candles
from_date = datetime.now() - timedelta(days=1)
to_date = datetime.now()

# Fetch data
try:
    df = get_historical_data(instrument_token, interval=timeframe, from_date=from_date, to_date=to_date)
except Exception as e:
    st.error(f"Data error: {e}")
    st.stop()

# Simple indicators
df['EMA_5'] = df['close'].ewm(span=5).mean()
df['EMA_20'] = df['close'].ewm(span=20).mean()
df['Signal'] = df.apply(lambda row: "BUY" if row['EMA_5'] > row['EMA_20'] else "SELL", axis=1)

latest_signal = df.iloc[-1]["Signal"]
ltp = get_ltp(symbol)

# Show output
st.subheader(f"Signal: **{latest_signal}**")
st.metric("LTP", value=ltp)
st.line_chart(df.set_index("datetime")[["close", "EMA_5", "EMA_20"]])
st.dataframe(df.tail(10)[["datetime", "open", "high", "low", "close", "EMA_5", "EMA_20", "Signal"]])
