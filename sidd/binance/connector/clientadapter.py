import logging

from binance.spot import Spot

URLS = [
    "https://api.binance.com",
    "https://api1.binance.com",
    "https://api2.binance.com",
    "https://api3.binance.com",
]
LIMIT_LABEL = "x-mbx-used-weight"
LIMIT = 1200  # Should really try to get this dynamically
WARNING_THRESHOLD = 0.7


class SafeClient(Spot):
    def __init__(self):
        super().__init__(show_limit_usage=True, base_url=URLS[0])

    def query(self, url_path, payload=None):
        logging.info(f"Calling url_path={url_path} with payload={payload}.")
        response = super().query(url_path, payload)
        return handle_limits_from_response(response)


def handle_limits_from_response(response):
    usage = int(response["limit_usage"][LIMIT_LABEL])
    log_func = logging.info
    if usage / LIMIT > WARNING_THRESHOLD:
        log_func = logging.warning
    log_func(f"API usage is at usage={usage} of limit={LIMIT}.")
    return response["data"]
