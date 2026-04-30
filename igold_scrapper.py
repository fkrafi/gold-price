#!/usr/bin/env python3
"""
Fetch iGold gold rates and save as date-named JSON under api/v2/.
"""

import json
import os
import re
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

try:
    from playwright.sync_api import sync_playwright
except Exception:
    sync_playwright = None

H2_TEXT = "Current Live Retail Gold Rate in Dubai UAE"

UBUNTU_FIREFOX_UA = (
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:128.0) "
    "Gecko/20100101 Firefox/128.0"
)

DEFAULT_HEADERS = {
    "User-Agent": UBUNTU_FIREFOX_UA,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

API_DIR = "./v2/api"


def _get_session() -> requests.Session:
    """Create a requests session with retries."""
    session = requests.Session()
    retries = Retry(total=3, backoff_factor=0.5, status_forcelist=(429, 500, 502, 503, 504))
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def _extract_rates_from_soup(soup: BeautifulSoup):
    """Extract gold rates from the iGold rate table.
    Returns a dict with gold_24kt/22kt/21kt/18kt keys, or None.
    """
    heading = soup.find("h2", string=lambda t: t and H2_TEXT in t)
    table = heading.find_next_sibling("table", class_="table") if heading else None
    if not table and heading:
        table = heading.find_next("table", class_="table")
    if not table:
        return None

    row = table.select_one("tbody tr")
    tds = row.find_all("td") if row else []
    if len(tds) < 4:
        return None

    def clean(text):
        return re.sub(r"[^0-9.]", "", text).strip()

    return {
        "gold_24kt": clean(tds[0].get_text()),
        "gold_22kt": clean(tds[1].get_text()),
        "gold_21kt": clean(tds[2].get_text()),
        "gold_18kt": clean(tds[3].get_text()),
    }


def fetch_igold_goldrate():
    """Fetch gold rate table from iGold and return dict or None.
    Tries Playwright headless rendering first, then falls back to requests.
    """
    url = "https://igold.ae/gold-rate"

    # Try headless browser for JS-rendered content
    if sync_playwright is not None:
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page(user_agent=UBUNTU_FIREFOX_UA)
                page.goto(url, wait_until="networkidle")
                page.wait_for_timeout(3000)
                html = page.content()
                browser.close()
            soup = BeautifulSoup(html, "html.parser")
            data = _extract_rates_from_soup(soup)
            if data:
                return data
            else:
                print("Rendered page loaded but table not found; falling back to static fetch.")
        except Exception as e:
            print(f"Playwright error, falling back to static fetch: {e}")
            print("Hint: Install browsers with 'python3 -m playwright install chromium'.")

    # Fallback: static HTML fetch
    session = _get_session()
    try:
        resp = session.get(url, headers=DEFAULT_HEADERS, timeout=15)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"Error fetching iGold page: {e}")
        return None

    soup = BeautifulSoup(resp.text, "html.parser")
    data = _extract_rates_from_soup(soup)
    if not data:
        print("Gold rate table not found on the page.")
    return data


def save_gold_price(data):
    """Save gold price data to a date-named JSON file (YYYY-MM-DD.json)."""
    date_str = datetime.now().strftime("%Y-%m-%d")
    filename = f"{API_DIR}/{date_str}.json"
    os.makedirs(API_DIR, exist_ok=True)
    with open(filename, "w") as f:
        json.dump(data, f, indent=2)
    print(f"Saved gold rate data to {filename}")
    _update_history(date_str, data)


def _update_history(date_str: str, data: dict):
    """Prepend today's data to ./api/v2/history.json and keep history ordered.
    History format: { "YYYY-MM-DD": { ... }, ... } with most recent first.
    """
    history_path = f"{API_DIR}/history.json"
    os.makedirs(API_DIR, exist_ok=True)

    try:
        with open(history_path, "r") as f:
            existing = json.load(f)
            if not isinstance(existing, dict):
                existing = {}
    except FileNotFoundError:
        existing = {}
    except json.JSONDecodeError:
        existing = {}

    # Build new ordered history: today first, then all previous entries
    new_history = {date_str: data}
    for k, v in existing.items():
        if k == date_str:
            continue  # replace today's entry
        new_history[k] = v

    with open(history_path, "w") as f:
        json.dump(new_history, f, indent=2)
    print(f"Updated history at {history_path}")


def main():
    data = fetch_igold_goldrate()
    if data:
        save_gold_price(data)


if __name__ == "__main__":
    main()
