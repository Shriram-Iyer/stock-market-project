'use client';

import { Stock } from '@/utils/api';

interface MarketTickerProps {
    stocks: Stock[];
}

export default function MarketTicker({ stocks }: MarketTickerProps) {
    // Get stocks for the ticker (duplicate for seamless loop)
    const tickerStocks = [...stocks.slice(0, 15), ...stocks.slice(0, 15)];

    return (
        <div className="ticker-wrapper">
            <div className="ticker-track">
                {tickerStocks.map((stock, index) => {
                    const change = stock.close - stock.open;
                    const changePct = ((change / stock.open) * 100);
                    const isPositive = change >= 0;

                    return (
                        <div key={`${stock.ticker}-${index}`} className="ticker-item">
                            <span className="ticker-name">{stock.ticker.replace('.NS', '')}</span>
                            <span className="ticker-price">₹{stock.close.toLocaleString('en-IN', { maximumFractionDigits: 2 })}</span>
                            <span className={`ticker-change ${isPositive ? 'positive' : 'negative'}`}>
                                {isPositive ? '▲' : '▼'} {Math.abs(changePct).toFixed(2)}%
                            </span>
                        </div>
                    );
                })}
            </div>

            <style jsx>{`
        .ticker-wrapper {
          background: var(--bg-card);
          border-bottom: 1px solid var(--border);
          overflow: hidden;
          white-space: nowrap;
        }

        .ticker-track {
          display: inline-flex;
          animation: scroll 60s linear infinite;
        }

        .ticker-track:hover {
          animation-play-state: paused;
        }

        .ticker-item {
          display: inline-flex;
          align-items: center;
          gap: 8px;
          padding: 10px 24px;
          border-right: 1px solid var(--border);
        }

        .ticker-name {
          font-size: 0.75rem;
          font-weight: 700;
          color: var(--text-secondary);
        }

        .ticker-price {
          font-size: 0.875rem;
          font-weight: 600;
          color: var(--text-primary);
          font-family: 'SF Mono', monospace;
        }

        .ticker-change {
          font-size: 0.75rem;
          font-weight: 600;
          padding: 2px 6px;
          border-radius: 3px;
        }

        .ticker-change.positive {
          background: rgba(38, 166, 154, 0.15);
          color: #26a69a;
        }

        .ticker-change.negative {
          background: rgba(239, 83, 80, 0.15);
          color: #ef5350;
        }

        @keyframes scroll {
          0% {
            transform: translateX(0);
          }
          100% {
            transform: translateX(-50%);
          }
        }
      `}</style>
        </div>
    );
}
