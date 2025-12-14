import re

def normalize_ticker(ticker):
    if not ticker:
        return ''
    ticker = ticker.upper()
    if re.search(r'\.[A-Z]{2,4}$', ticker):
        return ticker
    return ticker.replace('.', '-').upper()