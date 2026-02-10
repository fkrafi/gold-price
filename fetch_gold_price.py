#!/usr/bin/env python3
"""
Fetch Joyalukkas gold rates and save as date-named JSON.
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

def _to_snake_key(text: str) -> str:
    """Convert a label to snake_case key, removing the word 'rate'."""
    t = text.lower()
    # remove standalone 'rate'
    t = re.sub(r"\brate\b", "", t)
    # replace non-alphanumeric with underscores
    t = re.sub(r"[^a-z0-9]+", "_", t)
    # collapse multiple underscores and trim
    t = re.sub(r"_+", "_", t).strip("_")
    return t

def _extract_rates_from_soup(soup: BeautifulSoup):
    """Extract key/value pairs from the gold rate table.
    Returns a dict mapping snake_case keys to cell values, or None.
    """
    container = soup.select_one(".goldRate-scrollit-ZgL")
    table = container.find("table") if container else soup.find("table")

    if not table:
        return None

    data = {}
    skip_first = True  # Skip the first row (likely header)
    for tr in table.find_all("tr"):
        cells = tr.find_all(["th", "td"])
        if len(cells) >= 2:
            if skip_first:
                skip_first = False
                continue
            key_raw = cells[0].get_text(strip=True)
            val_text = cells[1].get_text(strip=True)
            # Remove 'AED' from the value (case-insensitive)
            val_text = re.sub(r"AED", "", val_text, flags=re.IGNORECASE).strip()
            key = _to_snake_key(key_raw)
            if key:
                data[key] = val_text

    return data or None

UBUNTU_FIREFOX_UA = (
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:128.0) "
    "Gecko/20100101 Firefox/128.0"
)

DEFAULT_HEADERS = {
    "User-Agent": UBUNTU_FIREFOX_UA,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

def _get_session() -> requests.Session:
    """Create a requests session with retries."""
    session = requests.Session()
    retries = Retry(total=3, backoff_factor=0.5, status_forcelist=(429, 500, 502, 503, 504))
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session

def fetch_joyalukkas_goldrate():
    """Fetch gold rate table from Joyalukkas and return dict or None.
    Tries Playwright headless rendering first, then falls back to requests.
    """
    url = "https://www.joyalukkas.com/ae/goldrate"

    # Try headless browser for JS-rendered content
    if sync_playwright is not None:
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page(user_agent=UBUNTU_FIREFOX_UA)
                page.goto(url, wait_until="networkidle")
                try:
                    page.wait_for_selector(".goldRate-scrollit-ZgL table", timeout=10000)
                except Exception:
                    page.wait_for_selector("table", timeout=10000)
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
        print(f"Error fetching Joyalukkas page: {e}")
        return None

    soup = BeautifulSoup(resp.text, "html.parser")
    data = _extract_rates_from_soup(soup)
    if not data:
        print("Gold rate table not found on the page.")
    return data

def save_gold_price(data):
    """Save gold price data to a date-named JSON file (YYYY-MM-DD.json)."""
    date_str = datetime.now().strftime("%Y-%m-%d")
    filename = f"./api/{date_str}.json"
    os.makedirs("./api", exist_ok=True)
    with open(filename, "w") as f:
        json.dump(data, f, indent=2)
    print(f"Saved gold rate data to {filename}")
    _update_history(date_str, data)

def _update_history(date_str: str, data: dict):
    """Prepend today's data to ./api/history.json and keep only top 30 items.
    History format: { "YYYY-MM-DD": { ... }, ... } with most recent first.
    """
    history_path = "./api/history.json"
    os.makedirs("./api", exist_ok=True)

    # Load existing history, tolerate missing or invalid JSON
    try:
        with open(history_path, "r") as f:
            existing = json.load(f)
            if not isinstance(existing, dict):
                existing = {}
    except FileNotFoundError:
        existing = {}
    except json.JSONDecodeError:
        existing = {}

    # Build new ordered history: today first, then previous entries up to 29
    new_history = {date_str: data}
    count = 1
    for k, v in existing.items():
        if k == date_str:
            continue  # replace today's entry
        new_history[k] = v
        count += 1
        if count >= 30:
            break

    with open(history_path, "w") as f:
        json.dump(new_history, f, indent=2)
    print(f"Updated history at {history_path} (top {min(count,30)} items)")

def main():
    data = fetch_joyalukkas_goldrate()
    if data:
        save_gold_price(data)

if __name__ == "__main__":
    main()
