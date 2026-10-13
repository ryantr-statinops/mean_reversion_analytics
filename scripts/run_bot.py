import json
import time
import pandas as pd
from datetime import datetime
import MetaTrader5 as mt5
from src.mt5_connector import initialize_mt5, get_ohlc_data, send_order
from src.indicators import calculate_bb, calculate_rsi, calculate_adx, calculate_atr
from src.strategy import generate_signal
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Cooldown tracker (60 giây mỗi cặp)
LAST_TRADE_TIME = {}

# Mapping timeframe
TIMEFRAME_MAP = {
    "M1": mt5.TIMEFRAME_M1,
    "M5": mt5.TIMEFRAME_M5,
    "M15": mt5.TIMEFRAME_M15,
    "H1": mt5.TIMEFRAME_H1,
}

# Load config
with open("config/strategy_config.json") as f:
    config = json.load(f)

TIMEFRAME = TIMEFRAME_MAP[config["timeframe"]]
MAGIC = config["magic_number"]
RR = config["risk_reward"]
VOLUME_MAP = config.get("volume_map", {})

# Initialize MT5
if not initialize_mt5():
    quit()

SYMBOLS = []
for sym in config["symbols"]:
    if mt5.symbol_select(sym, True):
        SYMBOLS.append(sym)
        print(f"Đã chọn {sym}")
    else:
        print(f"Không thể chọn {sym}")

if not SYMBOLS:
    print("Không có cặp nào hợp lệ.")
    quit()

print("Bot Mean Reversion (6 cặp) đã chạy...")
print("Cập nhật mỗi 15 giây | Chỉ trade 13:00–17:00 (GMT+7) | Algo Trading phải được BẬT")

try:
    while True:
        # === LỌC GIỜ GIAO DỊCH ===
        current_hour = datetime.now().hour  # Múi giờ hệ thống = GMT+7 (nếu bạn ở VN)
        if not (13 <= current_hour <= 17):
            # Vẫn in trạng thái nhưng không trade
            status_parts = []
            for SYMBOL in SYMBOLS:
                status_parts.append(f"{SYMBOL}: OFF")
            print(f"[{datetime.now().strftime('%H:%M:%S')}] " + " | ".join(status_parts))
            time.sleep(15)
            continue

        # === PHASE 1: TRẠNG THÁI GIÁ CÓ TIMESTAMP ===
        status_parts = []
        symbol_data = {}

        for SYMBOL in SYMBOLS:
            df = get_ohlc_data(SYMBOL, TIMEFRAME, 100)
            symbol_data[SYMBOL] = df
            if df is None or len(df) < 50:
                status_parts.append(f"{SYMBOL}: N/A")
                continue

            price = df['close'].iloc[-1]
            if "XAU" in SYMBOL or "US500" in SYMBOL or "SP500" in SYMBOL:
                fmt = f"{price:.1f}".replace(".", "")
            else:
                fmt = f"{price:.5f}".replace(".", "")
            status_parts.append(f"{SYMBOL}: {fmt}")

        print(f"[{datetime.now().strftime('%H:%M:%S')}] " + " | ".join(status_parts))

        # === PHASE 2: PHÂN TÍCH & GỬI LỆNH ===
        for SYMBOL in SYMBOLS:
            df = symbol_data[SYMBOL]
            if df is None or len(df) < 50:
                continue

            # Tính chỉ báo
            bb = calculate_bb(df, config["bb_period"], config["bb_std"])
            df['rsi'] = calculate_rsi(df, config["rsi_period"])
            df['adx'] = calculate_adx(df, config["adx_period"])
            df['atr'] = calculate_atr(df, config["atr_period"])
            df = pd.concat([df, bb], axis=1)

            # --- DEBUG: KIỂM TRA ĐIỀU KIỆN CHI TIẾT ---
            last = df.iloc[-1]
            bb_buy = last['close'] < last['lower']
            bb_sell = last['close'] > last['upper']
            rsi_buy = last['rsi'] < 30
            rsi_sell = last['rsi'] > 70
            adx_ok = last['adx'] < config['adx_threshold']

            # Xác định tín hiệu thủ công (để debug)
            signal = None
            if bb_buy and rsi_buy and adx_ok:
                signal = "buy"
            elif bb_sell and rsi_sell and adx_ok:
                signal = "sell"

            # In debug nếu điều kiện gần đúng
            if not signal:
                reasons = []
                if not (bb_buy or bb_sell):
                    reasons.append("BB")
                if not (rsi_buy or rsi_sell):
                    reasons.append("RSI")
                if not adx_ok:
                    reasons.append("ADX")
                if reasons:
                    print(f"[DEBUG] {SYMBOL} không trade: {' + '.join(reasons)} | RSI={last['rsi']:.1f}, ADX={last['adx']:.1f}")
                continue

            # --- COOLDOWN ---
            now = datetime.now()
            if SYMBOL in LAST_TRADE_TIME:
                if (now - LAST_TRADE_TIME[SYMBOL]).total_seconds() < 60:
                    continue

            # --- GỬI LỆNH ---
            price = mt5.symbol_info_tick(SYMBOL).ask if signal == "buy" else mt5.symbol_info_tick(SYMBOL).bid
            atr_val = df['atr'].iloc[-1]
            sl_dist = atr_val * 1.5
            tp_dist = sl_dist * RR
            sl = price - sl_dist if signal == "buy" else price + sl_dist
            tp = price + tp_dist if signal == "buy" else price - tp_dist
            volume = VOLUME_MAP.get(SYMBOL, 0.01)

            result = send_order(SYMBOL, signal, price, sl, tp, volume, MAGIC)
            LAST_TRADE_TIME[SYMBOL] = now

            if result.retcode == mt5.TRADE_RETCODE_DONE:
                print(f"\n[{now.strftime('%Y-%m-%d %H:%M:%S')}] LỆNH KHỚP: {signal.upper()} {SYMBOL} @ {price:.5f}")
            else:
                print(f"\n[{now.strftime('%Y-%m-%d %H:%M:%S')}] LỆNH GỬI NHƯNG CHƯA KHỚP ({result.retcode}): {SYMBOL}")

        time.sleep(15)

except KeyboardInterrupt:
    print("\nBot đã dừng.")
finally:
    mt5.shutdown()