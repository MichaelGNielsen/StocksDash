import yfinance as yf
import json
import pandas as pd
import argparse

# Opsæt kommandolinjeparametre
parser = argparse.ArgumentParser(description="Analysér aktier og giv køb/hold/salg-anbefalinger.")
parser.add_argument("--debug", action="store_true", help="Vis detaljeret debug-information.")
parser.add_argument("--lang", choices=["da", "en"], default="da", help="Sprog for output (da: dansk, en: engelsk).")
args = parser.parse_args()

# Oversættelse af scores til tekst
SCORE_TEXT = {
    "da": {5: "Stærk Køb", 4: "Køb", 3: "Hold", 2: "Sælg", 1: "Stærk Sælg"},
    "en": {5: "Strong Buy", 4: "Buy", 3: "Hold", 2: "Sell", 1: "Strong Sell"}
}

# Indlæs tickers fra JSON
try:
    with open("tickers.json", "r", encoding="utf-8") as f:
        tickers = json.load(f)
except FileNotFoundError:
    print("Fejl: tickers.json blev ikke fundet.")
    exit(1)
except json.JSONDecodeError:
    print("Fejl: tickers.json er ikke i gyldigt JSON-format.")
    exit(1)

# Vis tickers, hvis debug er aktiveret
if args.debug:
    print("Tickers fra tickers.json:")
    for ticker, name in tickers.items():
        print(f" - {ticker}: {name}")

def analyze_stock(ticker):
    try:
        # Download data med auto_adjust=True for at matche stocks.py
        df = yf.download(ticker, period="6mo", interval="1d", progress=False, auto_adjust=True)
        
        # Valider data
        if df.empty:
            if args.debug:
                print(f"Fejl ved {ticker}: Ingen data returneret.")
            return None
        if len(df) < 60:
            if args.debug:
                print(f"Fejl ved {ticker}: Kun {len(df)} datapunkter, kræver mindst 60.")
            return None
        
        # Håndter multi-index kolonner
        if isinstance(df.columns, pd.MultiIndex):
            if args.debug:
                print(f"Multi-index DataFrame detekteret for {ticker}. Kolonner: {df.columns}")
            df.columns = [col[0] for col in df.columns]
            if args.debug:
                print(f"Fladtrykte kolonner for {ticker}: {list(df.columns)}")
        elif args.debug:
            print(f"Kolonner for {ticker}: {list(df.columns)}")

        # Valider kolonner
        required_columns = ['Close']
        if not all(col in df.columns for col in required_columns):
            if args.debug:
                print(f"Fejl ved {ticker}: Mangler kolonner. Tilgængelige kolonner: {list(df.columns)}")
            return None

        # Beregn 50-dages glidende gennemsnit med min_periods=1 for at matche stocks.py
        df['MA50'] = df['Close'].rolling(window=50, min_periods=1).mean()

        # Tjek for NaN
        if df[['Close', 'MA50']].iloc[-2:].isna().any().any():
            if args.debug:
                print(f"Fejl ved {ticker}: Manglende eller ugyldige data i Close eller MA50.")
            return None

        # Vis seneste data, hvis debug er aktiveret
        if args.debug:
            print(f"Seneste data for {ticker}:\n{df[['Close', 'MA50']].tail(3)}")

        price = df['Close'].iloc[-1]
        prev_price = df['Close'].iloc[-2]
        ma50 = df['MA50'].iloc[-1]
        prev_ma50 = df['MA50'].iloc[-2]

        ma_trending_up = ma50 > prev_ma50
        price_above_ma = price > ma50

        # Tjek 10-dages trend
        recent_closes = df['Close'].iloc[-10:]
        if len(recent_closes) < 10:
            if args.debug:
                print(f"Fejl ved {ticker}: Kun {len(recent_closes)} datapunkter i de sidste 10 dage.")
            return None
        recent_trend_up = all(recent_closes.iloc[i] < recent_closes.iloc[i + 1] for i in range(len(recent_closes) - 1))

        # Scoring model
        if price_above_ma and ma_trending_up and recent_trend_up:
            return 5  # Stærk Køb
        elif price_above_ma and ma_trending_up:
            return 4  # Køb
        elif price < ma50 and prev_price > prev_ma50:
            return 2  # Sælg
        elif price < ma50 and not ma_trending_up:
            return 1  # Stærk Sælg
        else:
            return 3  # Hold

    except Exception as e:
        if args.debug:
            print(f"Fejl ved {ticker}: {str(e)} (type: {type(e).__name__})")
        return None

results = []

# Gennemgå alle aktier
for ticker, name in tickers.items():
    if args.debug:
        print(f"Analyserer {ticker} ({name})...")
    score = analyze_stock(ticker)
    if score is None:
        if args.debug:
            print(f"Ingen score for {ticker}: Analyse mislykkedes.")
    else:
        results.append({
            "Ticker": ticker,
            "Name": name,
            "Score": score,
            "ScoreText": SCORE_TEXT[args.lang][score]
        })

# Sortér efter score (højeste først)
results.sort(key=lambda x: x["Score"], reverse=True)

# Udskriv resultater
print("\nResultater:")
if not results:
    print("Ingen aktier blev analyseret succesfuldt.")
else:
    for r in results:
        print(f"{r['Score']} - {r['Ticker']} - {r['Name']} - {r['ScoreText']}")

# Gem til CSV
df_out = pd.DataFrame(results)
df_out.to_csv("stock_scores.csv", index=False, encoding="utf-8")
print("Resultater gemt til stock_scores.csv")