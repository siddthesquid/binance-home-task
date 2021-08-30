from decimal import Decimal

from sidd.binance.connector.clientadapter import SafeClient


class Ticker24HrCache:
    def __init__(self):
        self.cache = {}

    def get(self, symbol, cached=True, bulk_request=False):
        if not (cached and symbol in self.cache):
            fetch_symbol = None if bulk_request else symbol
            self.fetch(fetch_symbol)
        return self.cache[symbol]

    def fetch(self, symbol=None):
        client = SafeClient()
        raw_tickers_24hr = client.ticker_24hr(symbol)
        if symbol:
            raw_tickers_24hr = [raw_tickers_24hr]
        self.cache.update(
            {
                raw_symbol_ticker_24hr["symbol"]: Ticker24Hr.from_raw_input(
                    raw_symbol_ticker_24hr
                )
                for raw_symbol_ticker_24hr in raw_tickers_24hr
            }
        )

    def __getitem__(self, symbol):
        return self.get(symbol, cached=True, bulk_request=False)


class Ticker24Hr:
    def __init__(self, volume, trades, bid_price, ask_price):
        self.volume = volume
        self.trades = trades
        self.bid_price = bid_price
        self.ask_price = ask_price
        self.spread = ask_price - bid_price

    @classmethod
    def from_raw_input(cls, raw_symbol_ticker_24hr):
        return Ticker24Hr(
            Decimal(raw_symbol_ticker_24hr["volume"]),
            int(raw_symbol_ticker_24hr["count"]),
            Decimal(raw_symbol_ticker_24hr["bidPrice"]),
            Decimal(raw_symbol_ticker_24hr["askPrice"]),
        )

    def __repr__(self):
        return f"<vol={self.volume} trades={self.trades} bbo={self.bid_price}/{self.ask_price}>"
