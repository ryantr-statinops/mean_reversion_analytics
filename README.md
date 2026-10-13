# Mean Reversion Trading Bot – Multi-Symbol (MT5)

![Trading Bot](https://img.shields.io/badge/Status-Live-green)
![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Platform](https://img.shields.io/badge/Platform-MetaTrader%205-orange)

A professional algorithmic trading bot designed for the **MetaTrader 5 (MT5)** platform. This bot implements a **Mean Reversion** strategy across multiple financial instruments, including FX pairs, Gold (XAUUSD), and Indices (S&P 500).

---

## Strategy Overview

The bot identifies overextended price movements and trades the return to the mean. It uses a combination of volatility, momentum, and trend strength filters.

### Core Indicators
- **Bollinger Bands (BB)**: Defines the "mean" and standard deviation boundaries.
- **Relative Strength Index (RSI)**: Confirms overbought/oversold conditions.
- **Average Directional Index (ADX)**: Acts as a regime filter to ensure trades are only taken in low-trend (sideways) environments.
- **Average True Range (ATR)**: Used for dynamic volatility-based Stop Loss calculation.

### Entry Conditions
*   **BUY**: Price crosses above the Lower Bollinger Band AND RSI < 30 AND ADX < 18.
*   **SELL**: Price crosses below the Upper Bollinger Band AND RSI > 70 AND ADX < 18.

### Risk Management
- **Dynamic SL**: 1.5x ATR distance from entry.
- **Risk/Reward (RR)**: Default 0.9 (configurable).
- **Time Filter**: Operates strictly between **13:00 – 17:00 (GMT+7)** to capture specific liquidity windows.

---

## Project Structure

```text
mean_reversion_eurusd_bot/
├── config/
│   └── strategy_config.json    # Bot parameters & symbol list
├── src/
│   ├── indicators.py           # Technical indicator logic (BB, RSI, ADX, ATR)
│   ├── mt5_connector.py        # MT5 API bridge & order execution
│   └── strategy.py             # Signal generation logic
├── scripts/
│   ├── run_bot.py              # Main execution loop
│   └── export_history.py       # Trade history exporter
├── data/                       # Historical data & exports
├── notebooks/                  # Performance analysis & backtesting
├── requirements.txt            # Project dependencies
└── .gitignore                  # Git exclusion rules
```

---

## Installation & Setup

### 1. Prerequisites
- **Windows OS** (Required for MetaTrader 5 Python API).
- **MetaTrader 5 Terminal** installed and logged into an account.
- **Algo Trading** enabled in MT5 (Tools > Options > Expert Advisors).

### 2. Environment Setup
Clone the repository and install dependencies:

```bash
# Create virtual environment
python -m venv .venv

# Activate environment
# Windows:
.venv\Scripts\activate

# Install requirements
pip install -r requirements.txt
```

---

## Usage

### Test Connection
Before running the bot, verify the connection to MT5:
```bash
python test_connection.py
```

### Run the Bot
To start the live trading loop:
```bash
python scripts/run_bot.py
```

### Export History
To export your trade history to a CSV file for analysis:
```bash
python scripts/export_history.py
```

---

## Configuration

Modify `config/strategy_config.json` to adjust the bot's behavior:

```json
{
  "symbols": ["EURUSDm", "GBPUSDm", "XAUUSDm"],
  "timeframe": "M1",
  "bb_period": 10,
  "bb_std": 1.8,
  "rsi_period": 8,
  "adx_threshold": 18,
  "risk_reward": 0.9
}
```

---

## Disclaimer

**Trading financial instruments involves significant risk.** This bot is for educational and research purposes only. Past performance does not guarantee future results. Use at your own risk. The developer is not responsible for any financial losses incurred.

---
**Author:** [Your Name/Github]  
**License:** MIT