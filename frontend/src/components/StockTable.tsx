'use client';

import Link from 'next/link';
import { Stock } from '@/utils/api';

interface StockTableProps {
    stocks: Stock[];
    showRank?: boolean;
}

export default function StockTable({ stocks, showRank = false }: StockTableProps) {
    return (
        <table className="stock-table">
            <thead>
                <tr>
                    {showRank && <th style={{ textAlign: 'center', width: '50px' }}>Rank</th>}
                    <th>Symbol</th>
                    <th style={{ textAlign: 'right' }}>LTP</th>
                    <th style={{ textAlign: 'right' }}>Change</th>
                    <th style={{ textAlign: 'right' }}>% Change</th>
                    <th style={{ textAlign: 'right' }}>Open</th>
                    <th style={{ textAlign: 'right' }}>High</th>
                    <th style={{ textAlign: 'right' }}>Low</th>
                    <th style={{ textAlign: 'right' }}>Volume</th>
                </tr>
            </thead>
            <tbody>
                {stocks.map((stock, index) => {
                    const change = stock.close - stock.open;
                    const changePct = ((change / stock.open) * 100);
                    const isPositive = change >= 0;

                    return (
                        <tr key={stock.ticker}>
                            {showRank && (
                                <td style={{ textAlign: 'center' }}>
                                    <span style={{
                                        display: 'inline-block',
                                        minWidth: '24px',
                                        padding: '2px 6px',
                                        borderRadius: '4px',
                                        fontSize: '0.75rem',
                                        fontWeight: '600',
                                        background: index < 3 ? 'var(--green-bg)' : index >= stocks.length - 3 ? 'var(--red-bg)' : 'var(--bg-elevated)',
                                        color: index < 3 ? 'var(--green)' : index >= stocks.length - 3 ? 'var(--red)' : 'var(--text-muted)'
                                    }}>
                                        {index + 1}
                                    </span>
                                </td>
                            )}
                            <td>
                                <Link href={`/stocks/${stock.ticker}`} className="ticker">
                                    {stock.ticker.replace('.NS', '')}
                                </Link>
                            </td>
                            <td style={{ textAlign: 'right' }} className="price">
                                ₹{stock.close.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                            </td>
                            <td style={{ textAlign: 'right' }} className={isPositive ? 'change-positive' : 'change-negative'}>
                                {isPositive ? '+' : ''}{change.toFixed(2)}
                            </td>
                            <td style={{ textAlign: 'right' }} className={isPositive ? 'change-positive' : 'change-negative'}>
                                {isPositive ? '+' : ''}{changePct.toFixed(2)}%
                            </td>
                            <td style={{ textAlign: 'right', color: 'var(--text-secondary)' }}>
                                ₹{stock.open.toFixed(2)}
                            </td>
                            <td style={{ textAlign: 'right', color: 'var(--green)' }}>
                                ₹{stock.high.toFixed(2)}
                            </td>
                            <td style={{ textAlign: 'right', color: 'var(--red)' }}>
                                ₹{stock.low.toFixed(2)}
                            </td>
                            <td style={{ textAlign: 'right', color: 'var(--text-secondary)' }}>
                                {(stock.volume / 1000000).toFixed(2)}M
                            </td>
                        </tr>
                    );
                })}
            </tbody>
        </table>
    );
}
