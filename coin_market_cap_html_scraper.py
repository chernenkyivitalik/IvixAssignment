import sqlite3
import time
from datetime import datetime, timezone

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager


def setup_driver():
    options = Options()
    options.add_argument('--headless=new')
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)


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


def extract_coin_data(html):
    """Extract coins data from the loaded page."""
    soup = BeautifulSoup(html, 'html.parser')
    table = soup.find('table')
    if not table:
        return []

    coins = []
    collected_at = datetime.now(timezone.utc).isoformat()
    rows = table.tbody.find_all('tr')  # type:ignore
    for row in rows:
        cols = row.find_all('td')  # type:ignore
        if len(cols) < 11:
            continue

        rank = int(cols[1].text.strip())
        name = cols[2].find_all('p')[0].text.strip()  # type:ignore
        symbol = cols[2].find_all('p')[1].text.strip()  # type:ignore
        price = float(cols[3].text.strip().replace('$', '').replace(',', ''))
        change_24h = float(cols[4].text.strip().replace('%', '').replace(',', ''))
        market_cap = cols[7].text.strip()
        coins.append((rank, name, symbol, price, change_24h, market_cap, collected_at))

    return coins


def scroll_to_bottom(driver, step=500, delay=1.5):
    """Scroll the page to the bottom to load all the records in the table."""
    last_scroll_y = driver.execute_script('return window.scrollY')

    while True:
        driver.execute_script(f'window.scrollBy(0, {step});')
        time.sleep(delay)  # Wait to load next records

        new_scroll_y = driver.execute_script('return window.scrollY')
        if new_scroll_y == last_scroll_y:
            break
        last_scroll_y = new_scroll_y


if __name__ == '__main__':
    driver = setup_driver()
    db_connection = setup_database()

    for page in range(1, 6):
        driver.get(f'https://coinmarketcap.com/?page={page}')
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.TAG_NAME, 'table')))
        scroll_to_bottom(driver)
        data = extract_coin_data(driver.page_source)
        save_to_database(db_connection, data)

    driver.quit()
    db_connection.close()
