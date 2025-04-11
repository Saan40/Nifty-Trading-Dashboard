import pandas as pd
import numpy as np

# Calculate EMA, MACD, RSI, and ATR without TA-Lib
def calculate_indicators(df):
    df['EMA_9'] = df['close'].ewm(span=9, adjust=False).mean()
    df['EMA_21'] = df['close'].ewm(span=21, adjust=False).mean()

    df['MACD'] = df['close'].ewm(span=12, adjust=False).mean() - df['close'].ewm(span=26, adjust=False).mean()
    df['MACD_signal'] = df['MACD'].ewm(span=9, adjust=False).mean()

    delta = df['close'].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=14).mean()
    avg_loss = loss.rolling(window=14).mean()
    rs = avg_gain / avg_loss
    df['RSI'] = 100 - (100 / (1 + rs))

    df['H-L'] = abs(df['high'] - df['low'])
    df['H-PC'] = abs(df['high'] - df['close'].shift(1))
    df['L-PC'] = abs(df['low'] - df['close'].shift(1))
    tr = df[['H-L', 'H-PC', 'L-PC']].max(axis=1)
    df['ATR'] = tr.rolling(window=14).mean()

    return df

# Signal logic: simple candlestick + MACD combo
def generate_signal(df):
    if len(df) < 2:
        return "WAIT"
    latest = df.iloc[-1]
    prev = df.iloc[-2]

    bullish = (
        prev['close'] < prev['open'] and
        latest['close'] > latest['open'] and
        latest['close'] > prev['open'] and
        latest['open'] < prev['close'] and
        latest['MACD'] > latest['MACD_signal']
    )

    bearish = (
        prev['close'] > prev['open'] and
        latest['close'] < latest['open'] and
        latest['close'] < prev['open'] and
        latest['open'] > prev['close'] and
        latest['MACD'] < latest['MACD_signal']
    )

    if bullish:
        return "CALL"
    elif bearish:
        return "PUT"
    else:
        return "HOLD"

# Take Profit / Stop Loss calculation based on ATR or candle size
def calculate_tp_sl(df, ltp, direction, risk_pct=0.1):
    atr = df.iloc[-1]['ATR']
    body_size = abs(df.iloc[-1]['close'] - df.iloc[-1]['open'])
    buffer = max(atr, body_size)

    risk_amount = ltp * risk_pct

    if direction == "CALL":
        sl = ltp - buffer
        tp = ltp + (risk_amount * 2)
    elif direction == "PUT":
        sl = ltp + buffer
        tp = ltp - (risk_amount * 2)
    else:
        sl, tp = None, None

    return round(tp, 2), round(sl, 2)
