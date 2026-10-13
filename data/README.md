# Data

This folder holds exported data and analysis results. CSV/JSON files are not committed (see `.gitignore`).

- Run `python scripts/export_history.py` to generate `results/trades.csv` (multi-symbol, filtered by `magic_number`).
- Open `notebooks/performance_analysis.ipynb` to review performance. The notebook skips gracefully when no file exists yet.
