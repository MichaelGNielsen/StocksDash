# python main.py --debug
# https://imgur.com/a/R8BMBLa


import argparse
import sys
import requests
from app import create_app
from data import scan_for_buy_signals

class Tee:
    """Hjælpe-klasse der skriver til både terminal og fil samtidig"""
    def __init__(self, name, mode='w'):
        self.file = open(name, mode, encoding='utf-8')
        self.stdout = sys.stdout
        sys.stdout = self

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        sys.stdout = self.stdout
        self.file.close()

    def write(self, data):
        self.file.write(data)
        self.stdout.write(data)

    def flush(self):
        self.file.flush()
        self.stdout.flush()

def send_notification(results):
    """Sender en notifikation til din telefon via ntfy.sh"""
    if not results:
        return

    # VIGTIGT: Ret dette emne til noget unikt for dig, så andre ikke ser dine beskeder!
    # Du abonnerer på dette emne i ntfy appen på din telefon.
    topic = "stocks_dash_mgn_alerts"

    count = len(results)
    title = f"🚀 {count} Aktier med Købssignal"

    # Byg besked-kroppen
    lines = []
    for res in results:
        symbol = res['ticker']
        price = res['price']
        extras = []
        if res.get('breakout'): extras.append("Breakout")
        if res.get('volume'): extras.append("Høj Vol")

        line = f"{symbol}: {price:.2f}"
        if extras:
            line += f" ({', '.join(extras)})"
        lines.append(line)

    message = "\n".join(lines)

    try:
        requests.post(
            f"https://ntfy.sh/{topic}",
            data=message.encode('utf-8'),
            headers={
                "Title": title.encode('utf-8'),
                "Tags": "chart_with_upwards_trend,moneybag",
            }
        )
        print(f"\n>>> Notifikation sendt til https://ntfy.sh/{topic}")
    except Exception as e:
        print(f"\n>>> Kunne ikke sende notifikation: {e}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Stock Analysis Dashboard")
    parser.add_argument('--debug', action='store_true', help="Run in debug mode")
    parser.add_argument('--scan', action='store_true', help="Scan all tickers for BUY signals")
    args = parser.parse_args()

    if args.scan:
        with Tee("scan_results.txt"):
            print("\nFORKLARING AF KOLONNER:")
            print("-" * 60)
            print(f"{'TICKER':<10} Aktiesymbol")
            print(f"{'PRIS':<10} Seneste lukkekurs")
            print(f"{'EXT %':<10} Hvor meget prisen er 'strakt' over SMA 20 i %")
            print(f"{'BREAKOUT':<10} Er prisen brudt igennem 20-dages toppen? (JA/Nej)")
            print(f"{'VOLUMEN':<10} Er handelsvolumen usædvanlig høj? (HØJ/Normal)")
            print("-" * 60 + "\n")

            results = scan_for_buy_signals()
            send_notification(results)
    else:
        app = create_app()
        app.run(debug=args.debug, host='0.0.0.0')