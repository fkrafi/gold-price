# gold-price

Automated gold price fetcher that runs daily via GitHub Actions.

## Overview

This repository contains a Python script that fetches current gold prices and automatically updates the data file using GitHub Actions.

## Features

- **Automated Daily Updates**: Runs automatically every day at midnight UTC
- **Manual Trigger**: Can be triggered manually via GitHub Actions workflow
- **Auto-commit**: Automatically commits and pushes updated data to the repository

## Files

- `fetch_gold_price.py` - Python script that fetches gold prices from an API
- `gold_price_data.json` - Generated file containing the latest gold price data
- `requirements.txt` - Python dependencies
- `.github/workflows/fetch-gold-price.yml` - GitHub Actions workflow configuration

## How It Works

1. The GitHub Action runs on a schedule (daily at 00:00 UTC)
2. It checks out the repository
3. Sets up Python environment
4. Installs dependencies from `requirements.txt`
5. Runs `fetch_gold_price.py` to fetch current gold prices
6. Checks if the data has changed
7. If changed, commits and pushes the updated `gold_price_data.json` file

## Manual Execution

You can manually trigger the workflow from the Actions tab in GitHub.

## Local Development

To run the script locally:

```bash
pip install -r requirements.txt
python fetch_gold_price.py
```