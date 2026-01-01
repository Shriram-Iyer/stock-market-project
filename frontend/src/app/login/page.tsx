'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useAuth } from '@/utils/AuthContext';

export default function LoginPage() {
    const [identifier, setIdentifier] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

    const { login, isAuthenticated, loading: authLoading } = useAuth();
    const router = useRouter();

    // Redirect if already logged in
    useEffect(() => {
        if (!authLoading && isAuthenticated) {
            router.push('/');
        }
    }, [isAuthenticated, authLoading, router]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        setLoading(true);

        try {
            await login(identifier, password);
            router.push('/');
        } catch (err: any) {
            setError(err.response?.data?.error || 'Login failed');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="max-w-md mx-auto mt-20">
            <div className="glass-card p-8" style={{ borderRadius: '16px' }}>
                <h1 className="text-2xl font-bold text-center mb-2">Welcome Back</h1>
                <p className="text-center text-slate-400 mb-6">Login with your email or username</p>

                {error && (
                    <div className="bg-red-900/50 border border-red-500 text-red-300 px-4 py-3 rounded-xl mb-4">
                        {error}
                    </div>
                )}

                <form onSubmit={handleSubmit} className="space-y-5">
                    <div>
                        <label className="block text-sm text-slate-400 mb-2">Email or Username</label>
                        <input
                            type="text"
                            value={identifier}
                            onChange={(e) => setIdentifier(e.target.value)}
                            className="input-field"
                            placeholder="Enter email or username"
                            required
                        />
                    </div>

                    <div>
                        <label className="block text-sm text-slate-400 mb-2">Password</label>
                        <input
                            type="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            className="input-field"
                            placeholder="••••••••"
                            required
                        />
                    </div>

                    <button
                        type="submit"
                        disabled={loading}
                        className="btn btn-primary w-full disabled:opacity-50"
                    >
                        {loading ? 'Logging in...' : '🚀 Login'}
                    </button>
                </form>

                <p className="text-center text-slate-400 mt-6">
                    Don't have an account?{' '}
                    <Link href="/signup" className="text-blue-400 hover:underline font-semibold">
                        Sign up
                    </Link>
                </p>
            </div>
        </div>
    );
}
