import MetaTrader5 as mt5

if mt5.initialize():
    print("MT5 connection OK!")
    info = mt5.account_info()
    print(f"Account ID: {info.login}")
    mt5.shutdown()
else:
    print("MT5 connection error:", mt5.last_error())