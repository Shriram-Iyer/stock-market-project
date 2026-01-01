'use client';

import { Bar } from 'react-chartjs-2';
import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    BarElement,
    Title,
    Tooltip,
    Legend,
} from 'chart.js';
import { Stock } from '@/utils/api';

ChartJS.register(
    CategoryScale,
    LinearScale,
    BarElement,
    Title,
    Tooltip,
    Legend
);

interface TopMoversChartProps {
    stocks: Stock[];
}

export default function TopMoversChart({ stocks }: TopMoversChartProps) {
    const stocksWithChange = stocks.map(stock => ({
        ...stock,
        changePct: ((stock.close - stock.open) / stock.open) * 100,
    }));

    const sorted = [...stocksWithChange].sort((a, b) => b.changePct - a.changePct);
    const gainers = sorted.slice(0, 5);
    const losers = sorted.slice(-5).reverse();

    const chartData = {
        labels: [...gainers.map(s => s.ticker.replace('.NS', '')), ...losers.map(s => s.ticker.replace('.NS', ''))],
        datasets: [
            {
                label: 'Change %',
                data: [...gainers.map(s => s.changePct), ...losers.map(s => s.changePct)],
                backgroundColor: [
                    ...gainers.map(() => 'rgba(38, 166, 154, 0.8)'),
                    ...losers.map(() => 'rgba(239, 83, 80, 0.8)'),
                ],
                borderColor: [
                    ...gainers.map(() => 'rgb(38, 166, 154)'),
                    ...losers.map(() => 'rgb(239, 83, 80)'),
                ],
                borderWidth: 1,
                borderRadius: 4,
            },
        ],
    };

    const options = {
        indexAxis: 'y' as const,
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: { display: false },
            title: { display: false },
        },
        scales: {
            x: {
                ticks: { color: '#787b86' },
                grid: { color: 'rgba(42, 46, 57, 0.5)' },
            },
            y: {
                ticks: { color: '#787b86' },
                grid: { display: false },
            },
        },
    };

    return (
        <div style={{ width: '100%', height: '100%' }}>
            <Bar data={chartData} options={options} />
        </div>
    );
}
