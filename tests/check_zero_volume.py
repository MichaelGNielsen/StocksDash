import importlib.util
import pandas as pd
import pprint
import sys
import types

# Lightweight pandas_ta shim (EMA, RSI, ATR) so tests run without installing pandas_ta
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

ticker = 'TSLA'
timespans = ['1w','3mo','1y','5y']

for ts in timespans:
    print('\n-----')
    print(f'Checking {ticker} timespan={ts}')
    df, name = mod.get_stock_data(ticker, ts)
    if df.empty:
        print('No data returned')
        continue
    vol = df['Volume']
    zeros = (vol == 0).sum()
    nans = vol.isna().sum()
    negatives = (vol < 0).sum()
    print(f'Rows: {len(df)}, zeros: {zeros}, nans: {nans}, negatives: {negatives}, min={vol.min()}, max={vol.max()}')
    if zeros > 0:
        print('First zero rows:')
        print(df[vol==0].head().to_string())
    else:
        print('No zero-volume rows found in returned data')
