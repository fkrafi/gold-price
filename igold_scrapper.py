import os
import json
from datetime import datetime
from playwright.sync_api import sync_playwright


def scrape_gold_rates():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto("https://igold.ae/gold-rate", wait_until="networkidle")

        page.wait_for_timeout(3000)

        data = page.evaluate("""
        () => {
            const heading = [...document.querySelectorAll('h2')]
                .find(h => h.innerText.includes('Current Live Retail Gold Rate'));

            if (!heading) return null;

            const table = heading.nextElementSibling;
            const tds = table?.querySelectorAll('tr:nth-child(2) td');

            if (!tds || tds.length < 4) return null;

            const clean = (text) =>
                text.replace(/[^0-9.]/g, '').trim();

            return {
                gold_24kt: clean(tds[0].innerText),
                gold_22kt: clean(tds[1].innerText),
                gold_21kt: clean(tds[2].innerText),
                gold_18kt: clean(tds[3].innerText),
            };
        }
        """)

        browser.close()

        if not data:
            raise Exception("Failed to scrape gold rates")

        return data


def save_json(data):
    dir_path = os.path.join(".", "api", "v2")
    os.makedirs(dir_path, exist_ok=True)

    file_name = datetime.now().strftime("%Y-%m-%d") + ".json"
    file_path = os.path.join(dir_path, file_name)

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    print(f"Saved: {file_path}")


if __name__ == "__main__":
    try:
        gold_data = scrape_gold_rates()
        print("Scraped:", gold_data)
        save_json(gold_data)
    except Exception as e:
        print("Error:", str(e))