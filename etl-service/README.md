# ETL Service

Data pipeline service for fetching stock data from yFinance and populating the database.

## 🚀 Quick Start

```bash
cd etl-service
uv sync
uv run python -m etl.main --once
```

## 📁 Structure

```
etl-service/
├── src/etl/
│   ├── main.py           # Entry point
│   ├── config.py         # Configuration
│   ├── db.py             # Database connection
│   ├── data_fetcher.py   # yFinance integration
│   └── exceptions.py     # Custom exceptions
├── Dockerfile
├── pyproject.toml        # UV dependencies
└── README.md
```

## 📊 What It Does

1. **Fetches Nifty 50 stock list** from NSE
2. **Downloads historical data** (OHLCV) via yFinance
3. **Stores in PostgreSQL** for API consumption
4. **Runs on container startup** via docker-compose

## 🛠️ Features

- Batch data fetching for 50 stocks
- Configurable date ranges
- Error handling and retries
- Database upsert (insert or update)

## 🐳 Docker

```bash
docker build -t stock-etl .
docker run stock-etl
```

## 📝 Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| DATABASE_URL | PostgreSQL connection | Required |
| ETL_DAYS | Days of history to fetch | 365 |

## 🔄 Running Modes

```bash
# One-time run (default in Docker)
uv run python -m etl.main --once

# Continuous mode (runs periodically)
uv run python -m etl.main
```
