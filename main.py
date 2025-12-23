# python main.py --debug
# https://imgur.com/a/R8BMBLa


import argparse
from app import create_app
from data import scan_for_buy_signals

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Stock Analysis Dashboard")
    parser.add_argument('--debug', action='store_true', help="Run in debug mode")
    parser.add_argument('--scan', action='store_true', help="Scan all tickers for BUY signals")
    args = parser.parse_args()

    if args.scan:
        scan_for_buy_signals()
    else:
        app = create_app()
        app.run(debug=args.debug)