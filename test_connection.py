import MetaTrader5 as mt5

if mt5.initialize():
    print("Kết nối MT5 thành công!")
    info = mt5.account_info()
    print(f"ID tài khoản: {info.login}")
    mt5.shutdown()
else:
    print("Lỗi kết nối MT5:", mt5.last_error())