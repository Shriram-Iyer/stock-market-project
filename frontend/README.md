# Frontend

Next.js 15 dashboard for stock market analysis with modern UI and real-time updates.

## 🚀 Quick Start

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:3000

## 📁 Structure

```
frontend/
├── src/
│   ├── app/                 # Next.js App Router
│   │   ├── page.tsx         # Dashboard
│   │   ├── explore/         # Stock search
│   │   ├── portfolio/       # Portfolio management
│   │   ├── wishlist/        # Watchlist
│   │   ├── stocks/[ticker]/ # Stock detail pages
│   │   ├── login/           # Authentication
│   │   ├── signup/          # Registration
│   │   ├── globals.css      # Global styles
│   │   └── layout.tsx       # Root layout
│   ├── components/
│   │   ├── Navbar.tsx       # Navigation bar
│   │   ├── StockTable.tsx   # Stock list table
│   │   ├── StockSearch.tsx  # Partial search component
│   │   └── CandlestickChart.tsx
│   └── utils/
│       ├── api.ts           # API client
│       ├── AuthContext.tsx  # Auth state
│       └── ThemeContext.tsx # Dark/light theme
├── Dockerfile
├── package.json
└── README.md
```

## ✨ Features

### Pages
- **Dashboard** - Nifty 50 overview, gainers/losers
- **Explore** - Search any stock (case-insensitive)
- **Portfolio** - Track holdings with P&L
- **Wishlist** - Watchlist management
- **Stock Detail** - Charts, metrics, predictions

### Components
- **StockSearch** - Partial search with live suggestions
- **StockTable** - Sortable table with sticky headers
- **CandlestickChart** - OHLCV candlesticks

### UI/UX
- Dark/Light theme toggle
- Responsive design
- Premium button styling
- Hidden scrollbars

## 🎨 Styling

Uses vanilla CSS with CSS variables for theming:

```css
:root {
  --bg-primary: #0f172a;
  --text-primary: #f8fafc;
  --green: #22c55e;
  --red: #ef4444;
}
```

## 🐳 Docker

```bash
docker build -t stock-frontend .
docker run -p 3000:3000 stock-frontend
```

## 📝 Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| NEXT_PUBLIC_API_URL | API server URL | http://localhost:5000 |
