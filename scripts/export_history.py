import json
import os
from pathlib import Path
import pandas as pd
from datetime import datetime, timedelta
import MetaTrader5 as mt5
from src.mt5_connector import initialize_mt5, get_history

BASE_DIR = Path(__file__).resolve().parent.parent
with open(BASE_DIR / "config" / "strategy_config.json") as f:
    config = json.load(f)

if not initialize_mt5():
    quit()

from_date = datetime.now() - timedelta(days=7)
to_date = datetime.now()

df = get_history(config["magic_number"], from_date, to_date)

output_path = BASE_DIR / "data" / "results" / "trades.csv"
output_path.parent.mkdir(parents=True, exist_ok=True)

if not df.empty:
    df.to_csv(output_path, index=False)
    print(f"Saved {len(df)} deals to {output_path}")
else:
    print("No deals found.")

mt5.shutdown()