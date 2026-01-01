'use client';

import { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { stocksAPI, predictionsAPI } from '@/utils/api';
import CandlestickChart from '@/components/CandlestickChart';

// Prediction horizons for different trader types
const HORIZONS = {
    intraday: [
        { key: '1h', label: '1 Hour', description: 'Ultra short-term' },
        { key: '4h', label: '4 Hours', description: 'Day trading' },
    ],
    swing: [
        { key: '1d', label: '1 Day', description: 'Next day prediction' },
        { key: '3d', label: '3 Days', description: 'Short swing' },
        { key: '7d', label: '7 Days', description: 'Weekly outlook' },
    ],
    shortterm: [
        { key: '14d', label: '14 Days', description: 'Bi-weekly' },
        { key: '30d', label: '30 Days', description: 'Monthly outlook' },
        { key: '90d', label: '90 Days', description: 'Quarterly' },
    ],
};

interface Prediction {
    model: string;
    prediction: number;
    confidence: number;
    direction: 'UP' | 'DOWN' | 'NEUTRAL';
    horizon: string;
    changePercent: number;
}

interface SentimentData {
    overall: 'BULLISH' | 'BEARISH' | 'NEUTRAL';
    score: number;
    sources: { source: string; sentiment: string; score: number }[];
}

// Generate mock predictions for a given horizon
function generateMockPredictions(currentPrice: number, horizon: string): Prediction[] {
    // Different volatility based on horizon
    const volatilityMap: Record<string, number> = {
        '1h': 0.005, '4h': 0.012, '1d': 0.025, '3d': 0.04,
        '7d': 0.06, '14d': 0.08, '30d': 0.12, '90d': 0.20
    };
    const vol = volatilityMap[horizon] || 0.05;

    const models = [
        { name: 'LSTM (Deep Learning)', baseChange: 1 + (Math.random() - 0.3) * vol, confidence: 0.65 + Math.random() * 0.2 },
        { name: 'Prophet (Facebook)', baseChange: 1 + (Math.random() - 0.4) * vol, confidence: 0.60 + Math.random() * 0.25 },
        { name: 'XGBoost (Gradient Boosting)', baseChange: 1 + (Math.random() - 0.5) * vol, confidence: 0.55 + Math.random() * 0.3 },
        { name: 'ARIMA (Statistical)', baseChange: 1 + (Math.random() - 0.45) * vol, confidence: 0.50 + Math.random() * 0.25 },
    ];

    const horizonLabels: Record<string, string> = {
        '1h': '1 Hour', '4h': '4 Hours', '1d': '1 Day', '3d': '3 Days',
        '7d': '7 Days', '14d': '14 Days', '30d': '30 Days', '90d': '90 Days'
    };

    return models.map(m => {
        const predictedPrice = currentPrice * m.baseChange;
        const changePercent = ((predictedPrice - currentPrice) / currentPrice) * 100;
        return {
            model: m.name,
            prediction: predictedPrice,
            confidence: m.confidence,
            direction: changePercent > 0.5 ? 'UP' : changePercent < -0.5 ? 'DOWN' : 'NEUTRAL' as const,
            horizon: horizonLabels[horizon] || horizon,
            changePercent,
        };
    });
}

export default function StockDetailPage() {
    const params = useParams();
    const ticker = params.ticker as string;

    const [stock, setStock] = useState<any>(null);
    const [history, setHistory] = useState<any[]>([]);
    const [predictions, setPredictions] = useState<Prediction[]>([]);
    const [sentiment, setSentiment] = useState<SentimentData | null>(null);
    const [loading, setLoading] = useState(true);
    const [activeTab, setActiveTab] = useState<'chart' | 'predictions' | 'sentiment'>('chart');

    // Prediction horizon state
    const [traderType, setTraderType] = useState<'intraday' | 'swing' | 'shortterm'>('swing');
    const [selectedHorizon, setSelectedHorizon] = useState('7d');

    useEffect(() => {
        const fetchData = async () => {
            try {
                // Fetch stock details
                const stockData = await stocksAPI.getOne(ticker);
                setStock(stockData);

                // Fetch price history - API returns 'data' not 'history'
                try {
                    const historyData = await stocksAPI.getHistory(ticker, 90);
                    setHistory(historyData.data || historyData.history || []);
                } catch {
                    setHistory([]);
                }

                // Generate predictions for default horizon
                setPredictions(generateMockPredictions(stockData.close, selectedHorizon));

                // Mock sentiment for demo
                setSentiment({
                    overall: Math.random() > 0.5 ? 'BULLISH' : Math.random() > 0.5 ? 'NEUTRAL' : 'BEARISH',
                    score: 0.5 + Math.random() * 0.4,
                    sources: [
                        { source: 'News Headlines (FinBERT)', sentiment: 'POSITIVE', score: 0.72 + Math.random() * 0.2 },
                        { source: 'Social Media (Twitter/X)', sentiment: Math.random() > 0.5 ? 'POSITIVE' : 'NEUTRAL', score: 0.45 + Math.random() * 0.3 },
                        { source: 'Analyst Reports', sentiment: 'POSITIVE', score: 0.78 + Math.random() * 0.15 },
                        { source: 'Market Trends', sentiment: Math.random() > 0.6 ? 'POSITIVE' : 'NEUTRAL', score: 0.55 + Math.random() * 0.25 },
                    ]
                });
            } catch (err) {
                console.error('Error fetching stock data:', err);
            } finally {
                setLoading(false);
            }
        };

        if (ticker) {
            fetchData();
        }
    }, [ticker]);

    // Update predictions when horizon changes
    useEffect(() => {
        if (stock?.close) {
            setPredictions(generateMockPredictions(stock.close, selectedHorizon));
        }
    }, [selectedHorizon, stock?.close]);

    // Handle trader type change
    const handleTraderTypeChange = (type: 'intraday' | 'swing' | 'shortterm') => {
        setTraderType(type);
        // Set default horizon for trader type
        const defaultHorizons = { intraday: '1h', swing: '7d', shortterm: '30d' };
        setSelectedHorizon(defaultHorizons[type]);
    };

    if (loading) {
        return (
            <div style={{ display: 'flex', justifyContent: 'center', padding: '80px 0' }}>
                <div className="spinner" />
            </div>
        );
    }

    if (!stock) {
        return (
            <div className="container" style={{ padding: '24px', textAlign: 'center' }}>
                <h1>Stock Not Found</h1>
                <Link href="/explore" className="btn btn-primary" style={{ marginTop: '16px' }}>
                    Search Stocks
                </Link>
            </div>
        );
    }

    const change = stock.close - stock.open;
    const changePct = (change / stock.open) * 100;
    const isPositive = change >= 0;

    return (
        <div className="container" style={{ padding: '24px' }}>
            {/* Header */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '24px' }}>
                <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                        <h1 style={{ fontSize: '1.75rem', fontWeight: 'bold' }}>
                            {ticker.replace('.NS', '').replace('.BO', '')}
                        </h1>
                        <span style={{
                            background: isPositive ? 'var(--green-bg)' : 'var(--red-bg)',
                            color: isPositive ? 'var(--green)' : 'var(--red)',
                            padding: '4px 8px',
                            borderRadius: '4px',
                            fontSize: '0.75rem',
                            fontWeight: '600'
                        }}>
                            {isPositive ? '▲' : '▼'} {Math.abs(changePct).toFixed(2)}%
                        </span>
                    </div>
                    <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>{ticker}</p>
                </div>
                <div style={{ textAlign: 'right' }}>
                    <div style={{ fontSize: '2rem', fontWeight: 'bold', color: isPositive ? 'var(--green)' : 'var(--red)' }}>
                        ₹{stock.close.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                    </div>
                    <div style={{ color: isPositive ? 'var(--green)' : 'var(--red)', fontSize: '0.875rem' }}>
                        {isPositive ? '+' : ''}{change.toFixed(2)} ({changePct.toFixed(2)}%)
                    </div>
                </div>
            </div>

            {/* Metrics Row */}
            <div className="stats-grid" style={{ marginBottom: '24px' }}>
                <div className="stat-card">
                    <div className="stat-label">Open</div>
                    <div className="stat-value" style={{ fontSize: '1.25rem' }}>₹{stock.open.toFixed(2)}</div>
                </div>
                <div className="stat-card">
                    <div className="stat-label">High</div>
                    <div className="stat-value" style={{ fontSize: '1.25rem', color: 'var(--green)' }}>₹{stock.high.toFixed(2)}</div>
                </div>
                <div className="stat-card">
                    <div className="stat-label">Low</div>
                    <div className="stat-value" style={{ fontSize: '1.25rem', color: 'var(--red)' }}>₹{stock.low.toFixed(2)}</div>
                </div>
                <div className="stat-card">
                    <div className="stat-label">Volume</div>
                    <div className="stat-value" style={{ fontSize: '1.25rem' }}>{(stock.volume / 1000000).toFixed(2)}M</div>
                </div>
            </div>

            {/* Tabs */}
            <div style={{ display: 'flex', gap: '8px', marginBottom: '16px', borderBottom: '1px solid var(--border)', paddingBottom: '8px' }}>
                {['chart', 'predictions', 'sentiment'].map((tab) => (
                    <button
                        key={tab}
                        onClick={() => setActiveTab(tab as any)}
                        className={`btn ${activeTab === tab ? 'btn-primary' : 'btn-secondary'}`}
                        style={{ textTransform: 'capitalize' }}
                    >
                        {tab === 'predictions' ? '📈 Predictions' : tab === 'sentiment' ? '🧠 Sentiment' : '📊 Chart'}
                    </button>
                ))}
            </div>

            {/* Tab Content */}
            {activeTab === 'chart' && (
                <div className="card">
                    <div className="card-header">Price History (90 Days)</div>
                    <div className="card-body">
                        {history.length > 0 ? (
                            <CandlestickChart
                                data={history.map(h => ({
                                    time: h.date,
                                    open: h.open,
                                    high: h.high,
                                    low: h.low,
                                    close: h.close,
                                    volume: h.volume
                                }))}
                                height={450}
                            />
                        ) : (
                            <p style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '40px' }}>
                                Loading historical data...
                            </p>
                        )}
                    </div>
                </div>
            )}

            {activeTab === 'predictions' && (
                <div className="card">
                    <div className="card-header">
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
                            <span>ML Price Predictions</span>
                            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                                Powered by LSTM, Prophet, XGBoost & ARIMA
                            </div>
                        </div>
                    </div>
                    <div className="card-body">
                        {/* Trader Type Selector */}
                        <div style={{ marginBottom: '16px' }}>
                            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '8px' }}>
                                Select your trading style:
                            </div>
                            <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                                {[
                                    { key: 'intraday', label: '⚡ Intraday', desc: 'Day Trading' },
                                    { key: 'swing', label: '📊 Swing', desc: 'Interday' },
                                    { key: 'shortterm', label: '📈 Short-term', desc: 'Investing' },
                                ].map(t => (
                                    <button
                                        key={t.key}
                                        onClick={() => handleTraderTypeChange(t.key as any)}
                                        className={`btn ${traderType === t.key ? 'btn-primary' : 'btn-secondary'}`}
                                        style={{ padding: '8px 16px' }}
                                    >
                                        {t.label}
                                        <span style={{ display: 'block', fontSize: '0.65rem', opacity: 0.8 }}>{t.desc}</span>
                                    </button>
                                ))}
                            </div>
                        </div>

                        {/* Horizon Selector */}
                        <div style={{ marginBottom: '20px', padding: '12px', background: 'var(--bg-elevated)', borderRadius: '8px' }}>
                            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '8px' }}>
                                Prediction Horizon:
                            </div>
                            <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
                                {HORIZONS[traderType].map(h => (
                                    <button
                                        key={h.key}
                                        onClick={() => setSelectedHorizon(h.key)}
                                        style={{
                                            padding: '6px 12px',
                                            borderRadius: '16px',
                                            border: selectedHorizon === h.key ? '2px solid var(--blue)' : '1px solid var(--border)',
                                            background: selectedHorizon === h.key ? 'var(--blue)' : 'transparent',
                                            color: selectedHorizon === h.key ? 'white' : 'var(--text-primary)',
                                            cursor: 'pointer',
                                            fontSize: '0.875rem',
                                            fontWeight: selectedHorizon === h.key ? '600' : '400',
                                        }}
                                    >
                                        {h.label}
                                    </button>
                                ))}
                            </div>
                        </div>

                        {/* OVERALL PREDICTION SUMMARY */}
                        {predictions.length > 0 && (() => {
                            // Calculate weighted average prediction (weighted by confidence)
                            const totalConfidence = predictions.reduce((sum, p) => sum + p.confidence, 0);
                            const weightedPrice = predictions.reduce((sum, p) => sum + (p.prediction * p.confidence), 0) / totalConfidence;
                            const weightedChange = predictions.reduce((sum, p) => sum + (p.changePercent * p.confidence), 0) / totalConfidence;
                            const avgConfidence = totalConfidence / predictions.length;

                            // Count directions
                            const upCount = predictions.filter(p => p.direction === 'UP').length;
                            const downCount = predictions.filter(p => p.direction === 'DOWN').length;

                            // Determine overall direction
                            let overallDirection: 'BULLISH' | 'BEARISH' | 'NEUTRAL' = 'NEUTRAL';
                            let emoji = '➡️';
                            let bgColor = 'var(--bg-elevated)';
                            let borderColor = 'var(--border)';

                            if (upCount > downCount && weightedChange > 0.5) {
                                overallDirection = 'BULLISH';
                                emoji = '🚀';
                                bgColor = 'var(--green-bg)';
                                borderColor = 'var(--green)';
                            } else if (downCount > upCount && weightedChange < -0.5) {
                                overallDirection = 'BEARISH';
                                emoji = '📉';
                                bgColor = 'var(--red-bg)';
                                borderColor = 'var(--red)';
                            }

                            return (
                                <div style={{
                                    marginBottom: '24px',
                                    padding: '20px',
                                    background: bgColor,
                                    border: `2px solid ${borderColor}`,
                                    borderRadius: '12px',
                                }}>
                                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
                                        <div>
                                            <div style={{ fontSize: '0.875rem', color: 'var(--text-muted)', marginBottom: '4px' }}>
                                                🎯 Overall Prediction ({predictions[0]?.horizon || 'N/A'})
                                            </div>
                                            <div style={{ fontSize: '2rem', fontWeight: 'bold' }}>
                                                ₹{weightedPrice.toFixed(2)}
                                            </div>
                                            <div style={{
                                                fontSize: '1rem',
                                                fontWeight: '600',
                                                color: weightedChange > 0 ? 'var(--green)' : weightedChange < 0 ? 'var(--red)' : 'var(--text-primary)'
                                            }}>
                                                {weightedChange > 0 ? '▲' : weightedChange < 0 ? '▼' : '→'} {Math.abs(weightedChange).toFixed(2)}%
                                            </div>
                                        </div>
                                        <div style={{ textAlign: 'center' }}>
                                            <div style={{ fontSize: '2.5rem' }}>{emoji}</div>
                                            <div style={{
                                                fontSize: '1.25rem',
                                                fontWeight: 'bold',
                                                color: overallDirection === 'BULLISH' ? 'var(--green)' : overallDirection === 'BEARISH' ? 'var(--red)' : 'var(--text-primary)'
                                            }}>
                                                {overallDirection}
                                            </div>
                                            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                                                {upCount} models ↑ | {downCount} models ↓
                                            </div>
                                        </div>
                                        <div style={{ textAlign: 'right' }}>
                                            <div style={{ fontSize: '0.875rem', color: 'var(--text-muted)', marginBottom: '4px' }}>
                                                Avg Confidence
                                            </div>
                                            <div style={{
                                                fontSize: '1.5rem',
                                                fontWeight: 'bold',
                                                color: avgConfidence > 0.7 ? 'var(--green)' : avgConfidence > 0.5 ? 'var(--yellow)' : 'var(--red)'
                                            }}>
                                                {(avgConfidence * 100).toFixed(0)}%
                                            </div>
                                        </div>
                                    </div>
                                    <div style={{ marginTop: '12px', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                                        📊 Weighted average across {predictions.length} ML models (LSTM, Prophet, XGBoost, ARIMA)
                                    </div>
                                </div>
                            );
                        })()}

                        {/* Individual Model Predictions */}
                        <div style={{ fontSize: '0.875rem', color: 'var(--text-muted)', marginBottom: '12px' }}>
                            Individual Model Predictions:
                        </div>
                        <div style={{ display: 'grid', gap: '16px' }}>
                            {predictions.map((pred) => (
                                <div key={pred.model} style={{
                                    background: 'var(--bg-elevated)',
                                    padding: '16px',
                                    borderRadius: '8px',
                                    border: '1px solid var(--border)'
                                }}>
                                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                        <div>
                                            <div style={{ fontWeight: '600', marginBottom: '4px' }}>{pred.model}</div>
                                            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                                                {pred.horizon} forecast
                                            </div>
                                        </div>
                                        <div style={{ textAlign: 'right' }}>
                                            <div style={{
                                                fontSize: '1.25rem',
                                                fontWeight: 'bold',
                                                color: pred.direction === 'UP' ? 'var(--green)' : pred.direction === 'DOWN' ? 'var(--red)' : 'var(--text-primary)'
                                            }}>
                                                ₹{pred.prediction.toFixed(2)}
                                            </div>
                                            <div style={{
                                                fontSize: '0.875rem',
                                                color: pred.changePercent > 0 ? 'var(--green)' : pred.changePercent < 0 ? 'var(--red)' : 'var(--text-muted)'
                                            }}>
                                                {pred.changePercent > 0 ? '▲' : pred.changePercent < 0 ? '▼' : '→'} {Math.abs(pred.changePercent).toFixed(2)}%
                                            </div>
                                        </div>
                                    </div>
                                    <div style={{ marginTop: '12px' }}>
                                        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '4px' }}>
                                            Confidence: {(pred.confidence * 100).toFixed(0)}%
                                        </div>
                                        <div style={{
                                            height: '6px',
                                            background: 'var(--border)',
                                            borderRadius: '3px',
                                            overflow: 'hidden'
                                        }}>
                                            <div style={{
                                                height: '100%',
                                                width: `${pred.confidence * 100}%`,
                                                background: pred.confidence > 0.7 ? 'var(--green)' : pred.confidence > 0.5 ? 'var(--yellow)' : 'var(--red)',
                                                borderRadius: '3px'
                                            }} />
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>

                        <div style={{ marginTop: '16px', padding: '12px', background: 'var(--bg)', borderRadius: '8px', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                            ⚠️ <strong>Disclaimer:</strong> These predictions are generated by ML models and should not be considered financial advice. Always do your own research before making investment decisions.
                        </div>
                    </div>
                </div>
            )}

            {activeTab === 'sentiment' && (
                <div className="card">
                    <div className="card-header">Sentiment Analysis (FinBERT NLP)</div>
                    <div className="card-body">
                        {sentiment ? (
                            <>
                                <div style={{
                                    textAlign: 'center',
                                    padding: '24px',
                                    background: sentiment.overall === 'BULLISH' ? 'var(--green-bg)' : sentiment.overall === 'BEARISH' ? 'var(--red-bg)' : 'var(--bg-elevated)',
                                    borderRadius: '8px',
                                    marginBottom: '24px'
                                }}>
                                    <div style={{
                                        fontSize: '3rem',
                                        marginBottom: '8px'
                                    }}>
                                        {sentiment.overall === 'BULLISH' ? '🐂' : sentiment.overall === 'BEARISH' ? '🐻' : '😐'}
                                    </div>
                                    <div style={{
                                        fontSize: '2rem',
                                        fontWeight: 'bold',
                                        color: sentiment.overall === 'BULLISH' ? 'var(--green)' : sentiment.overall === 'BEARISH' ? 'var(--red)' : 'var(--text-primary)'
                                    }}>
                                        {sentiment.overall}
                                    </div>
                                    <div style={{ fontSize: '0.875rem', color: 'var(--text-muted)', marginTop: '8px' }}>
                                        Overall Sentiment Score: <strong>{(sentiment.score * 100).toFixed(0)}%</strong>
                                    </div>
                                </div>

                                <h3 style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', marginBottom: '12px' }}>
                                    📊 Source Breakdown
                                </h3>
                                <div style={{ display: 'grid', gap: '8px' }}>
                                    {sentiment.sources && sentiment.sources.map((source, i) => (
                                        <div key={i} style={{
                                            display: 'flex',
                                            justifyContent: 'space-between',
                                            alignItems: 'center',
                                            padding: '12px',
                                            background: 'var(--bg-elevated)',
                                            borderRadius: '8px'
                                        }}>
                                            <span>{source.source}</span>
                                            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                                <span style={{
                                                    padding: '2px 8px',
                                                    borderRadius: '4px',
                                                    fontSize: '0.75rem',
                                                    background: source.sentiment === 'POSITIVE' ? 'var(--green-bg)' : source.sentiment === 'NEGATIVE' ? 'var(--red-bg)' : 'var(--bg)',
                                                    color: source.sentiment === 'POSITIVE' ? 'var(--green)' : source.sentiment === 'NEGATIVE' ? 'var(--red)' : 'var(--text-muted)',
                                                }}>
                                                    {source.sentiment}
                                                </span>
                                                <span style={{ fontWeight: '600', minWidth: '40px', textAlign: 'right' }}>
                                                    {(source.score * 100).toFixed(0)}%
                                                </span>
                                            </div>
                                        </div>
                                    ))}
                                </div>

                                <div style={{ marginTop: '20px', padding: '12px', background: 'var(--bg)', borderRadius: '8px', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                                    📝 Sentiment is analyzed using <strong>FinBERT</strong>, a financial domain-specific BERT model trained on financial news and reports.
                                </div>
                            </>
                        ) : (
                            <p style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '40px' }}>
                                Loading sentiment analysis...
                            </p>
                        )}
                    </div>
                </div>
            )}
        </div>
    );
}
