# utils.py (No TA-Lib version)
import pandas as pd
import numpy as np

def calculate_indicators(df):
    df['EMA_9'] = df['close'].ewm(span=9, adjust=False).mean()
    df['EMA_21'] = df['close'].ewm(span=21, adjust=False).mean()
    df['RSI'] = compute_rsi(df['close'], 14)
    df['MACD'], df['MACD_signal'] = compute_macd(df['close'])
    df['ATR'] = compute_atr(df, period=14)
    return df

def compute_rsi(series, period):
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def compute_macd(series):
    exp1 = series.ewm(span=12, adjust=False).mean()
    exp2 = series.ewm(span=26, adjust=False).mean()
    macd = exp1 - exp2
    signal = macd.ewm(span=9, adjust=False).mean()
    return macd, signal

def compute_atr(df, period=14):
    df['H-L'] = abs(df['high'] - df['low'])
    df['H-PC'] = abs(df['high'] - df['close'].shift(1))
    df['L-PC'] = abs(df['low'] - df['close'].shift(1))
    tr = df[['H-L', 'H-PC', 'L-PC']].max(axis=1)
    atr = tr.rolling(window=period).mean()
    return atr

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

def generate_signal(df):
    if df.iloc[-1]['bullish_engulfing'] and df.iloc[-1]['MACD'] > df.iloc[-1]['MACD_signal']:
        return "CALL"
    elif df.iloc[-1]['bearish_engulfing'] and df.iloc[-1]['MACD'] < df.iloc[-1]['MACD_signal']:
        return "PUT"
    else:
        return "HOLD"
