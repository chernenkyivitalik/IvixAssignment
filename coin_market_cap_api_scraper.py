import asyncio
import os
import sqlite3
from datetime import datetime, timezone

import httpx
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.environ['API_TOKEN']
URL = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest'
HEADERS = {'X-CMC_PRO_API_KEY': API_KEY}


def setup_database():
    connection = sqlite3.connect('coinmarketcap_top100.db')
    cursor = connection.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS coins (
            rank INTEGER,
            name TEXT,
            symbol TEXT,
            price_usd REAL,
            change_24h REAL,
            market_cap_usd TEXT,
            collected_at TEXT
        )
    """)
    connection.commit()

    return connection


def save_to_database(connection, data):
    cursor = connection.cursor()
    cursor.executemany("""
        INSERT INTO coins (rank, name, symbol, price_usd, change_24h, market_cap_usd, collected_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, data)
    connection.commit()


async def fetch_page(client, start, limit=50):
    resp = await client.get(URL, params={'start': start, 'limit': limit}, headers=HEADERS, timeout=10)
    resp.raise_for_status()
    return resp.json()['data']


def extract_coin_data(data):
    coins = []
    collected_at = datetime.now(timezone.utc).isoformat()
    for item in data:
        rank = item['cmc_rank']
        name = item['name']
        symbol = item['symbol']
        quote = item['quote']['USD']
        price = quote['price']
        change = quote['percent_change_24h']
        market_cap = quote['market_cap']
        coins.append((rank, name, symbol, price, change, market_cap, collected_at))

    return coins


async def main():
    db_connection = setup_database()

    async with httpx.AsyncClient() as client:
        tasks = [fetch_page(client, start) for start in range(1, 301, 50)]
        pages = await asyncio.gather(*tasks)

        for page_data in pages:
            coins = extract_coin_data(page_data)
            save_to_database(db_connection, coins)
    
    db_connection.close()

if __name__ == '__main__':
    asyncio.run(main())
