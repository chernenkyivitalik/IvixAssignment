# Instalation

## (Optional) Use a virtual environment
`python -m venv venv source venv/bin/activate  # or venv\Scripts\activate on Windows`

## Install dependencies
`pip install -r requirements.txt`

## For the API scraper, set your API key
`echo "API_TOKEN=your_coinmarketcap_api_key_here" > .env`


# Run the sripts
### *coin_market_cap_html_scraper.py*
Scrapes top 100 coins from CoinMarketCap’s web UI using Selenium.

`python coin_market_cap_html_scraper.py`

### *coin_market_cap_api_scraper.py*
Uses CoinMarketCap's Pro API to fetch the top 300 coins (50 coins per request, done asynchronously).

`python coin_market_cap_api_scraper.py`
📌 Requires a free API key from https://pro.coinmarketcap.com/

### *live_price_poller.py*
Polls the current Bitcoin price (BTC→USD) every 10 seconds using CoinGecko. Prints live price and a 10-point moving average (SMA).

`python live_price_poller.py`
