'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/utils/AuthContext';
import { portfolioAPI, PortfolioHolding } from '@/utils/api';
import Link from 'next/link';
import StockSearch from '@/components/StockSearch';

export default function PortfolioPage() {
    const { isAuthenticated, loading: authLoading } = useAuth();
    const [holdings, setHoldings] = useState<PortfolioHolding[]>([]);
    const [summary, setSummary] = useState<any>(null);
    const [risk, setRisk] = useState<any>(null);
    const [loading, setLoading] = useState(true);
    const [showAddForm, setShowAddForm] = useState(false);
    const [formData, setFormData] = useState({ ticker: '', quantity: '', buyPrice: '' });

    useEffect(() => {
        if (!authLoading && isAuthenticated) {
            fetchPortfolio();
        } else if (!authLoading && !isAuthenticated) {
            setLoading(false);
        }
    }, [isAuthenticated, authLoading]);

    const fetchPortfolio = async () => {
        try {
            const [portfolioData, riskData] = await Promise.all([
                portfolioAPI.get(),
                portfolioAPI.getRisk(),
            ]);
            setHoldings(portfolioData.holdings);
            setSummary(portfolioData.summary);
            setRisk(riskData);
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    const handleAdd = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            // Auto-append .NS if not present
            let ticker = formData.ticker.toUpperCase().trim();
            if (!ticker.endsWith('.NS') && !ticker.endsWith('.BO')) {
                ticker = ticker + '.NS';
            }
            await portfolioAPI.add(
                ticker,
                parseFloat(formData.quantity),
                parseFloat(formData.buyPrice)
            );
            setFormData({ ticker: '', quantity: '', buyPrice: '' });
            setShowAddForm(false);
            fetchPortfolio();
        } catch (err) {
            console.error(err);
        }
    };

    const handleRemove = async (id: string) => {
        try {
            // Optimistic UI update - remove from local state first
            setHoldings(prev => prev.filter(h => h.id !== id));
            await portfolioAPI.remove(id);
            // Refresh to get updated summary
            fetchPortfolio();
        } catch (err) {
            console.error('Failed to remove holding:', err);
            // Revert on error by refetching
            fetchPortfolio();
        }
    };

    if (!isAuthenticated && !authLoading) {
        return (
            <div className="text-center py-20">
                <p className="text-xl text-slate-400">Please login to view your portfolio</p>
                <Link href="/login" className="btn btn-primary inline-block mt-4">Login</Link>
            </div>
        );
    }

    if (loading) {
        return <div className="flex justify-center py-20"><div className="spinner" /></div>;
    }

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <h1 className="text-3xl font-bold">My Portfolio</h1>
                <button onClick={() => setShowAddForm(!showAddForm)} className="btn btn-primary" style={{ marginTop: '16px' }}>
                    {showAddForm ? 'Cancel' : '+ Add Holding'}
                </button>
            </div>

            {/* Add Form */}
            {showAddForm && (
                <form onSubmit={handleAdd} className="glass-card p-4 flex gap-4 flex-wrap" style={{ marginTop: '16px' }}>
                    <div style={{ flex: 1, minWidth: '200px' }}>
                        <StockSearch
                            placeholder="Search ticker (e.g., TCS, RELIANCE)"
                            onSelect={(ticker) => setFormData({ ...formData, ticker })}
                            showNavigate={false}
                        />
                        {formData.ticker && (
                            <div style={{ marginTop: '8px', color: 'var(--green)', fontSize: '0.875rem' }}>
                                Selected: {formData.ticker}
                            </div>
                        )}
                    </div>
                    <input
                        type="number"
                        placeholder="Quantity"
                        value={formData.quantity}
                        onChange={(e) => setFormData({ ...formData, quantity: e.target.value })}
                        className="input-field w-32"
                        step="0.01"
                        required
                    />
                    <input
                        type="number"
                        placeholder="Buy Price"
                        value={formData.buyPrice}
                        onChange={(e) => setFormData({ ...formData, buyPrice: e.target.value })}
                        className="input-field w-32"
                        step="0.01"
                        required
                    />
                    <button type="submit" className="btn btn-primary">Add</button>
                </form>
            )}

            {/* Summary Cards */}
            {summary && (
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="glass-card p-4">
                        <p className="text-slate-400 text-sm">Investment</p>
                        <p className="text-xl font-bold">₹{summary.total_investment.toLocaleString('en-IN')}</p>
                    </div>
                    <div className="glass-card p-4">
                        <p className="text-slate-400 text-sm">Current Value</p>
                        <p className="text-xl font-bold">₹{summary.total_current_value.toLocaleString('en-IN')}</p>
                    </div>
                    <div className="glass-card p-4">
                        <p className="text-slate-400 text-sm">P&L</p>
                        <p className={`text-xl font-bold ${summary.total_pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                            ₹{summary.total_pnl.toLocaleString('en-IN')} ({summary.total_pnl_pct.toFixed(2)}%)
                        </p>
                    </div>
                    {risk && (
                        <div className="glass-card p-4">
                            <p className="text-slate-400 text-sm">Risk Level</p>
                            <p className={`text-xl font-bold ${risk.risk_level === 'Low' ? 'text-green-400' : risk.risk_level === 'High' ? 'text-red-400' : 'text-yellow-400'}`}>
                                {risk.risk_level} ({risk.risk_score}/10)
                            </p>
                        </div>
                    )}
                </div>
            )}

            {/* Holdings Table */}
            <div className="glass-card overflow-x-auto">
                <table className="data-table">
                    <thead>
                        <tr>
                            <th>Ticker</th>
                            <th>Qty</th>
                            <th>Buy Price</th>
                            <th>Current</th>
                            <th>P&L</th>
                            <th></th>
                        </tr>
                    </thead>
                    <tbody>
                        {holdings.map((h) => (
                            <tr key={h.id}>
                                <td>
                                    <Link href={`/stocks/${h.ticker}`} className="text-blue-400 hover:underline">
                                        {h.ticker.replace('.NS', '')}
                                    </Link>
                                </td>
                                <td>{h.quantity}</td>
                                <td>₹{h.buy_price.toFixed(2)}</td>
                                <td>₹{(h.current_price || h.buy_price).toFixed(2)}</td>
                                <td className={h.pnl && h.pnl >= 0 ? 'text-green-400' : 'text-red-400'}>
                                    ₹{h.pnl?.toFixed(2)} ({h.pnl_pct?.toFixed(2)}%)
                                </td>
                                <td>
                                    <button onClick={() => handleRemove(h.id)} className="text-red-400 hover:text-red-300">
                                        ✕
                                    </button>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
                {holdings.length === 0 && (
                    <p className="text-center py-8 text-slate-400">No holdings yet. Add your first stock!</p>
                )}
            </div>
        </div>
    );
}
