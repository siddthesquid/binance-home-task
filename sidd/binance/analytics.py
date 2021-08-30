import re
from copy import deepcopy
from time import sleep
from typing import Iterable, Optional

from sidd.binance.connector.exchange import get_exchange

# A field regex could take any number of matches. These regex's should be paired with a function that evaluates
# these matches into another function that routes the field to a certain value in the Symbol data model. The tuples
# below represent
# (name, regex, function to value, can order by field?, can use for delta analysis?)
FIELD_FUNCTIONS = [
    ("symbol", r"symbol", lambda matches: lambda symbol: symbol.symbol, False, False),
    (
        "base_asset",
        r"base_asset",
        lambda matches: lambda symbol: symbol.base_asset,
        True,
        True,
    ),
    (
        "quote_asset",
        r"quote_asset",
        lambda matches: lambda symbol: symbol.quote_asset,
        True,
        True,
    ),
    (
        "volume",
        r"volume",
        lambda matches: lambda symbol: symbol.ticker_24hr(bulk_request=True).volume,
        True,
        True,
    ),
    (
        "trades",
        r"trades",
        lambda matches: lambda symbol: symbol.ticker_24hr(bulk_request=True).trades,
        True,
        True,
    ),
    (
        "bid_price",
        r"bid_price",
        lambda matches: lambda symbol: symbol.ticker_24hr(bulk_request=True).bid_price,
        True,
        True,
    ),
    (
        "ask_price",
        r"ask_price",
        lambda matches: lambda symbol: symbol.ticker_24hr(bulk_request=True).ask_price,
        True,
        True,
    ),
    (
        "spread",
        r"spread",
        lambda matches: lambda symbol: symbol.ticker_24hr(bulk_request=True).spread,
        True,
        True,
    ),
    (
        "order_book_bid_total_value[<number of levels>]",
        r"order_book_bid_total_value\[(\d+)\]",
        lambda matches: lambda symbol: symbol.depth(
            num_levels=int(matches[0])
        ).total_notional_value_of_bids(),
        False,
        True,
    ),
    (
        "order_book_ask_total_value[<number of levels>]",
        r"order_book_ask_total_value\[(\d+)\]",
        lambda matches: lambda symbol: symbol.depth(
            num_levels=int(matches[0])
        ).total_notional_value_of_asks(),
        False,
        True,
    ),
]

# An order regex starts with a field as defined by FIELD_FUNCTIONS and can end in [asc] or [desc] for
# ascending or descending order. The regex's should be paired with a function that evaluates the matches
# (the field from from the regex) into a tuple of the key symbols should be sorted by and whether the sort
# should be reversed (it is ascending order, by default).
ORDER_FUNCTIONS = [
    (r"^(.*)\[asc\]$", lambda matches: (_get_field_function(matches[0]), False)),
    (r"^(.*)\[desc\]$", lambda matches: (_get_field_function(matches[0]), True)),
    (r"^(.*)$", lambda matches: (_get_field_function(matches[0]), False)),
]


class DeltaTracker:
    def __init__(self, analysis_function, delta_fields, interval_ms):
        self.analysis_function = analysis_function
        self.delta_fields = delta_fields
        self.interval_s = interval_ms / 1000
        self.current_values = {}
        self.keep_running = True

    def start(self):
        while self.keep_running:
            current_symbol_analysis = self.analysis_function()
            for symbol_data in current_symbol_analysis:
                symbol = symbol_data["symbol"]
                deltas = {
                    delta_field: abs(
                        symbol_data[delta_field]
                        - self.current_values[symbol][delta_field]
                    )
                    if symbol in self.current_values
                    else None
                    for delta_field in self.delta_fields
                }
                symbol_data_with_delta = deepcopy(symbol_data)
                symbol_data_with_delta["deltas"] = deltas
                yield symbol_data_with_delta
            self.current_values = {
                symbol_data["symbol"]: symbol_data
                for symbol_data in current_symbol_analysis
            }
            sleep(self.interval_s)

    def stop(self):
        self.keep_running = False


def _get_field_function(field):
    for (_, possible_field, function, _, _) in FIELD_FUNCTIONS:
        matcher = re.compile(possible_field)
        matches = matcher.match(field)
        if matches:
            return function(matches.groups())
    raise ValueError(
        f'"{field}" is not a valid field. Must be one of {[name for (name, _, _, _, _) in FIELD_FUNCTIONS]}'
    )


def _get_order(field):
    for (possible_field, function) in ORDER_FUNCTIONS:
        matcher = re.compile(possible_field)
        matches = matcher.match(field)
        if matches:
            return function(matches.groups())


def symbol_analysis(
    quote_assets: Optional[Iterable[str]] = None,
    base_assets: Optional[Iterable[str]] = None,
    order_by: Optional[str] = None,
    limit: int = 5,
    fields: Optional[Iterable[str]] = None,
):
    binance = get_exchange()
    symbols = binance.symbols(base_assets=base_assets, quote_assets=quote_assets)
    if order_by:
        ordering = _get_order(order_by)
        symbols = sorted(symbols, key=ordering[0], reverse=ordering[1])
    symbols = symbols[:limit]
    fields = fields or ["symbol"]
    return [
        {field: _get_field_function(field)(symbol) for field in fields}
        for symbol in symbols
    ]


def get_delta_tracker(
    quote_assets: Optional[Iterable[str]] = None,
    base_assets: Optional[Iterable[str]] = None,
    order_by: Optional[str] = None,
    limit: int = 5,
    fields: Optional[Iterable[str]] = None,
    delta_fields: Optional[Iterable[str]] = None,
    interval_ms: int = 60000,
):
    fields = fields or ["symbol"]
    if "symbol" not in fields:
        fields.insert(0, "symbol")
    for delta_field in delta_fields:
        if delta_field not in fields:
            fields.append(delta_field)

    def baked_symbol_analysis():
        return symbol_analysis(quote_assets, base_assets, order_by, limit, fields)

    return DeltaTracker(baked_symbol_analysis, delta_fields, interval_ms)
