import pandas as pd
import talib

def calculate_indicators(df):
    df["EMA_20"] = talib.EMA(df["close"], timeperiod=20)
    df["EMA_50"] = talib.EMA(df["close"], timeperiod=50)
    df["RSI"] = talib.RSI(df["close"], timeperiod=14)
    macd, macdsignal, _ = talib.MACD(df["close"], fastperiod=12, slowperiod=26, signalperiod=9)
    df["MACD"] = macd
    df["MACD_signal"] = macdsignal
    return df

def identify_candlestick_patterns(df):
    df["pattern"] = None
    df["pattern"] = talib.CDLHAMMER(df["open"], df["high"], df["low"], df["close"])
    df["pattern"] = df["pattern"].apply(lambda x: "Hammer" if x > 0 else None)
    return df

def generate_signal(df):
    latest = df.iloc[-1]
    if latest["RSI"] < 30 and latest["MACD"] > latest["MACD_signal"] and latest["pattern"] == "Hammer":
        return "CALL"
    elif latest["RSI"] > 70 and latest["MACD"] < latest["MACD_signal"]:
        return "PUT"
    else:
        return "HOLD"
