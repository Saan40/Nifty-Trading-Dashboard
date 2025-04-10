import pandas as pd

# Signal logic using EMA crossover
def get_signal(df):
    df['EMA_5'] = df['close'].ewm(span=5).mean()
    df['EMA_20'] = df['close'].ewm(span=20).mean()

    if df['EMA_5'].iloc[-1] > df['EMA_20'].iloc[-1] and df['EMA_5'].iloc[-2] <= df['EMA_20'].iloc[-2]:
        return "BUY"
    elif df['EMA_5'].iloc[-1] < df['EMA_20'].iloc[-1] and df['EMA_5'].iloc[-2] >= df['EMA_20'].iloc[-2]:
        return "SELL"
    else:
        return "HOLD"

# TP/SL calculator based on recent candle size or ATR logic
def calculate_tp_sl(df, signal, risk_ratio=1.5):
    if df.empty or signal not in ["BUY", "SELL"]:
        return None, None, None

    entry = df['close'].iloc[-1]
    candle_range = df['high'].iloc[-1] - df['low'].iloc[-1]

    if signal == "BUY":
        sl = entry - candle_range
        tp = entry + candle_range * risk_ratio
    elif signal == "SELL":
        sl = entry + candle_range
        tp = entry - candle_range * risk_ratio
    else:
        tp, sl = None, None

    return round(entry, 2), round(tp, 2), round(sl, 2)

# Wrapper to convert raw candle data into DataFrame
def fetch_historical_data(api, token, interval, from_date, to_date, exchange="NFO"):
    params = {
        "exchange": exchange,
        "symboltoken": str(token),
        "interval": interval,
        "fromdate": from_date.strftime('%Y-%m-%d %H:%M'),
        "todate": to_date.strftime('%Y-%m-%d %H:%M')
    }
    try:
        response = api.getCandleData(params)
        candles = response.get("data", [])
        if not candles:
            return pd.DataFrame()
        df = pd.DataFrame(candles, columns=["datetime", "open", "high", "low", "close", "volume"])
        df["datetime"] = pd.to_datetime(df["datetime"])
        return df
    except Exception as e:
        print(f"Error fetching candle data: {e}")
        return pd.DataFrame()
