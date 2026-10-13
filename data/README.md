# Data

Thư mục chứa dữ liệu export và kết quả phân tích. Không commit file CSV/JSON (xem `.gitignore`).

- Chạy `python scripts/export_history.py` để tạo `results/trades.csv` (multi-symbol, lọc theo `magic_number`).
- Mở `notebooks/performance_analysis.ipynb` để xem hiệu suất. Notebook tự bỏ qua khi chưa có file.
