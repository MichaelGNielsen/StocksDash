# python main.py --debug
# https://imgur.com/a/R8BMBLa


import argparse
import sys
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
            scan_for_buy_signals()
    else:
        app = create_app()
        app.run(debug=args.debug, host='0.0.0.0')