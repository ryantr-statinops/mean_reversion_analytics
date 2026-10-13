import pandas as pd

def generate_signal(df, config):
    # Validate sufficient data
    required_cols = ['close', 'upper', 'lower', 'rsi', 'adx', 'atr']
    if not all(col in df.columns for col in required_cols):
        return None

    last = df.iloc[-1]
    prev = df.iloc[-2]

    # Trend filter: only trade when ADX is below the threshold
    if last['adx'] >= config['adx_threshold']:
        return None

    # BUY signal
    bb_buy = prev['close'] <= prev['lower'] and last['close'] > last['lower']
    rsi_buy = last['rsi'] < 30
    if bb_buy and rsi_buy:
        return "buy"

    # SELL signal
    bb_sell = prev['close'] >= prev['upper'] and last['close'] < last['upper']
    rsi_sell = last['rsi'] > 70
    if bb_sell and rsi_sell:
        return "sell"

    return None