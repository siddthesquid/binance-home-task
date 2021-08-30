import argparse
import sys

from sidd.binance.analytics import FIELD_FUNCTIONS, get_delta_tracker, symbol_analysis


# Overriding error so that the server doesn't crash due to bad commands
class NonExitingArgumentParser(argparse.ArgumentParser):
    def error(self, message: str):
        exc = sys.exc_info()[1]
        raise Exception(exc)


def get_parser():
    parser = NonExitingArgumentParser(
        prog="binance_analytics.py",
        description="Perform analysis on Binance financial data.",
    )
    parser.add_argument(
        "-p",
        "--pretty",
        action="store_true",
        default=False,
        help="Pretty print output.",
    )
    argparse.ArgumentParser()
    subparsers = parser.add_subparsers(help="Choose an action.")
    add_symbol_analysis_subparser(subparsers)
    add_delta_analysis_subparser(subparsers)
    add_question_subparser(subparsers)
    return parser


def add_symbol_analysis_subparser(subparsers):
    symbol_analysis_parser = subparsers.add_parser(
        "symbol_analysis",
        help="Order and display calculated fields on any symbol from Binance.",
    )
    _add_symbol_analysis_arguments(symbol_analysis_parser)
    symbol_analysis_parser.set_defaults(handler=handle_symbol_analysis)


def add_delta_analysis_subparser(subparsers):
    delta_analysis_parser = subparsers.add_parser(
        "delta_analysis", help="Track changes in various fields for any Binance symbol."
    )
    _add_symbol_analysis_arguments(delta_analysis_parser)
    possible_delta_fields = [
        field for (field, _, _, _, can_delta) in FIELD_FUNCTIONS if can_delta
    ]
    delta_analysis_parser.add_argument(
        "-d",
        "--delta_fields",
        type=str,
        required=True,
        help=f"Fields to perform delta analysis for. Accepted values are {possible_delta_fields}",
    )
    delta_analysis_parser.add_argument(
        "-i",
        "--interval",
        type=int,
        default=60000,
        help="Interval (in milliseconds) between re-fetching data from Binance to do delta comparisons with.",
    )
    delta_analysis_parser.set_defaults(handler=handle_delta_analysis)


def add_question_subparser(subparsers):
    question_parser = subparsers.add_parser(
        "binance_question",
        help="Get quick answers to any of the Binance interview questions with pre-plugged in solutions",
    )
    question_parser.add_argument(
        "question",
        type=int,
        choices=[1, 2, 3, 4, 5],
        help="Choose which question whose solution you want displayed from the output of this command.",
    )
    question_parser.set_defaults(handler=handle_question)


def handle_symbol_analysis(args):
    base_assets = (
        [asset.strip().upper() for asset in args.base_assets.split(",")]
        if args.base_assets
        else None
    )
    quote_assets = (
        [asset.strip().upper() for asset in args.quote_assets.split(",")]
        if args.quote_assets
        else None
    )
    order_by = args.order_by
    limit = args.limit
    fields = (
        [field.strip() for field in args.fields.split(",")] if args.fields else None
    )
    return symbol_analysis(quote_assets, base_assets, order_by, limit, fields)


def handle_delta_analysis(args):
    base_assets = (
        [asset.strip().upper() for asset in args.base_assets.split(",")]
        if args.base_assets
        else None
    )
    quote_assets = (
        [asset.strip().upper() for asset in args.quote_assets.split(",")]
        if args.quote_assets
        else None
    )
    order_by = args.order_by
    limit = args.limit
    fields = (
        [field.strip() for field in args.fields.split(",")] if args.fields else None
    )
    delta_fields = (
        [delta_field.strip() for delta_field in args.delta_fields.split(",")]
        if args.delta_fields
        else None
    )
    interval_ms = args.interval
    delta_tracker = get_delta_tracker(
        base_assets=base_assets,
        quote_assets=quote_assets,
        order_by=order_by,
        limit=limit,
        fields=fields,
        delta_fields=delta_fields,
        interval_ms=interval_ms,
    )
    return delta_tracker.start()


def handle_question(args):
    q = args.question
    if q == 1:
        return symbol_analysis(
            quote_assets=["BTC"],
            order_by="volume[desc]",
            limit=5,
            fields=["symbol", "volume"],
        )
    elif q == 2:
        return symbol_analysis(
            quote_assets=["USDT"],
            order_by="trades[desc]",
            limit=5,
            fields=["symbol", "trades"],
        )
    elif q == 3:
        return symbol_analysis(
            quote_assets=["BTC"],
            order_by="volume[desc]",
            limit=5,
            fields=[
                "symbol",
                "volume",
                "order_book_bid_total_value[200]",
                "order_book_ask_total_value[200]",
            ],
        )
    elif q == 4:
        return symbol_analysis(
            quote_assets=["USDT"],
            order_by="trades[desc]",
            limit=5,
            fields=["symbol", "trades", "spread"],
        )
    elif q == 5:
        return get_delta_tracker(
            quote_assets=["USDT"],
            order_by="trades[desc]",
            limit=5,
            fields=["symbol", "trades", "spread"],
            delta_fields=["spread"],
            interval_ms=10000,
        ).start()
    return None


def _add_symbol_analysis_arguments(subparser):
    subparser.add_argument(
        "-b",
        "--base_assets",
        type=str,
        default=None,
        help="Comma separated list. Filter symbols to those that include this asset as a base asset.",
    )
    subparser.add_argument(
        "-q",
        "--quote_assets",
        type=str,
        default=None,
        help="Comma separated list. Filter symbols to those that include this asset as a quote asset.",
    )
    possible_order_fields = [
        field for (field, _, _, can_order, _) in FIELD_FUNCTIONS if can_order
    ]
    subparser.add_argument(
        "-o",
        "--order_by",
        type=str,
        default=None,
        help=f"Order symbols by a certain feature. Accepted values are {possible_order_fields}. Ascending "
        f'order by default, but append "[asc]" or "[desc]" for ascending or descending order, respectively. '
        f'(e.g. "trades[desc]")',
    )
    subparser.add_argument(
        "-l",
        "--limit",
        type=int,
        default=5,
        help="Limit number of symbols to display/analyze. This is especially important for doing market "
        "depth queries as we may exhaust the API limit.",
    )
    possible_fields = [field for (field, _, _, _, _) in FIELD_FUNCTIONS]
    subparser.add_argument(
        "-f",
        "--fields",
        type=str,
        default=None,
        help=f"Fields to output for each selected symbol. Accepted values are {possible_fields}",
    )
