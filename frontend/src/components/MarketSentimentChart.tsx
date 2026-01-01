'use client';

import { Doughnut } from 'react-chartjs-2';
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js';
import { Stock } from '@/utils/api';

ChartJS.register(ArcElement, Tooltip, Legend);

interface MarketSentimentProps {
    stocks: Stock[];
}

export default function MarketSentimentChart({ stocks }: MarketSentimentProps) {
    const gainers = stocks.filter(s => s.close > s.open).length;
    const losers = stocks.filter(s => s.close < s.open).length;
    const unchanged = stocks.filter(s => s.close === s.open).length;

    const chartData = {
        labels: ['Gainers', 'Losers', 'Unchanged'],
        datasets: [
            {
                data: [gainers, losers, unchanged],
                backgroundColor: [
                    'rgba(38, 166, 154, 0.8)',
                    'rgba(239, 83, 80, 0.8)',
                    'rgba(120, 123, 134, 0.8)',
                ],
                borderColor: [
                    'rgb(38, 166, 154)',
                    'rgb(239, 83, 80)',
                    'rgb(120, 123, 134)',
                ],
                borderWidth: 2,
                hoverOffset: 10,
            },
        ],
    };

    const options = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                position: 'bottom' as const,
                labels: { color: '#787b86', padding: 15, usePointStyle: true },
            },
        },
        cutout: '65%',
    };

    const totalMovers = gainers + losers;
    const bullishPct = totalMovers > 0 ? (gainers / totalMovers * 100).toFixed(0) : '0';

    return (
        <div style={{ width: '100%', height: '100%', position: 'relative' }}>
            <Doughnut data={chartData} options={options} />
            <div style={{
                position: 'absolute',
                top: '40%',
                left: '50%',
                transform: 'translate(-50%, -50%)',
                textAlign: 'center'
            }}>
                <p style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#26a69a', margin: 0 }}>{bullishPct}%</p>
                <p style={{ fontSize: '0.75rem', color: '#787b86', margin: 0 }}>Bullish</p>
            </div>
        </div>
    );
}
