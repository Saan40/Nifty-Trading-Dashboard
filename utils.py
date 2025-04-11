import pandas as pd
import numpy as np

def calculate_indicators(df):
    df["EMA_5"] = df["close"].ewm(span=5).mean()
    df["EMA_20"] = df["close"].ewm(span=20).mean()
    df["MACD"] = df["close"].ewm(span=12).mean() - df["close"].ewm(span=26).mean()
    df["MACD_signal"] = df["MACD"].ewm(span=9).mean()
    df["ATR"] = df["high"].sub(df["low"]).rolling(window=14, min_periods=1).mean()
    return df

def generate_signal(df):
    latest = df.iloc[-1]
    if latest["EMA_5"] > latest["EMA_20"] and latest["MACD"] > latest["MACD_signal"]:
        return "CALL"
    elif latest["EMA_5"] < latest["EMA_20"] and latest["MACD"] < latest["MACD_signal"]:
        return "PUT"
    return "HOLD"

def calculate_tp_sl(ltp, atr):
    tp = round(ltp + atr * 1.5, 2)
    sl = round(ltp - atr * 1.0, 2)
    return tp, sl
