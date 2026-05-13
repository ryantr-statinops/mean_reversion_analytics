import pandas as pd

def generate_signal(df, config):
    # Kiểm tra đủ dữ liệu
    required_cols = ['close', 'upper', 'lower', 'rsi', 'adx', 'atr']
    if not all(col in df.columns for col in required_cols):
        return None

    last = df.iloc[-1]
    prev = df.iloc[-2]

    # Lọc xu hướng: chỉ trade nếu ADX < ngưỡng
    if last['adx'] >= config['adx_threshold']:
        return None

    # Tín hiệu MUA
    bb_buy = prev['close'] <= prev['lower'] and last['close'] > last['lower']
    rsi_buy = last['rsi'] < 30
    if bb_buy and rsi_buy:
        return "buy"

    # Tín hiệu BÁN
    bb_sell = prev['close'] >= prev['upper'] and last['close'] < last['upper']
    rsi_sell = last['rsi'] > 70
    if bb_sell and rsi_sell:
        return "sell"

    return None