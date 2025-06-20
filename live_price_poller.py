import asyncio
import logging
import signal
from collections import deque
from datetime import datetime, timezone

import httpx

URL = 'https://api.coingecko.com/api/v3/simple/price'

MAX_CONSECUTIVE_FAILURES = 5
BASIC_TIMEOUT = 1
MAX_TIMEOUT = BASIC_TIMEOUT * (2 ** (MAX_CONSECUTIVE_FAILURES - 1))

logger = logging.getLogger(__name__)
stop_event = asyncio.Event()


async def fetch_price(client, currency_symbol):
    """Fetch the current BTC price in USD from CoinGecko API."""
    params = {
        'ids': currency_symbol,
        'vs_currencies': 'usd',
        'include_last_updated_at': True,
    }

    resp = await client.get(URL, params=params, timeout=4.0)
    resp.raise_for_status()
    data = resp.json()
    return data[currency_symbol]['usd']


async def poll_price(currency_symbol):
    """Main polling loop to fetch and print BTC price every second."""
    consecutive_failures = 0
    timeout = BASIC_TIMEOUT
    price_window = deque(maxlen=10)

    async with httpx.AsyncClient() as client:
        while not stop_event.is_set():
            try:
                price = await fetch_price(client, currency_symbol)
                price_window.append(price)

                sma = sum(price_window) / len(price_window)
                timestamp = datetime.now(timezone.utc).isoformat()
                print(f"[{timestamp}] BTC → USD: ${price} SMA(10): ${sma}")

                # Reset on success
                consecutive_failures = 0
                timeout = BASIC_TIMEOUT

                await asyncio.sleep(BASIC_TIMEOUT)

            except (httpx.RequestError, httpx.HTTPStatusError) as err:
                consecutive_failures += 1
                logger.warning(
                    f'API error: {str(err)} — retrying in {timeout}s (failure {consecutive_failures}/{MAX_CONSECUTIVE_FAILURES})'
                )
                await asyncio.sleep(timeout)
                timeout = min(timeout * 2, MAX_TIMEOUT)

                if consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                    logger.error(f'{MAX_CONSECUTIVE_FAILURES} consecutive failures. Continuing to poll…')


def handle_shutdown(*_) -> None:
    print("\nShutting down…")
    stop_event.set()


if __name__ == "__main__":
    signal.signal(signal.SIGINT, handle_shutdown)
    asyncio.run(poll_price('bitcoin'))
