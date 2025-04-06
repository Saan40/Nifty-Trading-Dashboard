import pandas as pd
import ta

def calculate_indicators(df):
    df['rsi'] = ta.momentum.RSIIndicator(df['close']).rsi()
    df['macd'] = ta.trend.MACD(df['close']).macd_diff()
    df['atr'] = ta.volatility.AverageTrueRange(df['high'], df['low'], df['close']).average_true_range()
    return df

def identify_candlestick_patterns(df):
    patterns = []

    for i in range(2, len(df)):
        prev = df.iloc[i - 1]
        curr = df.iloc[i]
        if (
            prev['close'] < prev['open'] and
            curr['close'] > curr['open'] and
            curr['close'] > prev['open'] and
            curr['open'] < prev['close']
        ):
            patterns.append('bullish_engulfing')
        elif (
            prev['close'] > prev['open'] and
            curr['close'] < curr['open'] and
            curr['close'] < prev['open'] and
            curr['open'] > prev['close']
        ):
            patterns.append('bearish_engulfing')
        else:
            patterns.append('')
    patterns = [''] * 2 + patterns
    df['pattern'] = patterns
    return df

def generate_signal(df):
    last = df.iloc[-1]
    signal = ''
    if last['pattern'] == 'bullish_engulfing' and last['rsi'] < 70 and last['macd'] > 0:
        signal = 'CALL'
    elif last['pattern'] == 'bearish_engulfing' and last['rsi'] > 30 and last['macd'] < 0:
        signal = 'PUT'
    return signal
