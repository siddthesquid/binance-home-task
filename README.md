# Binance Analytics Tool

**Author**: Sidd Singal  
**Email**: ssingal05@gmail.com

This assignment was done as part of a take-home assessment for the Binance interview process. The goal is to use the Binance public API to answer/complete several tasks. In general, there are a few ways of retrieving the answers to these questions.

 * Accessing my hosted server via `https://api.binance.siddsingal.com`  
 * Running the server locally and performing the same queries via `localhost:8000`
 * Using the provided scripts to calculate the answers without having to run a server  

All possible methods of solving the questions will be provided below.

- [Binance Analytics Tool](#binance-analytics-tool)
- [General Stack](#general-stack)
- [https://api.binance.siddsingal.com](#httpsapibinancesiddsingalcom)
    - [`/`](#)
    - [`/health`](#health)
    - [`/symbol_analysis`](#symbol_analysis)
    - [`/question/<question number>`](#questionquestion-number)
    - [`/metrics`](#metrics)
- [`binance_analyzer.py`](#binance_analyzerpy)
- [Environment Setup](#environment-setup)
- [Solutions](#solutions)
    - [1. Print the top 5 symbols with quote asset BTC and the highest volume over the last 24 hours in descending order.](#1-print-the-top-5-symbols-with-quote-asset-btc-and-the-highest-volume-over-the-last-24-hours-in-descending-order)
        - [Endpoint](#endpoint)
        - [Script](#script)
    - [2. Print the top 5 symbols with quote asset USDT and the highest number of trades over the last 24 hours in descending order.](#2-print-the-top-5-symbols-with-quote-asset-usdt-and-the-highest-number-of-trades-over-the-last-24-hours-in-descending-order)
        - [Endpoint](#endpoint-1)
        - [Script](#script-1)
    - [3. Using the symbols from Q1, what is the total notional value of the top 200 bids and asks currently on each order book?](#3-using-the-symbols-from-q1-what-is-the-total-notional-value-of-the-top-200-bids-and-asks-currently-on-each-order-book)
        - [Endpoint](#endpoint-2)
        - [Script](#script-2)
    - [4. What is the price spread for each of the symbols from Q2?](#4-what-is-the-price-spread-for-each-of-the-symbols-from-q2)
        - [Endpoint](#endpoint-3)
        - [Script](#script-3)
    - [5. Every 10 seconds print the result of Q4 and the absolute delta from the previous value for each symbol.](#5-every-10-seconds-print-the-result-of-q4-and-the-absolute-delta-from-the-previous-value-for-each-symbol)
        - [Endpoint](#endpoint-4)
        - [Script](#script-4)
    - [6. Make the output of Q5 accessible by querying http://localhost:8080/metrics using the Prometheus Metrics format.](#6-make-the-output-of-q5-accessible-by-querying-httplocalhost8080metrics-using-the-prometheus-metrics-format)
        - [Endpoint](#endpoint-5)
        - [Script](#script-5)
- [Future Improvements](#future-improvements)

# General Stack

All the code here has been written in Python.  

 * The Binance Connector for Python has been leveraged for this assignment  
 * Flask was used for the framework of the REST API, with Gunicorn as the HTTP server  
 * Websocket functionality is provided with Flask-socketio  

In order to deploy the code to the web  

 * AWS EKS was deployed via `eksctl`  
 * the app was containerized with Docker (`Dockerfile` provided),  hosted on ECR  
 * Application deployed via Kubernetes (manifests provided in `kube-manifests/`).  
 * Further AWS support via ALB, Route 53, ACM  

# https://api.binance.siddsingal.com

The code is set up and running at https://api.binance.siddsingal.com on EKS. The following endpoints are available:

### `/`

This `README.md`

### `/health`

Simplistic healthcheck endpoint, always returns `200`.

### `/symbol_analysis`

Perform analysis on Binance symbols. The design has made it easy to add onto the analysis framework, and a decent number of options are already available. The following URL parameters can be provided.

* `quote_assets` - If provided, only symbols with the given quote assets will be considered
* `base_assets` - If provided, only symbols with the given base assets will be considered
* `order_by` - Order symbols by a certain feature. Accepted values are `base_asset`, `quote_asset`, `volume`, `trades`, `bid_price`, `ask_price`, `spread`. Ascending order by default, but append `[asc]` or `[desc]` for ascending or descending order, respectively. (e.g.  `trades[desc]`)
* `limit` - Limit number of symbols to display/analyze. This is especially important for doing market depth queries as we may exhaust the API limit.
* `fields` - Fields to output for each selected symbol. Accepted values are `symbol`, `base_asset`, `quote_asset`, `volume`, `trades`, `bid_price`, `ask_price`, `spread`, `order_book_bid_total_value[<number of levels>]`, `order_book_ask_total_value[<number of levels>]`

Example Request
```
curl -gLs "api.binance.siddsingal.com/symbol_analysis?base_assets=BTC,USDT,XRP,ETH,SC,DOGE&quote_assets=BTC,USDT&order_by=trades[desc]&limit=3&fields=symbol,base_asset,quote_asset,trades,spread,order_book_bid_total_value[200]" | jq
```

Response
```
[
  {
    "symbol": "BTCUSDT",
    "base_asset": "BTC",
    "quote_asset": "USDT",
    "trades": 1127445,
    "spread": 0.01,
    "order_book_bid_total_value[200]": 1894138.328491
  },
  {
    "symbol": "ETHUSDT",
    "base_asset": "ETH",
    "quote_asset": "USDT",
    "trades": 575796,
    "spread": 0.01,
    "order_book_bid_total_value[200]": 2118829.462325
  },
  {
    "symbol": "XRPUSDT",
    "base_asset": "XRP",
    "quote_asset": "USDT",
    "trades": 351272,
    "spread": 0.0001,
    "order_book_bid_total_value[200]": 2706801.2195
  }
]
```

### `/question/<question number>`

Prebaked solutions for the specific questions given for this assignment. Only available for questions 1-4.

Example Request
```
curl -gLs "api.binance.siddsingal.com/question/4" | jq
```

Response:
```
[
  {
    "symbol": "SOLUSDT",
    "trades": 1193585,
    "spread": 0.03
  },
  {
    "symbol": "ADAUSDT",
    "trades": 1179992,
    "spread": 0.001
  },
  {
    "symbol": "BTCUSDT",
    "trades": 1125135,
    "spread": 0.01
  },
  {
    "symbol": "SANDUSDT",
    "trades": 790396,
    "spread": 0.0009
  },
  {
    "symbol": "ICPUSDT",
    "trades": 700867,
    "spread": 0.04
  }
]
```

### `/metrics`

Prometheus endpoint specifically to address question 6. The metric of interest is `spread_delta`.

# `binance_analyzer.py`

This repository also comes with a script called `binance_analyzer.py`. The `--help` menu is pretty detailed, so please refer to that for more information on its usage.

# Environment Setup

Python 3.6+ is recommended for this code.

1. `cd` into the root of the code
2. Start a virtual environment
    ```
    python3.6 -m virtualenv venv
    . venv/bin/activate
    ```
3. Install relevant packages
    ```
    pip install -r requirements.txt
    ```
4. (optional) Start the server locally. This will be required for some of the questions below.
    ```
    gunicorn -b 0.0.0.0:8000 server:app -w 1 --threads 4
    ```
If you can see this page after accessing `localhost:8000/`, then you are good to go!

# Solutions

Please be sure to follow the environment setup above to be able to run the below solutions if not using the public endpoint I've provided. All endpoints below will be referred to as `$ENDPOINT`. If using the local endpoint, please be sure to start the server by following Environment Setup. You may want to set `$ENDPOINT` before starting.
```
# Public
ENDPOINT="https://api.binance.siddsingal.com"

# Local
ENDPOINT="localhost:8000"
```

### 1. Print the top 5 symbols with quote asset BTC and the highest volume over the last 24 hours in descending order.

##### Endpoint

```
# "Correct" Way
curl -gLs "$ENDPOINT/symbol_analysis?quote_assets=BTC&order_by=volume[desc]&limit=5&fields=symbol,volume"

# Cheating
curl -gLs "$ENDPOINT/question/1"
```

##### Script

```
# "Correct" Way
python binance_analyzer.py symbol_analysis -q BTC -o "volume[desc]" -l 5 -f "symbol,volume"

# Cheating
python binance_analyzer.py binance_question 1
```

### 2. Print the top 5 symbols with quote asset USDT and the highest number of trades over the last 24 hours in descending order.

##### Endpoint

```
# "Correct" Way
curl -gLs "$ENDPOINT/symbol_analysis?quote_assets=USDT&order_by=trades[desc]&limit=5&fields=symbol,trades"

# Cheating
curl -gLs "$ENDPOINT/question/2"
```

##### Script

```
# "Correct" Way
python binance_analyzer.py symbol_analysis -q USDT -o "trades[desc]" -l 5 -f "symbol,trades"

# Cheating
python binance_analyzer.py binance_question 2
```


### 3. Using the symbols from Q1, what is the total notional value of the top 200 bids and asks currently on each order book?

##### Endpoint

```
# "Correct" Way
curl -gLs "$ENDPOINT/symbol_analysis?quote_assets=BTC&order_by=volume[desc]&limit=5&fields=symbol,volume,order_book_bid_total_value[200],order_book_ask_total_value[200]"

# Cheating
curl -gLs "$ENDPOINT/question/3"
```

##### Script

```
# "Correct" Way
python binance_analyzer.py symbol_analysis -q BTC -o "volume[desc]" -l 5 -f "symbol,volume,order_book_bid_total_value[200],order_book_ask_total_value[200]"

# Cheating
python binance_analyzer.py binance_question 3
```

### 4. What is the price spread for each of the symbols from Q2?

##### Endpoint

```
# "Correct" Way
curl -gLs "$ENDPOINT/symbol_analysis?quote_assets=USDT&order_by=trades[desc]&limit=5&fields=symbol,trades,spread"

# Cheating
curl -gLs "$ENDPOINT/question/4"
```

##### Script

```
# "Correct" Way
python binance_analyzer.py symbol_analysis -q USDT -o "trades[desc]" -l 5 -f "symbol,trades,spread"

# Cheating
python binance_analyzer.py binance_question 4
```

### 5. Every 10 seconds print the result of Q4 and the absolute delta from the previous value for each symbol.

##### Endpoint

This is not available via endpoint.

##### Script

```
# "Correct" Way
python binance_analyzer.py delta_analysis -q USDT -o "trades[desc]" -l 5 -f "symbol,trades,spread" -d "spread" -i 10000

# Cheating
python binance_analyzer.py binance_question 5
```


### 6. Make the output of Q5 accessible by querying http://localhost:8080/metrics using the Prometheus Metrics format.

The metric is available as `spread_delta`

##### Endpoint

```
curl -gLs "$ENDPOINT/metrics"
```

##### Script

This is not available via script.

# Future Improvements

* Increased logging and error support
* Websockets integration for performing delta analysis
* Deploy Prometheus/Grafana alongside to visualize the metrics we're exporting
* Feature parity with Binance API
* Increased modularity of sidd.binance.connector API. A Mixin paradigm could work well here as plugins for different API requests to Binance
* Implement celery workers for long-running tasks instead of having to launch a single thread to do the prometheus delta analysis
* Customizable delta analysis for prometheus exporting - it is currently hardcoded
* Swagger for documentation - did not have time to get to this