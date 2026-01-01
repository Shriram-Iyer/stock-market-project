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
import { Stock } from '@/utils/api';

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

interface VolumeChartProps {
    stocks: Stock[];
}

export default function VolumeChart({ stocks }: VolumeChartProps) {
    const topByVolume = [...stocks]
        .sort((a, b) => (b.volume || 0) - (a.volume || 0))
        .slice(0, 10);

    const chartData = {
        labels: topByVolume.map(s => s.ticker.replace('.NS', '')),
        datasets: [
            {
                label: 'Volume (M)',
                data: topByVolume.map(s => (s.volume || 0) / 1000000),
                backgroundColor: 'rgba(41, 98, 255, 0.3)',
                borderColor: 'rgb(41, 98, 255)',
                borderWidth: 2,
                fill: true,
                tension: 0.4,
                pointRadius: 3,
                pointBackgroundColor: 'rgb(41, 98, 255)',
            },
        ],
    };

    const options = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: { display: false },
        },
        scales: {
            x: {
                ticks: { color: '#787b86' },
                grid: { display: false },
            },
            y: {
                ticks: { color: '#787b86' },
                grid: { color: 'rgba(42, 46, 57, 0.5)' },
            },
        },
    };

    return (
        <div style={{ width: '100%', height: '100%' }}>
            <Line data={chartData} options={options} />
        </div>
    );
}
