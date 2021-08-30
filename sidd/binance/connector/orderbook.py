from decimal import Decimal

from sidd.binance.connector.clientadapter import SafeClient

REPR_LIMIT = 5
VALID_NUM_LEVELS = [5, 10, 20, 50, 100, 500, 1000, 5000]


class OrderBookCache:
    def __init__(self):
        self.cache = {}

    def get(self, symbol, num_levels, cached=True):
        if not (
            cached
            and symbol in self.cache
            and self.cache[symbol].num_levels >= num_levels
        ):
            self.fetch(symbol, num_levels)
        return self.cache[symbol].with_num_levels(num_levels)

    def fetch(self, symbol, num_levels):
        client = SafeClient()
        if num_levels > VALID_NUM_LEVELS[-1]:
            raise ValueError(
                f"Given {num_levels} levels for order book request, but only up to {VALID_NUM_LEVELS[-1]} are allowed."
            )
        num_levels = list(
            filter(lambda valid_level: valid_level >= num_levels, VALID_NUM_LEVELS)
        )[0]
        raw_depth = client.depth(symbol, limit=num_levels)
        self.cache[symbol] = OrderBook.from_raw_input(raw_depth, num_levels)


class OrderBook:
    def __init__(self, bids, asks, num_levels):
        self.bids = bids
        self.asks = asks
        self.num_levels = num_levels

    @classmethod
    def from_raw_input(cls, raw_depth, num_levels):
        return OrderBook(
            [Order(raw_bid) for raw_bid in raw_depth["bids"]],
            [Order(raw_ask) for raw_ask in raw_depth["asks"]],
            num_levels,
        )

    def with_num_levels(self, num_levels):
        if num_levels > self.num_levels:
            raise IndexError(
                f"Requested {num_levels} from this order book, but only {self.num_levels} exist."
            )
        return OrderBook(self.bids[:num_levels], self.asks[:num_levels], num_levels)

    def total_notional_value_of_bids(self):
        return _total_notional_value_of_side(self.bids)

    def total_notional_value_of_asks(self):
        return _total_notional_value_of_side(self.asks)

    def __repr__(self):
        bids_repr = self.bids[:REPR_LIMIT]
        asks_repr = self.asks[:REPR_LIMIT]
        bids_truncated = "(truncated)" if len(self.bids) > REPR_LIMIT else ""
        asks_truncated = "(truncated)" if len(self.asks) > REPR_LIMIT else ""
        return f"<bids={bids_repr}{bids_truncated} asks={asks_repr}{asks_truncated}>"


class Order:
    def __init__(self, raw_order):
        self.price = Decimal(raw_order[0])
        self.quantity = Decimal(raw_order[1])

    def notional_value(self):
        return self.price * self.quantity

    def __repr__(self):
        return f"<price={self.price} qty={self.quantity}>"


def _total_notional_value_of_side(orders):
    return sum([order.notional_value() for order in orders])
