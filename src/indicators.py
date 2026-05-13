import pandas as pd
import numpy as np

def calculate_atr(df, period=14):
    df = df.copy()
    df['tr0'] = abs(df['high'] - df['low'])
    df['tr1'] = abs(df['high'] - df['close'].shift())
    df['tr2'] = abs(df['low'] - df['close'].shift())
    df['tr'] = df[['tr0', 'tr1', 'tr2']].max(axis=1)
    df['atr'] = df['tr'].rolling(period).mean()
    return df['atr']

def calculate_bb(df, period=20, std=2.0):
    df = df.copy()
    df['ma'] = df['close'].rolling(period).mean()
    df['std'] = df['close'].rolling(period).std()
    df['upper'] = df['ma'] + std * df['std']
    df['lower'] = df['ma'] - std * df['std']
    return df[['ma', 'upper', 'lower']]

def calculate_rsi(df, period=14):
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_adx(df, period=14):
    df = df.copy()
    df['up'] = df['high'].diff()
    df['down'] = -df['low'].diff()
    df['up'] = df['up'].where(df['up'] > 0, 0)
    df['down'] = df['down'].where(df['down'] > 0, 0)
    df['tr'] = df[['high', 'low', 'close']].apply(
        lambda row: max(row['high'] - row['low'],
                        abs(row['high'] - row['close']),
                        abs(row['low'] - row['close'])), axis=1)
    df['+dm'] = df['up'].where(df['up'] > df['down'], 0)
    df['-dm'] = df['down'].where(df['down'] > df['up'], 0)
    df['tr_smooth'] = df['tr'].rolling(period).sum()
    df['+dm_smooth'] = df['+dm'].rolling(period).sum()
    df['-dm_smooth'] = df['-dm'].rolling(period).sum()
    df['+di'] = 100 * df['+dm_smooth'] / df['tr_smooth']
    df['-di'] = 100 * df['-dm_smooth'] / df['tr_smooth']
    df['dx'] = 100 * abs(df['+di'] - df['-di']) / (df['+di'] + df['-di'])
    df['adx'] = df['dx'].rolling(period).mean()
    return df['adx']