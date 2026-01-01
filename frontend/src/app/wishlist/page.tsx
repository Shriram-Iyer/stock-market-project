'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/utils/AuthContext';
import { wishlistAPI } from '@/utils/api';
import Link from 'next/link';
import StockSearch from '@/components/StockSearch';

interface WishlistItem {
    id: string;
    ticker: string;
    added_at: string;
    current_price?: number;
}

export default function WishlistPage() {
    const { isAuthenticated, loading: authLoading } = useAuth();
    const [items, setItems] = useState<WishlistItem[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (!authLoading && isAuthenticated) {
            fetchWishlist();
        } else if (!authLoading) {
            setLoading(false);
        }
    }, [isAuthenticated, authLoading]);

    const fetchWishlist = async () => {
        try {
            const data = await wishlistAPI.get();
            setItems(data.data);
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    const handleAdd = async (tickerToAdd: string) => {
        try {
            await wishlistAPI.add(tickerToAdd);
            fetchWishlist();
        } catch (err) {
            console.error(err);
        }
    };

    const handleRemove = async (id: string) => {
        await wishlistAPI.remove(id);
        fetchWishlist();
    };

    if (!isAuthenticated && !authLoading) {
        return (
            <div className="text-center py-20">
                <p className="text-xl text-slate-400">Please login to view your wishlist</p>
                <Link href="/login" className="btn btn-primary inline-block mt-4">Login</Link>
            </div>
        );
    }

    if (loading) {
        return <div className="flex justify-center py-20"><div className="spinner" /></div>;
    }

    return (
        <div className="space-y-6">
            <h1 className="text-3xl font-bold">Wishlist</h1>

            {/* Search & Add */}
            <div className="glass-card p-4">
                <StockSearch
                    placeholder="Search for a stock to add..."
                    onSelect={handleAdd}
                    showNavigate={false}
                />
            </div>

            {/* Wishlist Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {items.map((item) => (
                    <div key={item.id} className="stock-card flex justify-between items-center">
                        <div>
                            <Link href={`/stocks/${item.ticker}`} className="font-semibold text-lg hover:text-blue-400">
                                {item.ticker.replace('.NS', '')}
                            </Link>
                            {item.current_price && (
                                <p className="text-slate-400">₹{item.current_price.toFixed(2)}</p>
                            )}
                        </div>
                        <button onClick={() => handleRemove(item.id)} className="text-red-400 hover:text-red-300 text-xl">
                            ✕
                        </button>
                    </div>
                ))}
            </div>

            {items.length === 0 && (
                <p className="text-center py-10 text-slate-400">
                    Your wishlist is empty. Search for stocks to add!
                </p>
            )}
        </div>
    );
}
