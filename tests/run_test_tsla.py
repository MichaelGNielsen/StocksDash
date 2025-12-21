import importlib.util
import pprint
import sys
import types
import pandas as pd

# Provide a lightweight shim for pandas_ta when not installed.
ta = types.SimpleNamespace()

def ema(series, length):
    return series.ewm(span=length, adjust=False).mean()

def rsi(series, length):
    delta = series.diff()
    up = delta.clip(lower=0)
    down = -1 * delta.clip(upper=0)
    ma_up = up.ewm(alpha=1/length, adjust=False).mean()
    ma_down = down.ewm(alpha=1/length, adjust=False).mean()
    rs = ma_up / ma_down
    return 100 - (100 / (1 + rs))

def atr(high, low, close, length):
    tr1 = high - low
    tr2 = (high - close.shift()).abs()
    tr3 = (low - close.shift()).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.rolling(window=length, min_periods=1).mean()

ta.ema = ema
ta.rsi = rsi
ta.atr = atr

sys.modules['pandas_ta'] = ta

spec = importlib.util.spec_from_file_location('data', r'c:\Users\mgn\OneDrive\src\python\stock_work\stocks\data.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

print('Calling get_stock_data("TSLA","1y") from WSL...')
df, name = mod.get_stock_data('TSLA', '1y')
print('Company name:', name)
print('Rows fetched:', len(df))
print('Columns:', list(df.columns) if not df.empty else 'EMPTY')

# print first 3 rows summary
if not df.empty:
    print('\nFirst 3 rows:')
    pprint.pprint(df.head(3).to_dict('index'))
