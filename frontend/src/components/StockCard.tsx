'use client';

import Link from 'next/link';
import { Stock } from '@/utils/api';

interface StockCardProps {
    stock: Stock;
}

export default function StockCard({ stock }: StockCardProps) {
    const priceChange = stock.close - stock.open;
    const priceChangePct = (priceChange / stock.open) * 100;
    const isPositive = priceChange >= 0;

    return (
        <Link href={`/stocks/${stock.ticker}`}>
            <div className="stock-card cursor-pointer">
                <div className="flex justify-between items-start mb-2">
                    <h3 className="font-semibold text-lg">
                        {stock.ticker.replace('.NS', '')}
                    </h3>
                    <span className="text-xs text-slate-400">NSE</span>
                </div>

                <div className="mb-3">
                    <span className="text-2xl font-bold">
                        ₹{stock.close.toLocaleString('en-IN', { maximumFractionDigits: 2 })}
                    </span>
                </div>

                <div className={`flex items-center gap-2 ${isPositive ? 'price-positive' : 'price-negative'}`}>
                    <span className="text-sm font-medium">
                        {isPositive ? '▲' : '▼'} {Math.abs(priceChange).toFixed(2)}
                    </span>
                    <span className="text-sm">
                        ({isPositive ? '+' : ''}{priceChangePct.toFixed(2)}%)
                    </span>
                </div>

                {stock.volatility && (
                    <div className="mt-3 pt-3 border-t border-slate-700">
                        <div className="flex justify-between text-xs text-slate-400">
                            <span>Volatility</span>
                            <span>{(stock.volatility * 100).toFixed(1)}%</span>
                        </div>
                        {stock.rsi_14 && (
                            <div className="flex justify-between text-xs text-slate-400 mt-1">
                                <span>RSI</span>
                                <span className={stock.rsi_14 > 70 ? 'text-red-400' : stock.rsi_14 < 30 ? 'text-green-400' : ''}>
                                    {stock.rsi_14.toFixed(1)}
                                </span>
                            </div>
                        )}
                    </div>
                )}
            </div>
        </Link>
    );
}
