import yfinance as yf
import pandas as pd
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

def get_stock_data(ticker, timespan):
    ticker = normalize_ticker(ticker)
    print(f"Debug: get_stock_data kaldt med ticker: {ticker}, timespan: {timespan}")
    stock = yf.Ticker(ticker)

    period_map = {
        "1d": "1d", "1w": "1wk", "1mo": "1mo", "3mo": "3mo",
        "6mo": "6mo", "1y": "1y", "3y": "3y", "5y": "5y",
        "10y": "10y", "max": "max"
    }

    period = period_map.get(timespan, "6mo")
    print(f"Debug: get_stock_data bruger period: {period}")

    for attempt in range(3):
        try:
            data = stock.history(period=period)
            ticker_long = get_long_name(ticker)
            if data.empty:
                print(f"Debug: Tomt datasæt returneret for {ticker} med period {period}")
                return pd.DataFrame(), ticker_long
            required_columns = ['Close', 'Volume', 'Open', 'High', 'Low']
            missing_columns = [col for col in required_columns if col not in data]
            if missing_columns:
                print(f"Debug: Manglende kolonner i data for {ticker}: {missing_columns}")
                return pd.DataFrame(), ticker_long
            print(f"Debug: get_stock_data hentede data for {ticker}. Datalængde: {len(data)}, Kolonner: {list(data.columns)}")
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
        "timespan": "6mo",
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