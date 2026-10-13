import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime

def initialize_mt5():
    if not mt5.initialize():
        print("Lỗi khởi tạo MT5")
        return False
    print("MT5 đã khởi tạo")
    return True

def get_ohlc_data(symbol, timeframe, n_bars=100):
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, n_bars)
    if rates is None or len(rates) == 0:
        return None
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    return df[['time', 'open', 'high', 'low', 'close', 'tick_volume']]

def send_order(symbol, order_type, price, sl, tp, volume, magic):
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": volume,
        "type": mt5.ORDER_TYPE_BUY if order_type == "buy" else mt5.ORDER_TYPE_SELL,
        "price": price,
        "sl": sl,
        "tp": tp,
        "deviation": 50,
        "magic": magic,
        "comment": "MeanReversion_EURUSD",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }
    result = mt5.order_send(request)
    print(f"[{datetime.now()}] {order_type.upper()} {symbol} @ {price:.5f} → retcode: {result.retcode}")
    return result

def get_history(magic, from_date, to_date):
    deals = mt5.history_deals_get(from_date, to_date)
    if deals is None:
        return pd.DataFrame()
    df = pd.DataFrame(list(deals), columns=deals[0]._asdict().keys())
    return df[df['magic'] == magic]