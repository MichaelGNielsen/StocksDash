import yfinance as yf
import pandas as pd
import pandas_ta as ta
import json
import os
import re
import time
from functools import lru_cache
from yfinance.exceptions import YFRateLimitError

ticker_file = "tickers.json"
preferences_file = "user_preferences.json"

@lru_cache(maxsize=100)
def cached_get_stock_data(ticker, timespan):
    print(f"Debug: cached_get_stock_data kaldt med ticker: {ticker}, timespan: {timespan}")
    return get_stock_data(ticker, timespan)

def normalize_ticker(ticker):
    print(f"Debug: normalize_ticker kaldt med input: {ticker}")
    if not ticker or not isinstance(ticker, str):
        print(f"Debug: normalize_ticker modtog ugyldig ticker: {ticker}. Returnerer tom streng.")
        return ''
    ticker = ticker.upper().strip()
    print(f"Debug: normalize_ticker konverterede til: {ticker}")
    return ticker

@lru_cache(maxsize=100)
def get_company_name(ticker):
    print(f"Debug: get_company_name kaldt med ticker: {ticker}")
    try:
        company = yf.Ticker(ticker)
        info = company.info
        name = info.get('longName', ticker)
        print(f"Debug: get_company_name for {ticker} returnerede: {name}")
        return name
    except Exception as e:
        print(f"Debug: Fejl i get_company_name for {ticker}: {e}")
        return ticker

@lru_cache(maxsize=100)
def get_long_name(ticker):
    print(f"Debug: get_long_name kaldt med ticker: {ticker}")
    stock = yf.Ticker(ticker)
    try:
        name = stock.info['longName']
        print(f"Debug: get_long_name for {ticker} returnerede: {name}")
        return name
    except KeyError:
        print(f"Debug: get_long_name fandt ingen longName for {ticker}")
        return ticker

@lru_cache(maxsize=100)
def get_pe_ratio(ticker):
    ticker = normalize_ticker(ticker)
    print(f"Debug: get_pe_ratio kaldt med ticker: {ticker}")
    stock = yf.Ticker(ticker)
    try:
        pe = stock.info['trailingPE']
        print(f"Debug: get_pe_ratio for {ticker} returnerede: {pe}")
        return pe
    except KeyError:
        print(f"Debug: get_pe_ratio fandt ingen trailingPE for {ticker}")
        return None

@lru_cache(maxsize=100)
def get_beta(ticker):
    ticker = normalize_ticker(ticker)
    print(f"Debug: get_beta kaldt med ticker: {ticker}")
    stock = yf.Ticker(ticker)
    try:
        beta = stock.info['beta']
        print(f"Debug: get_beta for {ticker} returnerede: {beta}")
        return beta
    except KeyError:
        print(f"Debug: get_beta fandt ingen beta for {ticker}")
        return None

# --- NY FUNKTION: Tæl AFVENT dage ---
def count_pending_days(df):
    """ Tæller hvor mange dage i træk status har været AFVENT """
    if df is None or 'perfect_order' not in df or 'extension_pc' not in df:
        return 0

    count = 0
    # Definition af AFVENT (Perfect order OK, men pris er > 5% over SMA20)
    pending_series = df['perfect_order'] & (df['extension_pc'] >= 5.0)

    for is_pending in reversed(pending_series):
        if is_pending:
            count += 1
        else:
            break
    print(f"Debug: count_pending_days returnerede {count} dage")
    return count

def check_perfect_order(df):
    print(f"Debug: check_perfect_order kaldt")
    """
    Analyserer om en aktie er i en 'Perfect Order' trend.
    Regler:
    1. SMA 5 > SMA 10 > SMA 20
    2. Alle tre gennemsnit skal stige (nuværende værdi > forrige værdi)
    3. Valgfrit filter: Pris over SMA 200 for langsigtede trends.
    """
    print(f"Debug: check_perfect_order kaldt")
    # Sørg for at vi har nok data til beregningerne
    if df is None or len(df) < 200:
        print(f"Debug: check_perfect_order - for lidt data ({len(df) if df is not None else 0})")
        return df

    # find close-series (støt både 'Close' og 'close')
    if 'Close' in df:
        close = df['Close']
    elif 'close' in df:
        close = df['close']
    else:
        return df

    # Genbrug allerede beregnede SMA200 hvis tilgængelig
    if 'SMA200' in df:
        sma200 = df['SMA200']
    else:
        try:
            sma200 = ta.sma(close, length=200)
        except Exception:
            sma200 = close.rolling(window=200, min_periods=1).mean()
        df['sma200'] = sma200

    # Beregn SMA værdier (brug pandas_ta hvis muligt)
    try:
        df['sma5'] = ta.sma(close, length=5)
        df['sma10'] = ta.sma(close, length=10)
        df['sma20'] = ta.sma(close, length=20)
        # hvis ikke allerede sat, sæt sma200 (laves ovenfor)
        df['sma200'] = df.get('sma200', sma200)
    except Exception as e:
        print(f"Debug: Fejl i SMA beregning i check_perfect_order: {e}")
        df['sma5'] = close.rolling(window=5, min_periods=1).mean()
        df['sma10'] = close.rolling(window=10, min_periods=1).mean()
        df['sma20'] = close.rolling(window=20, min_periods=1).mean()
        df['sma200'] = df.get('sma200', close.rolling(window=200, min_periods=1).mean())

    # Tjek rækkefølgen (The Stack)
    df['stack_ok'] = (df['sma5'] > df['sma10']) & (df['sma10'] > df['sma20'])

    # Tjek hældningen (optrending)
    df['sma5_rising'] = df['sma5'] > df['sma5'].shift(1)
    df['sma10_rising'] = df['sma10'] > df['sma10'].shift(1)
    df['sma20_rising'] = df['sma20'] > df['sma20'].shift(1)
    df['all_rising'] = df['sma5_rising'] & df['sma10_rising'] & df['sma20_rising']

    # Kombineret signal
    df['perfect_trend'] = df['stack_ok'] & df['all_rising']

    # Langsigtet filter
    df['long_term_ok'] = close > df['sma200']

    return df


def get_trade_signals(df):
    """
    Opretter handels-signaler: 1 = køb, -1 = salg, 0 = neutral.
    Købs-logik: Perfect Order (sma5>sma10>sma20) + sma5 stigende + pris > sma200
    Salgs-logik: sma5 krydser under sma10 OR pris < sma20
    """
    print(f"Debug: get_trade_signals kaldt")
    if df is None or len(df) < 20:
        return df

    # find close-series (støtter både 'Close' og 'close')
    if 'Close' in df:
        close = df['Close']
    elif 'close' in df:
        close = df['close']
    else:
        return df

    # Genbrug eksisterende SMA-kolonner hvis mulige, ellers beregn
    for days in (5, 10, 20, 200):
        col = f'sma{days}'
        if col not in df:
            try:
                df[col] = ta.sma(close, length=days)
            except Exception:
                df[col] = close.rolling(window=days, min_periods=1).mean()

    # Bevar tidligere simple boolean-signal (hvis til stede)
    if 'signal' in df:
        df['signal_basic'] = df['signal']

    # Købs-logik (Perfect Order + stigende + pris > sma200)
    buy_condition = (
        (df['sma5'] > df['sma10']) &
        (df['sma10'] > df['sma20']) &
        (df['sma5'] > df['sma5'].shift(1)) &
        (close > df['sma200'])
    )

    # Salgs-logik
    sell_condition = (df['sma5'] < df['sma10']) | (close < df['sma20'])

    # Opret signal-kolonne: 0 neutral, 1 køb, -1 salg
    df['signal'] = 0
    df.loc[buy_condition.fillna(False), 'signal'] = 1
    df.loc[sell_condition.fillna(False), 'signal'] = -1

    return df


def get_trade_signals_with_stop(df):
    """
    Handels-signaler med stop-loss:
    - Beregner sma5/10/20/200 og ATR
    - Buy: Perfect Order + sma5 stigende + pris > sma200
    - Stop loss: sma20 - 0.5 * ATR
    - Sell: pris < stop_loss eller sma5 < sma10
    """
    print(f"Debug: get_trade_signals_with_stop kaldt")

    if df is None or len(df) < 20:
        return df

    # support både kapitaliserede kolonnenavne og små
    if 'Close' in df:
        close = df['Close']
    elif 'close' in df:
        close = df['close']
    else:
        return df

    if 'High' in df:
        high = df['High']
    else:
        high = df.get('high', close)
    if 'Low' in df:
        low = df['Low']
    else:
        low = df.get('low', close)

    # Beregn SMA'er (genbrug hvis tilstede)
    for days in (5, 10, 20, 200):
        col = f'sma{days}'
        if col not in df:
            try:
                df[col] = ta.sma(close, length=days)
            except Exception:
                df[col] = close.rolling(window=days, min_periods=1).mean()

    # Beregn ATR
    try:
        df['atr'] = ta.atr(high, low, close, length=14)
    except Exception:
        # Enkel ATR-approx (true range rolling mean)
        tr1 = high - low
        tr2 = (high - close.shift()).abs()
        tr3 = (low - close.shift()).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        df['atr'] = tr.rolling(window=14, min_periods=1).mean()

    # Købslogik
    buy_condition = (
        (df['sma5'] > df['sma10']) &
        (df['sma10'] > df['sma20']) &
        (close > df['sma200']) &
        (df['sma5'] > df['sma5'].shift(1))
    )

    # Stop loss niveau
    df['stop_loss'] = df['sma20'] - (df['atr'] * 0.5)

    # Salgslogik
    sell_condition = (close < df['stop_loss']) | (df['sma5'] < df['sma10'])

    # Signal kolonne: 1 køb, -1 sælg, 0 neutral
    df['signal'] = 0
    df.loc[buy_condition.fillna(False), 'signal'] = 1
    df.loc[sell_condition.fillna(False), 'signal'] = -1

    return df

# --- OPDATERET: Advanced Trade Signals med trafiklys ---
def get_advanced_trade_signals(df, ticker_name="UKENDT"):
    """
    Opdateret med Breakout + Volumen filter.
    Køb kræver nu at volumen er højere end gennemsnittet for at bekræfte styrke.
    """
    print(f"Debug: get_advanced_trade_signals med volumen-filter kaldt for {ticker_name}")

    if df is None or len(df) < 20:
        return df

    # Arbejd på en kopi for at undgå problemer
    df = df.copy()

    close = df['Close'] if 'Close' in df else df.get('close')
    volume = df['Volume'] if 'Volume' in df else df.get('volume')
    high = df['High'] if 'High' in df else df.get('high')

    # Kør de tekniske beregninger
    df = check_perfect_order(df)

    # Sikr at 'perfect_order' kolonnen findes (check_perfect_order laver 'perfect_trend')
    if 'perfect_trend' in df:
        df['perfect_order'] = df['perfect_trend']
    else:
        df['perfect_order'] = (df['sma5'] > df['sma10']) & (df['sma10'] > df['sma20'])

    # --- VOLUMEN FILTER ---
    # Vi beregner gennemsnitlig volumen over 20 dage
    df['vol_avg_20'] = volume.rolling(window=20).mean()
    df['high_volume'] = volume > df['vol_avg_20']

    # Beregn 20-dages High (Breakout niveau)
    df['20d_high'] = high.rolling(window=20).max()

    # Beregn extension
    df['extension_pc'] = ((close - df['sma20']) / df['sma20']) * 100
    df['near_breakout'] = close >= (df['20d_high'] * 0.98)

    # NYE REGLER (Lempede): Volumen og Breakout er nu "bonus" info, ikke hårde krav.
    df['buy_signal'] = (df['perfect_order']) & \
                       (df['long_term_ok']) & \
                       (df['extension_pc'] < 8.0)
                       # & (df['near_breakout']) & (df['high_volume']) # <--- Gjort valgfri

    # Salgsregler (uændret)
    df['sell_signal'] = (df['sma5'] < df['sma10']) | (close < df['sma20'])

    df['signal'] = 0
    df.loc[df['buy_signal'].fillna(False), 'signal'] = 1
    df.loc[df['sell_signal'].fillna(False), 'signal'] = -1

    # Debug print
    try:
        last = df.iloc[-1]
        print(f"--- STATUS {ticker_name} (Sidste data) ---")
        print(f"Pris: {last[close.name]:.2f} | Vol: {last[volume.name]:.0f} (Snit: {last['vol_avg_20']:.0f})")
        print(f"Perfect Order: {last['perfect_order']} | Long Term: {last['long_term_ok']}")
        print(f"Extension: {last['extension_pc']:.2f}% (Limit: 8.0%)")
        print(f"Breakout: {last['near_breakout']} (High: {last['20d_high']:.2f})")
        print(f"High Volume: {last['high_volume']}")
        if last['signal'] == 1:
            extras = []
            if last['near_breakout']: extras.append("Breakout")
            if last['high_volume']: extras.append("Volumen")
            print(f"🚀 KØB SIGNAL: Perfect Order OK. Ekstra styrke: {', '.join(extras) if extras else 'Ingen'}")
        elif last['signal'] == -1:
            print("🛑 SALG SIGNAL: Trend brudt.")
        else:
            print("⚪ AFVENT: Mangler volumen, breakout eller perfect order.")
    except Exception as e:
        print(f"Debug: Kunne ikke printe status: {e}")

    return df



def get_stock_data(ticker, timespan):
    ticker = normalize_ticker(ticker)
    print(f"Debug: get_stock_data kaldt med ticker: {ticker}, timespan: {timespan}")
    stock = yf.Ticker(ticker)

    period_map = {
        "1d": "1d", "1w": "1wk", "1mo": "1mo", "3mo": "3mo",
        "6mo": "6mo", "1y": "1y", "3y": "3y", "5y": "5y",
        "10y": "10y", "max": "max"
    }

    # Altid hent max data (eller 10y som fallback) for at have nok data til alle indikatorer
    print(f"Debug: Henter 'max' data for indikatorberegning")

    for attempt in range(3):
        try:
            # Hent altid max data for indikatorberegning
            full_data = stock.history(period="max")
            ticker_long = get_long_name(ticker)

            if full_data.empty:
                print(f"Debug: Tomt datasæt returneret for {ticker}")
                return pd.DataFrame(), ticker_long

            required_columns = ['Close', 'Volume', 'Open', 'High', 'Low']
            missing_columns = [col for col in required_columns if col not in full_data]
            if missing_columns:
                print(f"Debug: Manglende kolonner i data for {ticker}: {missing_columns}")
                return pd.DataFrame(), ticker_long

            # Beregn tekniske indikatorer på FULDT datasæt
            print(f"Debug: Beregner indikatorer på {len(full_data)} datapunkter")
            # Beregn SMA200 og genbrug som 'EMA200' for kompatibilitet med resten af koden.
            # Dette undgår at beregne 200-dages glidende gennemsnit to gange (i plotting).
            full_data['SMA200'] = full_data['Close'].rolling(window=200, min_periods=1).mean()
            # Behold kolonnenavn 'EMA200' for bagudkompatibilitet (brug SMA200 værdi)
            full_data['EMA200'] = full_data['SMA200']
            full_data['RSI'] = ta.rsi(full_data['Close'], length=14)
            full_data['ATR'] = ta.atr(full_data['High'], full_data['Low'], full_data['Close'], length=14)

            # Logik for købssignal (behold som basic-signal)
            full_data['signal'] = (full_data['Close'] > full_data['EMA200']) & (full_data['RSI'] > 60)
            full_data['signal_basic'] = full_data['signal']

            # Beregn check_perfect_order (Perfect Order) og tilføj kolonner til full_data
            try:
                full_data = check_perfect_order(full_data)
            except Exception as e:
                print(f"Debug: Fejl ved beregning af check_perfect_order: {e}")

            # Beregn trade-signaler (køb/sælg/neutral) og overskriv 'signal' med -1/0/1
            try:
                # Brug den nye avancerede strategi (Perfect Order + Extension + Volumen)
                full_data = get_advanced_trade_signals(full_data, ticker_name=ticker_long)
            except Exception as e:
                print(f"Debug: Fejl ved beregning af trade-signaler: {e}")

            # Filtrer data baseret på valgt timespan
            requested_period = period_map.get(timespan, "1y")
            if requested_period != "max":
                # Konverter index til DatetimeIndex hvis nødvendigt
                if not isinstance(full_data.index, pd.DatetimeIndex):
                    full_data.index = pd.to_datetime(full_data.index)

                # Brug pandas Timestamp for konsistens — tilpas timezone hvis index er timezone-aware
                if full_data.index.tz is not None:
                    now = pd.Timestamp.now(tz=full_data.index.tz)
                else:
                    now = pd.Timestamp.now()

                # Bestem cutoff ved hjælp af pandas DateOffset eller Timedelta
                if requested_period == "1d":
                    cutoff_date = now - pd.Timedelta(days=1)
                elif requested_period == "1wk":
                    cutoff_date = now - pd.Timedelta(weeks=1)
                elif requested_period == "1mo":
                    cutoff_date = now - pd.Timedelta(days=30)
                elif requested_period == "3mo":
                    cutoff_date = now - pd.Timedelta(days=90)
                elif requested_period == "6mo":
                    cutoff_date = now - pd.Timedelta(days=180)
                elif requested_period == "1y":
                    cutoff_date = now - pd.Timedelta(days=365)
                elif requested_period == "3y":
                    cutoff_date = now - pd.Timedelta(days=365*3)
                elif requested_period == "5y":
                    cutoff_date = now - pd.Timedelta(days=365*5)
                elif requested_period == "10y":
                    cutoff_date = now - pd.Timedelta(days=365*10)
                else:
                    cutoff_date = now - pd.Timedelta(days=180)

                print(f"Debug: Filtrerer data fra {cutoff_date} til {now}")

                # Filtrer data - brug .loc og copy for at undgå SettingWithCopyWarning
                data = full_data.loc[full_data.index >= cutoff_date].copy()
                print(f"Debug: Filtrerede data til {timespan} ({len(data)} datapunkter af {len(full_data)})")
            else:
                data = full_data.copy()
                print(f"Debug: Bruger fuldt datasæt (max)")

            print(f"Debug: get_stock_data returnerer {len(data)} datapunkter for {timespan}. Kolonner: {list(data.columns)}")
            return data, ticker_long

        except YFRateLimitError:
            print(f"Debug: Rate limit nået for {ticker}: Venter {2 ** attempt} sekunder...")
            time.sleep(2 ** attempt)
        except Exception as e:
            print(f"Debug: Fejl ved hentning af data for {ticker}: {e}")
            return pd.DataFrame(), ticker

    print(f"Debug: Kunne ikke hente data for {ticker} efter flere forsøg.")
    return pd.DataFrame(), ticker

def load_tickers():
    print(f"Debug: load_tickers kaldt")
    if os.path.exists(ticker_file):
        try:
            with open(ticker_file, 'r') as file:
                tickers = json.load(file)
                if isinstance(tickers, list):
                    tickers = {ticker[0]: ticker[1] for ticker in tickers}
                print(f"Debug: Tickers indlæst fra {ticker_file}: {list(tickers.keys())}")
                return tickers
        except Exception as e:
            print(f"Debug: Fejl ved indlæsning af {ticker_file}: {e}")
    print(f"Debug: Ingen tickers fundet i {ticker_file}. Returnerer tomt dictionary.")
    return {}

def save_tickers(tickers):
    print(f"Debug: save_tickers kaldt med tickers: {list(tickers.keys())}")
    for attempt in range(3):
        try:
            with open(ticker_file, 'w') as file:
                tickers = {normalize_ticker(ticker): company for ticker, company in tickers.items()}
                json.dump(tickers, file, indent=4)
            print(f"Debug: Tickers gemt i {ticker_file}: {list(tickers.keys())}")
            return
        except IOError as e:
            print(f"Debug: Forsøg {attempt + 1}/3: Fejl ved gemning af tickers i {ticker_file}: {e}. Tjek tilladelser.")
            time.sleep(1)
    print(f"Debug: Kunne ikke gemme tickers i {ticker_file} efter flere forsøg.")

def load_preferences():
    print(f"Debug: load_preferences kaldt")
    default_preferences = {
        "trend_days": [5, 10, 20, 50, 100, 200],
        "bollinger": False,
        "timespan": "1y",
        "show_legends": False,
        "language": "en",
        "candlestick": True,
        "last_ticker": "TSLA"
    }

    if os.path.exists(preferences_file):
        try:
            with open(preferences_file, 'r') as file:
                preferences = json.load(file)
                for key, value in default_preferences.items():
                    preferences.setdefault(key, value)
                preferences["last_ticker"] = normalize_ticker(preferences.get("last_ticker", "TSLA"))
                print(f"Debug: Præferencer indlæst fra {preferences_file}: {preferences}")
                return preferences
        except (json.JSONDecodeError, ValueError, IOError) as e:
            print(f"Debug: Fejl ved indlæsning af {preferences_file}: {e}. Opretter ny fil med standardpræferencer.")
            save_preferences(default_preferences)
            return default_preferences
    else:
        print(f"Debug: {preferences_file} findes ikke. Opretter ny fil med standardpræferencer.")
        save_preferences(default_preferences)
        return default_preferences

def save_preferences(preferences):
    print(f"Debug: save_preferences kaldt med præferencer: {preferences}")
    validated_preferences = preferences.copy()
    valid_trend_days = [5, 10, 20, 50, 100, 200]

    # Valider trend_days
    validated_preferences["trend_days"] = [
        int(day) for day in validated_preferences.get("trend_days", valid_trend_days)
        if isinstance(day, (int, str)) and str(day).isdigit() and int(day) in valid_trend_days
    ]
    if not validated_preferences["trend_days"]:
        validated_preferences["trend_days"] = valid_trend_days
        print(f"Debug: trend_days var tom eller ugyldig. Bruger standard: {valid_trend_days}")

    # Valider last_ticker
    validated_preferences["last_ticker"] = normalize_ticker(validated_preferences.get("last_ticker", "TSLA"))
    if not validated_preferences["last_ticker"]:
        validated_preferences["last_ticker"] = "TSLA"
        print(f"Debug: last_ticker var tom eller ugyldig. Bruger standard: TSLA")

    print(f"Debug: Forsøger at gemme validerede præferencer i {preferences_file}: {validated_preferences}")
    for attempt in range(3):
        try:
            with open(preferences_file, 'w') as file:
                json.dump(validated_preferences, file, indent=4)
            print(f"Debug: Præferencer gemt succesfuldt i {preferences_file}: {validated_preferences}")
            return
        except PermissionError as e:
            print(f"Debug: Forsøg {attempt + 1}/3: Manglende tilladelser til at skrive til {preferences_file}: {e}")
            time.sleep(1)
        except IOError as e:
            print(f"Debug: Forsøg {attempt + 1}/3: IOError ved gemning af præferencer i {preferences_file}: {e}")
            time.sleep(1)
        except Exception as e:
            print(f"Debug: Forsøg {attempt + 1}/3: Uventet fejl ved gemning af præferencer: {e}")
            time.sleep(1)
    print(f"Debug: Kunne ikke gemme præferencer i {preferences_file} efter flere forsøg.")

def scan_for_buy_signals():
    """
    Scanner alle tickers i tickers.json for aktive købssignaler.
    Udskriver en pæn liste til terminalen.
    """
    print("\n" + "="*60)
    print("STARTER MARKEDS-SCANNING FOR KØBSSIGNALER")
    print("="*60 + "\n")

    tickers_map = load_tickers()
    results = []

    for ticker in tickers_map:
        try:
            # Hent data (bruger 6mo for at være sikker på nok data til beregning)
            # Vi ignorerer navnet her, da vi har det fra tickers_map
            df, _ = get_stock_data(ticker, "6mo")

            if df is None or df.empty or 'signal' not in df:
                continue

            # Tjek sidste række for signal
            last = df.iloc[-1]

            if last['signal'] == 1:
                print(f">>> MATCH: {ticker} har et aktivt KØB signal!")
                results.append({
                    'ticker': ticker,
                    'price': last['Close'],
                    'extension': last.get('extension_pc', 0),
                    'breakout': last.get('near_breakout', False),
                    'volume': last.get('high_volume', False)
                })
        except Exception as e:
            print(f"Fejl ved scanning af {ticker}: {e}")

    print("\n" + "="*60)
    print(f"SCANNING RESULTAT: {len(results)} AKTIER MED KØBSSIGNAL")
    print("-" * 60)
    print(f"{'TICKER':<10} {'PRIS':<10} {'EXT %':<10} {'BREAKOUT':<10} {'VOLUMEN':<10}")
    print("-" * 60)

    for res in results:
        brk = "JA" if res['breakout'] else "Nej"
        vol = "HØJ" if res['volume'] else "Normal"
        print(f"{res['ticker']:<10} {res['price']:<10.2f} {res['extension']:<10.2f} {brk:<10} {vol:<10}")
    print("="*60 + "\n")

    return results