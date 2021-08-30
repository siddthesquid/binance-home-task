from collections import defaultdict

from sidd.binance.connector.clientadapter import SafeClient
from sidd.binance.connector.orderbook import OrderBookCache
from sidd.binance.connector.ticker24hr import Ticker24HrCache


def get_exchange():
    return IndexedExchangeInfo()


class IndexedExchangeInfo:
    def __init__(self):
        client = SafeClient()
        raw_exchange_info = client.exchange_info()
        self._symbol_index = dict()
        self._base_asset_index = defaultdict(list)
        self._quote_asset_index = defaultdict(list)
        for raw_symbol_info in raw_exchange_info["symbols"]:
            symbol_info = SymbolData(raw_symbol_info, self)
            self._symbol_index[symbol_info.symbol] = symbol_info
            self._base_asset_index[symbol_info.base_asset].append(symbol_info)
            self._quote_asset_index[symbol_info.quote_asset].append(symbol_info)

        self.ticker_24hr_service = Ticker24HrCache()
        self.order_book_service = OrderBookCache()

    def symbols(self, quote_assets=None, base_assets=None):
        quote_asset_filtered_symbols = set(
            [
                symbol_data
                for quote_asset in quote_assets
                for symbol_data in self._quote_asset_index[quote_asset]
            ]
            if quote_assets is not None
            else self._symbol_index.values()
        )
        if len(quote_asset_filtered_symbols) == 0:
            raise ValueError(
                f"No symbols found with the provided quote asset filter - {quote_assets}."
            )
        base_asset_filtered_symbols = set(
            [
                symbol_data
                for base_asset in base_assets
                for symbol_data in self._base_asset_index[base_asset]
            ]
            if base_assets is not None
            else self._symbol_index.values()
        )
        if len(base_asset_filtered_symbols) == 0:
            raise ValueError(
                f"No symbols found with the provided base asset filter - {base_assets}."
            )
        return list(quote_asset_filtered_symbols & base_asset_filtered_symbols)

    def __getitem__(self, symbol):
        return self._symbol_index[symbol]

    def __repr__(self):
        return str(self._symbol_index.items())


class SymbolData:
    def __init__(self, raw_symbol_data, exchange):
        self.symbol = raw_symbol_data["symbol"]
        self.base_asset = raw_symbol_data["baseAsset"]
        self.quote_asset = raw_symbol_data["quoteAsset"]
        self.exchange = exchange

    def depth(self, num_levels=100, cached=True):
        return self.exchange.order_book_service.get(
            self.symbol, num_levels, cached=cached
        )

    def ticker_24hr(self, cached=True, bulk_request=False):
        return self.exchange.ticker_24hr_service.get(self.symbol, cached, bulk_request)

    def __hash__(self):
        return hash(self.symbol)

    def __eq__(self, other_symbol):
        return self.symbol == other_symbol.symbol

    def __repr__(self):
        return f"<{self.symbol} base={self.base_asset} quote={self.quote_asset}>"
