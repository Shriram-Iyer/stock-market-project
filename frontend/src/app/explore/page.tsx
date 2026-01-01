'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import StockSearch from '@/components/StockSearch';

export default function ExplorePage() {
    const [recentSearches, setRecentSearches] = useState<string[]>([]);
    const router = useRouter();

    // Load recent searches from localStorage
    useEffect(() => {
        const saved = localStorage.getItem('recentSearches');
        if (saved) {
            setRecentSearches(JSON.parse(saved));
        }
    }, []);

    const saveToRecent = (ticker: string) => {
        const updated = [ticker, ...recentSearches.filter(t => t !== ticker)].slice(0, 10);
        setRecentSearches(updated);
        localStorage.setItem('recentSearches', JSON.stringify(updated));
    };

    const handleStockSelect = (ticker: string) => {
        saveToRecent(ticker);
        router.push(`/stocks/${ticker}`);
    };

    // Popular stocks to show by default
    const popularStocks = [
        { ticker: 'RELIANCE.NS', name: 'Reliance Industries' },
        { ticker: 'TCS.NS', name: 'Tata Consultancy Services' },
        { ticker: 'INFY.NS', name: 'Infosys' },
        { ticker: 'HDFCBANK.NS', name: 'HDFC Bank' },
        { ticker: 'ICICIBANK.NS', name: 'ICICI Bank' },
        { ticker: 'BHARTIARTL.NS', name: 'Bharti Airtel' },
        { ticker: 'ITC.NS', name: 'ITC Limited' },
        { ticker: 'SBIN.NS', name: 'State Bank of India' },
        { ticker: 'HINDUNILVR.NS', name: 'Hindustan Unilever' },
        { ticker: 'KOTAKBANK.NS', name: 'Kotak Mahindra Bank' },
        { ticker: 'WIPRO.NS', name: 'Wipro' },
        { ticker: 'TATAMOTORS.NS', name: 'Tata Motors' },
    ];

    return (
        <div className="container" style={{ padding: '24px', maxWidth: '900px', margin: '0 auto' }}>
            <h1 style={{ fontSize: '1.75rem', fontWeight: 'bold', marginBottom: '8px' }}>
                Explore Stocks
            </h1>
            <p style={{ color: 'var(--text-muted)', marginBottom: '24px' }}>
                Search for any stock across all exchanges
            </p>

            {/* Search Box using StockSearch component */}
            <div style={{ marginBottom: '32px' }}>
                <StockSearch
                    placeholder="Search by ticker or company name (e.g., RELIANCE, TCS)"
                    onSelect={handleStockSelect}
                    showNavigate={false}
                />
            </div>

            {/* Recent Searches */}
            {recentSearches.length > 0 && (
                <div style={{ marginBottom: '32px' }}>
                    <h2 style={{ fontSize: '1rem', color: 'var(--text-secondary)', marginBottom: '12px' }}>
                        Recent Searches
                    </h2>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                        {recentSearches.map((ticker) => (
                            <Link
                                key={ticker}
                                href={`/stocks/${ticker}`}
                                className="btn btn-secondary"
                                style={{ fontSize: '0.8rem' }}
                            >
                                {ticker.replace('.NS', '').replace('.BO', '')}
                            </Link>
                        ))}
                    </div>
                </div>
            )}

            {/* Popular Stocks */}
            <div>
                <h2 style={{ fontSize: '1rem', color: 'var(--text-secondary)', marginBottom: '16px' }}>
                    Popular Stocks
                </h2>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(250px, 1fr))', gap: '12px' }}>
                    {popularStocks.map((stock) => (
                        <Link
                            key={stock.ticker}
                            href={`/stocks/${stock.ticker}`}
                            onClick={() => saveToRecent(stock.ticker)}
                            className="stock-card"
                            style={{ textDecoration: 'none' }}
                        >
                            <div className="ticker">{stock.ticker.replace('.NS', '')}</div>
                            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{stock.name}</div>
                        </Link>
                    ))}
                </div>
            </div>
        </div>
    );
}
