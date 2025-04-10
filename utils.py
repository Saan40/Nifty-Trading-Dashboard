import pandas as pd
import numpy as np

# --- Indicators ---
def calculate_indicators(df):
    df['EMA_5'] = df['close'].ewm(span=5).mean()
    df['EMA_20'] = df['close'].ewm(span=20).mean()
    df['ATR'] = compute_atr(df, period=14)
    return df

def compute_atr(df, period=14):
    df['H-L'] = abs(df['high'] - df['low'])
    df['H-PC'] = abs(df['high'] - df['close'].shift(1))
    df['L-PC'] = abs(df['low'] - df['close'].shift(1))
    tr = df[['H-L', 'H-PC', 'L-PC']].max(axis=1)
    atr = tr.rolling(window=period).mean()
    return atr

# --- Candlestick Patterns ---
def identify_candlestick_patterns(df):
    df['bullish_engulfing'] = (
        (df['close'].shift(1) < df['open'].shift(1)) &
        (df['close'] > df['open']) &
        (df['open'] < df['close'].shift(1)) &
        (df['close'] > df['open'].shift(1))
    )
    df['bearish_engulfing'] = (
        (df['close'].shift(1) > df['open'].shift(1)) &
        (df['close'] < df['open']) &
        (df['open'] > df['close'].shift(1)) &
        (df['close'] < df['open'].shift(1))
    )
    return df

# --- Signal Logic ---
def get_signal(df):
    latest = df.iloc[-1]
    if latest['EMA_5'] > latest['EMA_20']:
        return "BUY"
    elif latest['EMA_5'] < latest['EMA_20']:
        return "SELL"
    else:
        return "HOLD"

# --- TP/SL Calculation ---
def calculate_tp_sl(price, signal, atr):
    if signal == "BUY":
        entry = price
        sl = price - (atr * 1.5)
        tp = price + (atr * 2)
    elif signal == "SELL":
        entry = price
        sl = price + (atr * 1.5)
        tp = price - (atr * 2)
    else:
        return None, None, None
    return round(entry, 2), round(tp, 2), round(sl, 2)
