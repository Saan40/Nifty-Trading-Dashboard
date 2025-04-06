import streamlit as st
import pandas as pd
import datetime as dt
from angel_login import angel_login
from SmartApi.smartConnect import SmartConnect
import plotly.graph_objects as go
import requests

# Signal configuration
MAX_RISK = 0.10  # 10%
BUDGET = 5000

# Define FnO tokens for current month (example)
INSTRUMENTS = {
    "NIFTY FUT": "26009",
    "BANKNIFTY FUT": "26037"
}

# GNews API setup
GNEWS_API_KEY = "2fd0fba74fc73144767e14f57b90f19c"
GNEWS_URL = f"https://gnews.io/api/v4/top-headlines?category=business&lang=en&country=in&token={GNEWS_API_KEY}"

# Setup
st.set_page_config(layout="wide")
st.title("Nifty & BankNifty FnO Signal Dashboard (Angel One + News + Indicators)")

symbol_choice = st.selectbox("Select Instrument", list(INSTRUMENTS.keys()))
selected_token = INSTRUMENTS[symbol_choice]

# Login to Angel One
try:
    access_token, feed_token = angel_login()
    st.success("Login successful!")
except Exception as e:
    st.error("Login failed: " + str(e))
    st.stop()

# Angel One SmartConnect object
obj = SmartConnect(api_key="6z7qhWH4")
obj.access_token = access_token
obj.feed_token = feed_token

# Get Historical Data
def get_data(symbol_token):
    params = {
        "exchange": "NFO",
        "symboltoken": symbol_token,
        "interval": "FIFTEEN_MINUTE",
        "fromdate": (dt.datetime.now() - dt.timedelta(days=7)).strftime('%Y-%m-%d %H:%M'),
        "todate": dt.datetime.now().strftime('%Y-%m-%d %H:%M')
    }
    data = obj.getCandleData(params)
    df = pd.DataFrame(data['data'], columns=["Time", "Open", "High", "Low", "Close", "Volume"])
    df["Time"] = pd.to_datetime(df["Time"])
    df.set_index("Time", inplace=True)
    df = df.astype(float)
    return df

# Get latest news sentiment
def get_news_sentiment():
    try:
        news = requests.get(GNEWS_URL).json()
        headlines = [article['title'] for article in news['articles']]
        sentiment = "Neutral"
        if any(x in str(headlines).lower() for x in ["inflation", "cpi", "pm modi", "finance minister", "recession", "rate hike"]):
            sentiment = "Bearish"
        elif any(x in str(headlines).lower() for x in ["growth", "bullish", "recovery", "rally"]):
            sentiment = "Bullish"
        return sentiment, headlines
    except:
        return "Neutral", []

# Generate signal
def generate_signal(df, sentiment):
    latest = df.iloc[-1]
    body = abs(latest["Close"] - latest["Open"])
    atr = df["High"].rolling(window=14).max() - df["Low"].rolling(window=14).min()
    latest_atr = atr.iloc[-1]

    direction = "CALL" if latest["Close"] > latest["Open"] else "PUT"

    if body > 0.8 * latest_atr:
        if sentiment == "Bullish" and direction == "CALL":
            return "CALL"
        elif sentiment == "Bearish" and direction == "PUT":
            return "PUT"
    return "NO SIGNAL"

# Main
with st.spinner("Fetching data..."):
    df = get_data(selected_token)
    sentiment, headlines = get_news_sentiment()
    signal = generate_signal(df, sentiment)

# Display
st.subheader("Signal")
st.metric("Trade Signal", signal)
st.metric("News Sentiment", sentiment)

st.subheader("Latest News Headlines")
for headline in headlines[:5]:
    st.markdown(f"- {headline}")

# Chart
fig = go.Figure(data=[go.Candlestick(
    x=df.index,
    open=df['Open'],
    high=df['High'],
    low=df['Low'],
    close=df['Close']
)])
fig.update_layout(title=f"{symbol_choice} Candlestick", xaxis_rangeslider_visible=False)
st.plotly_chart(fig, use_container_width=True)
