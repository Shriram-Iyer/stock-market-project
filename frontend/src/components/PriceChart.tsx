'use client';

import { Line } from 'react-chartjs-2';
import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend,
    Filler,
} from 'chart.js';

ChartJS.register(
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend,
    Filler
);

interface PriceChartProps {
    data: {
        date: string;
        close: number;
        ma_50?: number;
    }[];
    ticker: string;
}

export default function PriceChart({ data, ticker }: PriceChartProps) {
    const chartData = {
        labels: data.map(d => d.date),
        datasets: [
            {
                label: 'Close Price',
                data: data.map(d => d.close),
                borderColor: 'rgb(59, 130, 246)',
                backgroundColor: 'rgba(59, 130, 246, 0.1)',
                fill: true,
                tension: 0.1,
            },
            {
                label: 'MA 50',
                data: data.map(d => d.ma_50 || null),
                borderColor: 'rgb(251, 146, 60)',
                backgroundColor: 'transparent',
                borderDash: [5, 5],
                pointRadius: 0,
            },
        ],
    };

    const options = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                position: 'top' as const,
                labels: {
                    color: '#94a3b8',
                },
            },
            title: {
                display: true,
                text: `${ticker} Price History`,
                color: '#f8fafc',
                font: {
                    size: 16,
                },
            },
        },
        scales: {
            x: {
                ticks: {
                    color: '#94a3b8',
                    maxTicksLimit: 10,
                },
                grid: {
                    color: 'rgba(71, 85, 105, 0.3)',
                },
            },
            y: {
                ticks: {
                    color: '#94a3b8',
                    callback: function (value: number | string) {
                        return '₹' + Number(value).toLocaleString('en-IN');
                    },
                },
                grid: {
                    color: 'rgba(71, 85, 105, 0.3)',
                },
            },
        },
        interaction: {
            intersect: false,
            mode: 'index' as const,
        },
    };

    return (
        <div className="chart-container h-96">
            <Line data={chartData} options={options} />
        </div>
    );
}
