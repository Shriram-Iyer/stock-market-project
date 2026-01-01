'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useAuth } from '@/utils/AuthContext';
import { useTheme } from '@/utils/ThemeContext';

export default function Navbar() {
    const { user, logout, isAuthenticated } = useAuth();
    const { theme, toggleTheme } = useTheme();
    const pathname = usePathname();

    const isActive = (path: string) => pathname === path;

    return (
        <nav className="navbar">
            <Link href="/" className="nav-logo">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M3 17l6-6 4 4 8-8V4h-3l3-3 3 3h-3v4l-8 8-4-4-6 6-2-2z" />
                </svg>
                StockDash
            </Link>

            <div className="nav-links">
                <Link href="/" className={`nav-link ${isActive('/') ? 'active' : ''}`}>
                    Dashboard
                </Link>
                <Link href="/explore" className={`nav-link ${isActive('/explore') ? 'active' : ''}`}>
                    Explore
                </Link>
                {isAuthenticated && (
                    <>
                        <Link href="/portfolio" className={`nav-link ${isActive('/portfolio') ? 'active' : ''}`}>
                            Portfolio
                        </Link>
                        <Link href="/wishlist" className={`nav-link ${isActive('/wishlist') ? 'active' : ''}`}>
                            Watchlist
                        </Link>
                    </>
                )}
            </div>

            <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: '12px' }}>
                {/* Theme Toggle Button */}
                <button
                    onClick={toggleTheme}
                    className="btn btn-secondary"
                    style={{
                        padding: '8px',
                        minWidth: '40px',
                        fontSize: '1.1rem',
                    }}
                    title={theme === 'dark' ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
                >
                    {theme === 'dark' ? '☀️' : '🌙'}
                </button>

                {isAuthenticated ? (
                    <>
                        <span style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
                            {user?.username}
                        </span>
                        <button onClick={logout} className="btn btn-secondary">
                            Logout
                        </button>
                    </>
                ) : (
                    <>
                        <Link href="/login" className="nav-link">
                            Login
                        </Link>
                        <Link href="/signup" className="btn btn-primary">
                            Sign Up
                        </Link>
                    </>
                )}
            </div>
        </nav>
    );
}
