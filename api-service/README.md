# API Service

Flask-based REST API with JWT authentication and Socket.IO for real-time updates.

## 🚀 Quick Start

```bash
cd api-service
uv sync
uv run python -m api.app
```

Server runs at http://localhost:5000

## 📁 Structure

```
api-service/
├── src/api/
│   ├── app.py            # Flask application entry
│   ├── auth.py           # JWT authentication logic
│   ├── config.py         # Configuration settings
│   ├── db.py             # Database connection pool
│   └── routers/
│       ├── stocks.py     # Stock data endpoints
│       ├── portfolios.py # Portfolio + wishlist
│       └── users.py      # Auth endpoints
├── Dockerfile
├── pyproject.toml        # UV dependencies
└── README.md
```

## 🔌 API Endpoints

### Stocks
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/stocks` | List Nifty 50 stocks |
| GET | `/api/stocks/search?q=REL` | Search (case-insensitive) |
| GET | `/api/stocks/{ticker}` | Stock details |
| GET | `/api/stocks/{ticker}/history` | OHLCV history |
| GET | `/api/stocks/{ticker}/candles` | Candlestick data |

### Portfolio
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/portfolio` | User portfolio |
| POST | `/api/portfolio` | Add holding |
| DELETE | `/api/portfolio/{id}` | Remove holding |
| GET | `/api/portfolio/risk` | Risk metrics |

### Wishlist
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/wishlist` | User wishlist |
| POST | `/api/wishlist` | Add stock |
| DELETE | `/api/wishlist/{id}` | Remove stock |

### Auth
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/users/signup` | Create account |
| POST | `/api/users/login` | Login (email/username) |
| GET | `/api/users/me` | Current user |

## 🔐 Authentication

- Uses JWT tokens in cookies
- Supports login with email OR username
- Token expires in 24 hours

## 🐳 Docker

```bash
docker build -t stock-api .
docker run -p 5000:5000 stock-api
```

## 📝 Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| DATABASE_URL | PostgreSQL connection | Required |
| JWT_SECRET | JWT signing key | Required |
| FLASK_ENV | Environment | production |
