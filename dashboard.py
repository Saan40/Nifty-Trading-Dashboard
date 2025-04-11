import os
import streamlit as st
import pandas as pd
import datetime as dt
from angel_login import (
    smart_api, 
    instruments_df, 
    get_instrument_token, 
    get_option_token,
    get_historical_candles
)

# --- SETTINGS ---
st.set_page_config(page_title="FnO Signal Dashboard", layout="wide")
st.title("NIFTY & BANKNIFTY FnO Signal Dashboard")

# --- USER INPUT ---
symbol = st.selectbox("Select Symbol", ["NIFTY", "BANKNIFTY"])
timeframe = st.selectbox("Select Timeframe", ["5minute", "15minute"])
exchange = "NFO"

# --- TOKEN LOOKUP FOR FUTURES (Current Week) ---
today = dt.date.today()
weekly_expiries = instruments_df[
    (instruments_df["trading_symbol"].str.startswith(symbol))
    & (instruments_df["exch_seg"] == exchange)
    & (instruments_df["trading_symbol"].str.contains("FUT"))
]

# Filter for current/nearest expiry
weekly_expiries["expiry"] = pd.to_datetime(weekly_expiries["trading_symbol"].str.extract(r'(\d{2}[A-Z]{3}\d{2})')[0], format="%d%b%y", errors="coerce")
weekly_expiries = weekly_expiries.dropna(subset=["expiry"])
weekly_expiries = weekly_expiries[weekly_expiries["expiry"] >= pd.Timestamp(today)]
weekly_expiries = weekly_expiries.sort_values("expiry")
if weekly_expiries.empty:
    st.error(f"No {symbol} future instruments found for current expiry.")
    st.stop()

future_token = weekly_expiries.iloc[0]["token"]
future_symbol = weekly_expiries.iloc[0]["trading_symbol"]

st.write(f"Selected: `{future_symbol}` | Token: `{future_token}`")

# --- HISTORICAL DATA ---
to_date = dt.datetime.now()
from_date = to_date - dt.timedelta(days=5)

try:
    candles = get_historical_candles(future_token, from_date, to_date, timeframe)
    df = pd.DataFrame(candles, columns=["timestamp", "open", "high", "low", "close", "volume"])
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df.set_index("timestamp", inplace=True)
except Exception as e:
    st.error(f"Failed to fetch historical data: {e}")
    st.stop()

# --- SIMPLE SIGNAL LOGIC ---
def generate_signal(df):
    latest = df.iloc[-1]
    previous = df.iloc[-2]

    signal = "HOLD"
    entry = df.index[-1]
    sl = tp = None

    if latest["close"] > latest["open"] and previous["close"] < previous["open"]:
        signal = "BUY"
    elif latest["close"] < latest["open"] and previous["close"] > previous["open"]:
        signal = "SELL"

    atr = df["high"].rolling(3).max() - df["low"].rolling(3).min()
    atr_val = atr.iloc[-1]
    
    if signal == "BUY":
        sl = latest["low"]
        tp = latest["close"] + atr_val
    elif signal == "SELL":
        sl = latest["high"]
        tp = latest["close"] - atr_val

    return {
        "Signal": signal,
        "Entry Time": entry,
        "Entry Price": latest["close"],
        "TP": round(tp, 2) if tp else None,
        "SL": round(sl, 2) if sl else None
    }

signal_result = generate_signal(df)

# --- DISPLAY ---
st.subheader("Latest Signal")
st.write(signal_result)

# --- CHART ---
import plotly.graph_objects as go

fig = go.Figure()
fig.add_trace(go.Candlestick(
    x=df.index,
    open=df["open"],
    high=df["high"],
    low=df["low"],
    close=df["close"],
    name="Candles"
))

entry_time = signal_result["Entry Time"]
entry_price = signal_result["Entry Price"]

if signal_result["Signal"] in ["BUY", "SELL"]:
    fig.add_trace(go.Scatter(
        x=[entry_time], 
        y=[entry_price],
        mode="markers+text",
        name=signal_result["Signal"],
        marker=dict(color="green" if signal_result["Signal"]=="BUY" else "red", size=10),
        text=signal_result["Signal"],
        textposition="top center"
    ))
    fig.add_hline(y=signal_result["TP"], line=dict(color="blue", dash="dash"), annotation_text="TP")
    fig.add_hline(y=signal_result["SL"], line=dict(color="orange", dash="dot"), annotation_text="SL")

st.plotly_chart(fig, use_container_width=True)
