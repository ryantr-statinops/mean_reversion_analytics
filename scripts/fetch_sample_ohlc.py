"""Fetch sample OHLC (Stooq, fallback synthetic) and generate sample trades.csv.

Usage (repo root):
    python scripts/fetch_sample_ohlc.py
    python scripts/fetch_sample_ohlc.py --source synthetic --bars 500 --seed 42

Output (gitignored, for local notebook verification only):
    data/sample/ohlc_<SYMBOL>.csv
    data/results/trades.csv  (columns: time, profit, symbol)

Notes:
- Stooq free endpoint only gives daily bars, good enough to verify
  notebooks/performance_analysis.ipynb end-to-end, NOT for M1 strategy validation.
- Profit is synthetic: TP/SL distance from ATR * risk_reward, converted
  to USD with a rough per-symbol factor. Do not use for live decisions.
"""

import argparse
import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.append(str(Path(__file__).resolve().parent.parent))

from src.indicators import calculate_adx, calculate_atr, calculate_bb, calculate_rsi
from src.strategy import generate_signal

BASE_DIR = Path(__file__).resolve().parent.parent

# MT5 symbol -> Stooq symbol
STOOQ_MAP = {
    "EURUSDm": "eurusd",
    "GBPUSDm": "gbpusd",
    "USDCHFm": "usdchf",
    "AUDUSDm": "audusd",
    "XAUUSDm": "xauusd",
    "US500m": "^spx",
}

# Rough USD conversion for synthetic profit (sample only)
USD_FACTOR = {
    "EURUSDm": 100000.0,
    "GBPUSDm": 100000.0,
    "USDCHFm": 100000.0,
    "AUDUSDm": 100000.0,
    "XAUUSDm": 100.0,
    "US500m": 10.0,
}

BASE_PRICE = {
    "EURUSDm": 1.0850,
    "GBPUSDm": 1.2700,
    "USDCHFm": 0.8900,
    "AUDUSDm": 0.6600,
    "XAUUSDm": 2350.0,
    "US500m": 5300.0,
}


def fetch_stooq(symbol: str, timeout: int = 15) -> pd.DataFrame | None:
    code = urllib.parse.quote(STOOQ_MAP[symbol], safe="^")
    url = f"https://stooq.com/q/d/l/?s={code}&i=d"
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            df = pd.read_csv(resp)
    except Exception as exc:
        print(f"Invalid Stooq {symbol}: {exc}, fallback synthetic")
        return None
    df.columns = [c.strip().lower() for c in df.columns]
    if not {"date", "open", "high", "low", "close"}.issubset(df.columns):
        print(f"Invalid Stooq schema {symbol}: {list(df.columns)}, fallback synthetic")
        return None
    df = df.dropna().tail(500).reset_index(drop=True)
    if len(df) < 60:
        print(f"Invalid Stooq bars {symbol}: {len(df)}, fallback synthetic")
        return None
    df["time"] = pd.to_datetime(df["date"])
    df["symbol"] = symbol
    return df[["time", "open", "high", "low", "close", "symbol"]]


def synthetic_ohlc(symbol: str, bars: int, seed: int) -> pd.DataFrame:
    rng = np.random.default_rng(hash((seed, symbol)) % (2**32))
    base = BASE_PRICE.get(symbol, 1.0)
    vol = base * 0.002
    rets = rng.normal(0, 1, bars) * vol / base
    # Mild mean-reversion so BB/RSI signals actually fire
    rets[1:] -= 0.15 * rets[:-1]
    close = base * (1 + np.cumsum(rets))
    spread = np.abs(rng.normal(0, vol * 0.5, bars))
    df = pd.DataFrame(
        {
            "time": pd.date_range(end=pd.Timestamp.now().floor("D"), periods=bars, freq="D"),
            "open": close,
            "high": close + spread,
            "low": close - spread,
            "close": close,
            "symbol": symbol,
        }
    )
    return df


def simulate_trades(df: pd.DataFrame, config: dict, symbol: str) -> list[dict]:
    work = df.copy()
    bb = calculate_bb(work, config["bb_period"], config["bb_std"])
    work["rsi"] = calculate_rsi(work, config["rsi_period"])
    work["adx"] = calculate_adx(work, config["adx_period"])
    work["atr"] = calculate_atr(work, config["atr_period"])
    work = pd.concat([work, bb], axis=1).dropna().reset_index(drop=True)

    volume = config.get("volume_map", {}).get(symbol, config.get("volume", 0.01))
    factor = USD_FACTOR.get(symbol, 100000.0)
    rr = config.get("risk_reward", 0.9)
    trades = []

    for i in range(2, len(work) - 5):
        window = work.iloc[: i + 1]
        signal = generate_signal(window, config)
        if signal is None:
            continue
        entry = float(work.loc[i, "close"])
        atr = float(work.loc[i, "atr"])
        if not np.isfinite(atr) or atr <= 0:
            continue
        sl_dist = atr * 1.5
        tp_dist = sl_dist * rr
        # Look ahead 5 bars: TP hit first = win, SL hit first = loss
        outcome = None
        for j in range(i + 1, min(i + 6, len(work))):
            h, low = float(work.loc[j, "high"]), float(work.loc[j, "low"])
            if signal == "buy":
                if h >= entry + tp_dist:
                    outcome = "win"
                    break
                if low <= entry - sl_dist:
                    outcome = "loss"
                    break
            else:
                if low <= entry - tp_dist:
                    outcome = "win"
                    break
                if h >= entry + sl_dist:
                    outcome = "loss"
                    break
        if outcome is None:  # time exit at +5 bars
            exit_px = float(work.loc[min(i + 5, len(work) - 1), "close"])
            pnl_price = (exit_px - entry) if signal == "buy" else (entry - exit_px)
            profit = pnl_price * volume * factor
        else:
            profit = (tp_dist if outcome == "win" else -sl_dist) * volume * factor
        trades.append(
            {
                "time": int(pd.Timestamp(work.loc[i, "time"]).timestamp()),
                "profit": round(float(profit), 2),
                "symbol": symbol,
            }
        )
    return trades


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", choices=["stooq", "synthetic"], default="stooq")
    ap.add_argument("--bars", type=int, default=500)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    with open(BASE_DIR / "config" / "strategy_config.json") as f:
        config = json.load(f)

    sample_dir = BASE_DIR / "data" / "sample"
    sample_dir.mkdir(parents=True, exist_ok=True)
    all_trades: list[dict] = []

    for symbol in config["symbols"]:
        ohlc = None
        if args.source == "stooq":
            ohlc = fetch_stooq(symbol)
        if ohlc is None:
            ohlc = synthetic_ohlc(symbol, args.bars, args.seed)
            print(f"Synthetic {symbol}: {len(ohlc)} bars")
        else:
            print(f"Stooq {symbol}: {len(ohlc)} bars")
        ohlc.to_csv(sample_dir / f"ohlc_{symbol}.csv", index=False)
        trades = simulate_trades(ohlc, config, symbol)
        print(f"Trades {symbol}: {len(trades)}")
        all_trades.extend(trades)

    if not all_trades:
        print("No trades generated, notebook will show empty state")
        all_trades = [
            {"time": 1728566400, "profit": 12.5, "symbol": config["symbols"][0]},
            {"time": 1728566700, "profit": -8.2, "symbol": config["symbols"][0]},
        ]

    out = BASE_DIR / "data" / "results" / "trades.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(all_trades).sort_values("time").to_csv(out, index=False)
    print(f"Saved {len(all_trades)} sample trades -> {out}")


if __name__ == "__main__":
    main()
