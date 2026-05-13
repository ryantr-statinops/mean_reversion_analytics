import json
import pandas as pd
from datetime import datetime, timedelta
import MetaTrader5 as mt5
from src.mt5_connector import initialize_mt5, get_history

with open("config/strategy_config.json") as f:
    config = json.load(f)

if not initialize_mt5():
    quit()

from_date = datetime.now() - timedelta(days=7)
to_date = datetime.now()

df = get_history(config["magic_number"], from_date, to_date)

if not df.empty:
    df.to_csv("data/results/trades_eurusd.csv", index=False)
    print(f"✅ Đã lưu {len(df)} lệnh vào data/results/trades_eurusd.csv")
else:
    print("⚠️ Không có lệnh nào được tìm thấy.")

mt5.shutdown()