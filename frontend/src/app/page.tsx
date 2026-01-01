'use client';

import { useState, useEffect } from 'react';
import MarketTicker from '@/components/MarketTicker';
import StockTable from '@/components/StockTable';
import TopMoversChart from '@/components/TopMoversChart';
import MarketSentimentChart from '@/components/MarketSentimentChart';
import VolumeChart from '@/components/VolumeChart';
import { stocksAPI, portfolioAPI, wishlistAPI, Stock } from '@/utils/api';
import { useAuth } from '@/utils/AuthContext';
import Link from 'next/link';

interface PortfolioHolding {
    ticker: string;
    quantity: number;
    buy_price: number;
}

interface WishlistItem {
    ticker: string;
}

export default function DashboardPage() {
    const [stocks, setStocks] = useState<Stock[]>([]);
    const [portfolioStocks, setPortfolioStocks] = useState<(Stock & { quantity: number; avgPrice: number })[]>([]);
    const [wishlistStocks, setWishlistStocks] = useState<Stock[]>([]);
    const [userTickers, setUserTickers] = useState<Set<string>>(new Set());
    const [loading, setLoading] = useState(true);
    const [viewMode, setViewMode] = useState<'table' | 'grid'>('table');
    const { isAuthenticated } = useAuth();

    useEffect(() => {
        const fetchData = async () => {
            try {
                // Always fetch Nifty 50 for market overview
                const response = await stocksAPI.getAll(1, 50);
                setStocks(response.data);

                // If logged in, fetch portfolio and wishlist stocks
                if (isAuthenticated) {
                    try {
                        const [portfolioRes, wishlistRes] = await Promise.all([
                            portfolioAPI.get(),
                            wishlistAPI.get()
                        ]);

                        const allUserTickers = new Set<string>();

                        // Process portfolio
                        if (portfolioRes.holdings && portfolioRes.holdings.length > 0) {
                            const portfolioHoldings = portfolioRes.holdings as PortfolioHolding[];
                            portfolioHoldings.forEach(h => allUserTickers.add(h.ticker));

                            // Match with stock data
                            const matchedPortfolio = portfolioHoldings.map(h => {
                                const stockData = response.data.find((s: Stock) => s.ticker === h.ticker);
                                if (stockData) {
                                    return {
                                        ...stockData,
                                        quantity: h.quantity,
                                        avgPrice: h.buy_price,
                                    };
                                }
                                return null;
                            }).filter(Boolean) as (Stock & { quantity: number; avgPrice: number })[];

                            setPortfolioStocks(matchedPortfolio);
                        }

                        // Process wishlist
                        if (wishlistRes.data && wishlistRes.data.length > 0) {
                            const wishlistItems = wishlistRes.data as WishlistItem[];
                            wishlistItems.forEach(w => allUserTickers.add(w.ticker));

                            // Match with stock data (exclude stocks already in portfolio)
                            const portfolioTickers = new Set(portfolioRes.holdings?.map((h: PortfolioHolding) => h.ticker) || []);
                            const matchedWishlist = wishlistItems
                                .filter(w => !portfolioTickers.has(w.ticker))
                                .map(w => response.data.find((s: Stock) => s.ticker === w.ticker))
                                .filter(Boolean) as Stock[];

                            setWishlistStocks(matchedWishlist);
                        }

                        setUserTickers(allUserTickers);
                    } catch (err) {
                        console.log('Could not fetch user stocks:', err);
                    }
                }
            } catch (err) {
                console.error(err);
            } finally {
                setLoading(false);
            }
        };
        fetchData();
    }, [isAuthenticated]);

    if (loading) {
        return (
            <div style={{ display: 'flex', justifyContent: 'center', padding: '80px 0' }}>
                <div className="spinner" />
            </div>
        );
    }

    // Filter out user's stocks from Nifty 50 and sort by ranking (change %)
    const filteredStocks = stocks
        .filter(s => !userTickers.has(s.ticker))
        .sort((a, b) => {
            const changeA = ((a.close - a.open) / a.open) * 100;
            const changeB = ((b.close - b.open) / b.open) * 100;
            return changeB - changeA; // Descending by performance
        });

    const gainers = stocks.filter(s => s.close > s.open).length;
    const losers = stocks.filter(s => s.close < s.open).length;
    const topGainer = [...stocks].sort((a, b) => ((b.close - b.open) / b.open) - ((a.close - a.open) / a.open))[0];
    const topLoser = [...stocks].sort((a, b) => ((a.close - a.open) / a.open) - ((b.close - b.open) / b.open))[0];

    // Calculate portfolio value
    const portfolioValue = portfolioStocks.reduce((sum, s) => sum + (s.close * s.quantity), 0);
    const portfolioCost = portfolioStocks.reduce((sum, s) => sum + (s.avgPrice * s.quantity), 0);
    const portfolioGain = portfolioValue - portfolioCost;
    const portfolioGainPct = portfolioCost > 0 ? (portfolioGain / portfolioCost) * 100 : 0;

    return (
        <div>
            {/* Auto-scrolling Market Ticker */}
            {stocks.length > 0 && <MarketTicker stocks={stocks} />}

            <div className="container" style={{ padding: '24px' }}>

                {/* PORTFOLIO SECTION - Card Grid */}
                {isAuthenticated && portfolioStocks.length > 0 && (
                    <div className="card" style={{ marginBottom: '24px', border: '2px solid var(--green)' }}>
                        <div className="card-header" style={{
                            background: 'var(--green-bg)',
                            display: 'flex',
                            justifyContent: 'space-between',
                            alignItems: 'center'
                        }}>
                            <span style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                💼 My Portfolio
                                <span style={{
                                    background: 'var(--green)',
                                    color: 'white',
                                    padding: '2px 8px',
                                    borderRadius: '12px',
                                    fontSize: '0.75rem'
                                }}>
                                    {portfolioStocks.length} holdings
                                </span>
                            </span>
                            <div style={{ textAlign: 'right' }}>
                                <div style={{ fontSize: '1.25rem', fontWeight: 'bold' }}>
                                    ₹{portfolioValue.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                                </div>
                                <div style={{
                                    fontSize: '0.75rem',
                                    color: portfolioGain >= 0 ? 'var(--green)' : 'var(--red)'
                                }}>
                                    {portfolioGain >= 0 ? '▲' : '▼'} ₹{Math.abs(portfolioGain).toFixed(2)} ({portfolioGainPct.toFixed(2)}%)
                                </div>
                            </div>
                        </div>
                        <div className="card-body" style={{
                            display: 'grid',
                            gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))',
                            gap: '12px',
                            padding: '16px'
                        }}>
                            {portfolioStocks.map(stock => {
                                const currentValue = stock.close * stock.quantity;
                                const investedValue = stock.avgPrice * stock.quantity;
                                const pnl = currentValue - investedValue;
                                const pnlPct = (pnl / investedValue) * 100;
                                const isProfit = pnl >= 0;
                                return (
                                    <a key={stock.ticker} href={`/stocks/${stock.ticker}`} className="stock-card" style={{
                                        background: 'var(--bg-elevated)',
                                        border: `1px solid ${isProfit ? 'var(--green)' : 'var(--red)'}`,
                                    }}>
                                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                                            <div className="ticker" style={{ fontSize: '1rem', fontWeight: '700' }}>
                                                {stock.ticker.replace('.NS', '')}
                                            </div>
                                            <span style={{
                                                fontSize: '0.65rem',
                                                background: 'var(--bg)',
                                                padding: '2px 6px',
                                                borderRadius: '4px',
                                                color: 'var(--text-muted)'
                                            }}>
                                                {stock.quantity} qty
                                            </span>
                                        </div>
                                        <div className="price" style={{ color: isProfit ? 'var(--green)' : 'var(--red)', fontSize: '1.25rem', marginTop: '4px' }}>
                                            ₹{stock.close.toFixed(2)}
                                        </div>
                                        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                                            Avg: ₹{stock.avgPrice.toFixed(2)}
                                        </div>
                                        <div style={{
                                            marginTop: '8px',
                                            padding: '6px',
                                            background: isProfit ? 'var(--green-bg)' : 'var(--red-bg)',
                                            borderRadius: '4px',
                                            textAlign: 'center'
                                        }}>
                                            <span style={{ fontSize: '0.875rem', fontWeight: '600', color: isProfit ? 'var(--green)' : 'var(--red)' }}>
                                                {isProfit ? '+' : ''}₹{pnl.toFixed(0)} ({pnlPct.toFixed(1)}%)
                                            </span>
                                        </div>
                                    </a>
                                );
                            })}
                        </div>
                    </div>
                )}

                {/* WISHLIST SECTION */}
                {isAuthenticated && wishlistStocks.length > 0 && (
                    <div className="card" style={{ marginBottom: '24px', border: '2px solid var(--blue)' }}>
                        <div className="card-header" style={{
                            background: 'var(--blue-bg)',
                            display: 'flex',
                            justifyContent: 'space-between',
                            alignItems: 'center'
                        }}>
                            <span style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                ⭐ My Watchlist
                                <span style={{
                                    background: 'var(--blue)',
                                    color: 'white',
                                    padding: '2px 8px',
                                    borderRadius: '12px',
                                    fontSize: '0.75rem'
                                }}>
                                    {wishlistStocks.length} stocks
                                </span>
                            </span>
                            <Link href="/explore" className="btn btn-primary" style={{ fontSize: '0.75rem', padding: '4px 12px' }}>
                                + Add More
                            </Link>
                        </div>
                        <div className="card-body" style={{
                            display: 'grid',
                            gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))',
                            gap: '12px',
                            padding: '16px'
                        }}>
                            {wishlistStocks.map((stock) => {
                                const change = stock.close - stock.open;
                                const changePct = ((change / stock.open) * 100);
                                const isPositive = change >= 0;
                                return (
                                    <a key={stock.ticker} href={`/stocks/${stock.ticker}`} className="stock-card" style={{
                                        background: 'var(--bg-elevated)',
                                        border: `1px solid ${isPositive ? 'var(--green)' : 'var(--red)'}`,
                                    }}>
                                        <div className="ticker" style={{ fontSize: '1rem' }}>{stock.ticker.replace('.NS', '')}</div>
                                        <div className="price" style={{ color: isPositive ? 'var(--green)' : 'var(--red)', fontSize: '1.25rem' }}>
                                            ₹{stock.close.toFixed(2)}
                                        </div>
                                        <div className="change" style={{ color: isPositive ? 'var(--green)' : 'var(--red)', fontSize: '0.875rem' }}>
                                            {isPositive ? '▲' : '▼'} {changePct.toFixed(2)}%
                                        </div>
                                    </a>
                                );
                            })}
                        </div>
                    </div>
                )}

                {/* Welcome message for non-logged-in users */}
                {!isAuthenticated && (
                    <div className="card" style={{ marginBottom: '24px', background: 'var(--blue-bg)', border: '1px solid var(--blue)' }}>
                        <div className="card-body" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <div>
                                <div style={{ fontWeight: '600', marginBottom: '4px' }}>Track Your Favorite Stocks</div>
                                <div style={{ fontSize: '0.875rem', color: 'var(--text-muted)' }}>
                                    Sign up to add stocks to your portfolio and watchlist
                                </div>
                            </div>
                            <div style={{ display: 'flex', gap: '8px' }}>
                                <Link href="/login" className="btn btn-secondary">Login</Link>
                                <Link href="/signup" className="btn btn-primary">Sign Up</Link>
                            </div>
                        </div>
                    </div>
                )}

                {/* Stats Cards */}
                <div className="stats-grid" style={{ marginBottom: '24px' }}>
                    <div className="stat-card">
                        <div className="stat-value" style={{ color: 'var(--blue)' }}>{stocks.length}</div>
                        <div className="stat-label">Total Stocks</div>
                    </div>
                    <div className="stat-card">
                        <div className="stat-value" style={{ color: 'var(--green)' }}>{gainers}</div>
                        <div className="stat-label">Advancing</div>
                    </div>
                    <div className="stat-card">
                        <div className="stat-value" style={{ color: 'var(--red)' }}>{losers}</div>
                        <div className="stat-label">Declining</div>
                    </div>
                    <div className="stat-card">
                        {topGainer && (
                            <>
                                <div className="stat-value" style={{ color: 'var(--green)', fontSize: '1.25rem' }}>
                                    {topGainer.ticker.replace('.NS', '')}
                                </div>
                                <div className="stat-label">Top Gainer +{(((topGainer.close - topGainer.open) / topGainer.open) * 100).toFixed(2)}%</div>
                            </>
                        )}
                    </div>
                    <div className="stat-card">
                        {topLoser && (
                            <>
                                <div className="stat-value" style={{ color: 'var(--red)', fontSize: '1.25rem' }}>
                                    {topLoser.ticker.replace('.NS', '')}
                                </div>
                                <div className="stat-label">Top Loser {(((topLoser.close - topLoser.open) / topLoser.open) * 100).toFixed(2)}%</div>
                            </>
                        )}
                    </div>
                </div>

                {/* Charts Row */}
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '24px' }}>
                    <div className="card" style={{ overflow: 'hidden' }}>
                        <div className="card-header">Top Movers</div>
                        <div style={{ padding: '16px', height: '300px', position: 'relative' }}>
                            {stocks.length > 0 && <TopMoversChart stocks={stocks} />}
                        </div>
                    </div>
                    <div className="card" style={{ overflow: 'hidden' }}>
                        <div className="card-header">Market Breadth</div>
                        <div style={{ padding: '16px', height: '300px', position: 'relative' }}>
                            {stocks.length > 0 && <MarketSentimentChart stocks={stocks} />}
                        </div>
                    </div>
                </div>

                {/* Volume Chart */}
                <div className="card" style={{ marginBottom: '24px', overflow: 'hidden' }}>
                    <div className="card-header">Volume Leaders</div>
                    <div style={{ padding: '16px', height: '220px', position: 'relative' }}>
                        {stocks.length > 0 && <VolumeChart stocks={stocks} />}
                    </div>
                </div>

                {/* Nifty 50 Stock List Section - Sorted by Ranking */}
                <div className="card">
                    <div className="card-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span>
                            Nifty 50 Stocks
                            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginLeft: '8px' }}>
                                (Sorted by Performance)
                            </span>
                        </span>
                        <div style={{ display: 'flex', gap: '8px' }}>
                            <button
                                onClick={() => setViewMode('table')}
                                className={`btn ${viewMode === 'table' ? 'btn-primary' : 'btn-secondary'}`}
                                style={{ padding: '4px 12px', fontSize: '0.75rem' }}
                            >
                                Table
                            </button>
                            <button
                                onClick={() => setViewMode('grid')}
                                className={`btn ${viewMode === 'grid' ? 'btn-primary' : 'btn-secondary'}`}
                                style={{ padding: '4px 12px', fontSize: '0.75rem' }}
                            >
                                Grid
                            </button>
                        </div>
                    </div>

                    {/* Scrollable Table/Grid Container */}
                    <div className="scrollbar-hidden" style={{
                        maxHeight: '500px',
                        overflowY: 'auto',
                        borderRadius: '0 0 8px 8px'
                    }}>
                        {viewMode === 'table' ? (
                            <StockTable stocks={filteredStocks} showRank={true} />
                        ) : (
                            <div className="card-body" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: '12px' }}>
                                {filteredStocks.map((stock, index) => {
                                    const change = stock.close - stock.open;
                                    const changePct = ((change / stock.open) * 100);
                                    const isPositive = change >= 0;
                                    return (
                                        <a key={stock.ticker} href={`/stocks/${stock.ticker}`} className="stock-card">
                                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                                <div className="ticker">{stock.ticker.replace('.NS', '')}</div>
                                                <span style={{
                                                    fontSize: '0.75rem',
                                                    color: 'var(--text-muted)',
                                                    background: 'var(--bg-elevated)',
                                                    padding: '2px 6px',
                                                    borderRadius: '4px'
                                                }}>
                                                    #{index + 1}
                                                </span>
                                            </div>
                                            <div className="price" style={{ color: isPositive ? 'var(--green)' : 'var(--red)' }}>
                                                ₹{stock.close.toFixed(2)}
                                            </div>
                                            <div className="change" style={{ color: isPositive ? 'var(--green)' : 'var(--red)' }}>
                                                {isPositive ? '▲' : '▼'} {changePct.toFixed(2)}%
                                            </div>
                                        </a>
                                    );
                                })}
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}
