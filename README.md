# StockDash - Stock Market Analysis Dashboard

A comprehensive, free, local stock market analysis dashboard for Indian stocks (Nifty 50) with ML predictions, real-time updates, portfolio tracking, and beautiful UI.

## 🖥️ Live Demo

![Dashboard](https://img.shields.io/badge/Demo-localhost:3000-blue)

## ✨ Features

### Dashboard
- Real-time Nifty 50 stock prices with gainers/losers
- Interactive candlestick charts (1D, 5D, 1M, 3M, 6M, 1Y)
- Market summary cards with key metrics
- Sticky table headers with smooth scrolling

### Stock Search
- **Partial search** across all tickers (not just Nifty 50)
- **Case-insensitive** search
- Live suggestions as you type
- Available on Explore, Portfolio, and Wishlist pages

### Portfolio Management
- Add/remove stock holdings
- Track buy price, quantity, P&L
- Real-time value calculations
- Risk assessment metrics

### Wishlist/Watchlist
- Quick add stocks to track
- Remove with one click
- Price monitoring

### Authentication
- JWT-based login/signup
- Email OR username login
- Auto-redirect for logged-in users
- Secure password hashing

### UI/UX
- Dark/Light theme toggle
- Premium button styling (rounded corners, gradients)
- Responsive design
- Hidden scrollbars with scroll functionality

## 🚀 Quick Start

```bash
# Clone the repository
git clone https://github.com/yourusername/stock-market-project.git
cd stock-market-project

# Create environment file
cp .env.example .env

# Start all services
docker-compose up --build
```

**Access the application:**
- **Frontend**: http://localhost:3000
- **API**: http://localhost:5000
- **API Docs**: http://localhost:5000/api

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Frontend                             │
│                    (Next.js 15 + CSS)                       │
│                    Port: 3000                                │
└─────────────────────┬───────────────────────────────────────┘
                      │ HTTP/WebSocket
┌─────────────────────▼───────────────────────────────────────┐
│                       API Service                            │
│                   (Flask + Socket.IO)                        │
│                      Port: 5000                              │
└─────────────────────┬───────────────────────────────────────┘
                      │ SQL
┌─────────────────────▼───────────────────────────────────────┐
│                       Database                               │
│                     (PostgreSQL)                             │
│                      Port: 5432                              │
└─────────────────────────────────────────────────────────────┘
        ▲
        │ ETL Pipeline
┌───────┴─────────────────────────────────────────────────────┐
│                      ETL Service                             │
│               (Python + yFinance + ML)                       │
│                    Runs on startup                           │
└─────────────────────────────────────────────────────────────┘
```

| Service | Technology | Port | Description |
|---------|------------|------|-------------|
| Frontend | Next.js 15 + CSS | 3000 | React dashboard UI |
| API | Flask + Socket.IO | 5000 | REST API + WebSocket |
| ETL | Python + yFinance | - | Data fetching + ML |
| Database | PostgreSQL 15 | 5432 | Stock data storage |

## 📁 Project Structure

```
stock-market-project/
├── api-service/         # Flask REST API + WebSocket
│   ├── src/api/         # API routes, auth, models
│   └── Dockerfile
├── etl-service/         # Data pipeline + ML models
│   ├── src/etl/         # ETL jobs, data fetching
│   └── Dockerfile
├── frontend/            # Next.js 15 dashboard
│   ├── src/app/         # App router pages
│   ├── src/components/  # Reusable components
│   └── Dockerfile
├── database/            # PostgreSQL setup
│   └── init.sql         # Schema initialization
├── docker-compose.yml   # Container orchestration
└── README.md
```

## 🔧 Development

### API Service
```bash
cd api-service
uv sync
uv run python -m api.app
```

### ETL Service
```bash
cd etl-service
uv sync
uv run python -m etl.main --once
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## 📊 API Endpoints

### Stocks
- `GET /api/stocks` - List all Nifty 50 stocks
- `GET /api/stocks/search?q=REL` - Search stocks (case-insensitive)
- `GET /api/stocks/{ticker}` - Get stock details
- `GET /api/stocks/{ticker}/history` - Historical OHLCV data

### Portfolio
- `GET /api/portfolio` - Get user portfolio
- `POST /api/portfolio` - Add holding
- `DELETE /api/portfolio/{id}` - Remove holding

### Wishlist
- `GET /api/wishlist` - Get user wishlist
- `POST /api/wishlist` - Add to wishlist
- `DELETE /api/wishlist/{id}` - Remove from wishlist

### Auth
- `POST /api/users/signup` - Create account
- `POST /api/users/login` - Login (email or username)
- `GET /api/users/me` - Get current user

## 🔐 Environment Variables

Create a `.env` file in the root directory:

```env
POSTGRES_USER=stockuser
POSTGRES_PASSWORD=stockpass123
POSTGRES_DB=stockmarket
JWT_SECRET=your-secret-key-here
HF_TOKEN=your-huggingface-token  # Optional, for sentiment
```

## ⚠️ Troubleshooting

| Issue | Solution |
|-------|----------|
| Database not ready | Wait for healthcheck or `docker-compose restart api` |
| No stock data | ETL runs on startup; check `docker-compose logs etl` |
| Auth issues | Clear cookies, verify JWT_SECRET is set |
| Build fails | Run `docker-compose down -v` then rebuild |

## 🤖 ML Models (Future)

- ARIMA (time series forecasting)
- Linear Regression
- Random Forest
- XGBoost
- LSTM (deep learning)
- Prophet (Facebook)
- FinBERT (sentiment analysis)

## 📜 License

MIT License - see [LICENSE](LICENSE) for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit changes
4. Push to branch
5. Open a Pull Request
