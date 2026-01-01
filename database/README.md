# Database

PostgreSQL database schema for stock market data.

## 🚀 Quick Start

Database is automatically initialized by docker-compose with the `init.sql` script.

```bash
# Connect to database
docker exec -it stock-db psql -U stockuser -d stockmarket
```

## 📁 Structure

```
database/
├── init.sql      # Schema initialization
├── Dockerfile    # PostgreSQL image config
└── README.md
```

## 📊 Schema

### stocks
Main table for stock price data (OHLCV).

| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL | Primary key |
| ticker | VARCHAR(20) | Stock symbol (e.g., RELIANCE.NS) |
| date | DATE | Trading date |
| open | DECIMAL(12,2) | Opening price |
| high | DECIMAL(12,2) | Day high |
| low | DECIMAL(12,2) | Day low |
| close | DECIMAL(12,2) | Closing price |
| volume | BIGINT | Trading volume |
| created_at | TIMESTAMP | Record creation time |

### users
User accounts for authentication.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| email | VARCHAR(255) | User email (unique) |
| username | VARCHAR(50) | Username (unique) |
| password_hash | VARCHAR(255) | Bcrypt hash |
| created_at | TIMESTAMP | Account creation |

### portfolios
User stock holdings.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| user_id | UUID | Foreign key to users |
| ticker | VARCHAR(20) | Stock symbol |
| quantity | DECIMAL(12,4) | Number of shares |
| buy_price | DECIMAL(12,2) | Purchase price |
| created_at | TIMESTAMP | Entry time |

### wishlists
User watchlist items.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| user_id | UUID | Foreign key to users |
| ticker | VARCHAR(20) | Stock symbol |
| added_at | TIMESTAMP | When added |

## 🔧 Indexes

- `stocks(ticker, date)` - Fast stock lookup
- `users(email)` - Email uniqueness
- `users(username)` - Username uniqueness
- `portfolios(user_id)` - User portfolio lookup
- `wishlists(user_id)` - User wishlist lookup

## 🐳 Docker

```bash
docker build -t stock-db .
docker run -p 5432:5432 -e POSTGRES_PASSWORD=stockpass123 stock-db
```

## 📝 Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| POSTGRES_USER | Database user | stockuser |
| POSTGRES_PASSWORD | User password | Required |
| POSTGRES_DB | Database name | stockmarket |
