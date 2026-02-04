#!/usr/bin/env python3
"""
Fetch current gold prices and generate a data file.
"""

import json
import requests
from datetime import datetime

def fetch_gold_price():
    """Fetch gold price from API."""
    # Using metals-api.com or similar free API
    # For this example, we'll use a free gold price API
    api_url = "https://api.metals.live/v1/spot/gold"
    
    try:
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data
    except requests.RequestException as e:
        print(f"Error fetching gold price: {e}")
        # Return mock data if API fails
        return {
            "timestamp": datetime.now().isoformat(),
            "gold_price_usd": 0.0,
            "source": "mock_data",
            "error": str(e)
        }

def save_gold_price(data):
    """Save gold price data to JSON file."""
    timestamp = datetime.now().isoformat()
    
    output_data = {
        "last_updated": timestamp,
        "gold_data": data
    }
    
    # Save to JSON file
    with open("gold_price_data.json", "w") as f:
        json.dump(output_data, f, indent=2)
    
    print(f"Gold price data saved at {timestamp}")
    print(f"Data: {json.dumps(output_data, indent=2)}")

def main():
    """Main function to fetch and save gold price."""
    print("Fetching gold price...")
    data = fetch_gold_price()
    save_gold_price(data)
    print("Done!")

if __name__ == "__main__":
    main()
