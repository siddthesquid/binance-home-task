import logging
import threading
import traceback

import markdown
import simplejson as json
from flask import Flask, request
from prometheus_client import Gauge, generate_latest

from sidd.binance.analytics import get_delta_tracker
from sidd.binance.cmdinterface import get_parser

app = Flask(__name__)
spread_delta_metric = Gauge(
    "spread_delta", "Spread delta", ["symbol", "base_asset", "quote_asset"]
)

gunicorn_error_logger = logging.getLogger("gunicorn.error")
app.logger.handlers.extend(gunicorn_error_logger.handlers)
app.logger.setLevel(logging.DEBUG)
logging.basicConfig(
    level=gunicorn_error_logger.level, handlers=gunicorn_error_logger.handlers
)


# Thread for answering question 6 - up to date prometheus metrics for most traded USDT quoted currencies. This metric
# specifically tracks how the spread changes for the top 5 most traded USDT securities
class USDTSpreadDeltaThread(threading.Thread):
    def run(self):
        delta_tracker = get_delta_tracker(
            quote_assets=["USDT"],
            order_by="trades[desc]",
            limit=5,
            fields=["symbol", "base_asset", "quote_asset", "trades", "spread"],
            delta_fields=["spread"],
            interval_ms=10000,
        )
        for symbol_data in delta_tracker.start():
            symbol = symbol_data["symbol"]
            base_asset = symbol_data["base_asset"]
            quote_asset = symbol_data["quote_asset"]
            spread = symbol_data["deltas"]["spread"]
            if spread is not None:
                spread_delta_metric.labels(
                    symbol=symbol, base_asset=base_asset, quote_asset=quote_asset
                ).set(spread)


USDTSpreadDeltaThread().start()


@app.route("/")
def index():
    readme_file = open("README.md", "r")
    md_template_string = markdown.markdown(
        readme_file.read(), extensions=["fenced_code"]
    )

    return md_template_string


@app.route("/symbol_analysis")
def symbols():
    command = ["symbol_analysis"]
    raw_quote_assets = request.args.get("quote_assets")
    raw_base_assets = request.args.get("base_assets")
    raw_order_by = request.args.get("order_by")
    raw_limit = request.args.get("limit", default=5)
    raw_fields = request.args.get("fields")
    if raw_quote_assets:
        command += ["-q", raw_quote_assets]
    if raw_base_assets:
        command += ["-b", raw_base_assets]
    if raw_order_by:
        command += ["-o", raw_order_by]
    if raw_limit:
        command += ["-l", str(raw_limit)]
    if raw_fields:
        command += ["-f", raw_fields]
    parser = get_parser()
    args = parser.parse_args(command)
    return json.dumps(args.handler(args))


@app.route("/question/<int:question>")
def questions(question):
    command = ["binance_question"]
    if question == 5:
        raise ValueError(
            "Any request with infinite generation is not supported at this time."
        )
    command += [str(question)]
    parser = get_parser()
    args = parser.parse_args(command)
    return json.dumps(args.handler(args))


@app.route("/health")
def health():
    return "Looking good!", 200


@app.route("/metrics")
def metrics():
    return generate_latest()


@app.errorhandler(ValueError)
def handle_value_error(e: Exception):
    logging.error(traceback.format_exc())
    return {"error_type": "ValueError", "message": str(e)}, 400


@app.errorhandler(Exception)
def handle_exception(e: Exception):
    logging.error(traceback.format_exc())
    return {"method": str(e)}, 400
