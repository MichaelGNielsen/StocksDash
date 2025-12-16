# python main.py --debug
# https://imgur.com/a/R8BMBLa


import argparse
from app import create_app

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Stock Analysis Dashboard")
    parser.add_argument('--debug', action='store_true', help="Run in debug mode")
    args = parser.parse_args()

    app = create_app()
    app.run(debug=args.debug)