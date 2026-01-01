'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { stocksAPI } from '@/utils/api';

interface SearchResult {
    ticker: string;
    name?: string;
    exchange?: string;
}

interface StockSearchProps {
    placeholder?: string;
    className?: string;
    onSelect?: (ticker: string) => void;
    showNavigate?: boolean;
}

export default function StockSearch({
    placeholder = "Search stocks...",
    className = "",
    onSelect,
    showNavigate = true
}: StockSearchProps) {
    const [query, setQuery] = useState('');
    const [suggestions, setSuggestions] = useState<SearchResult[]>([]);
    const [loading, setLoading] = useState(false);
    const [showDropdown, setShowDropdown] = useState(false);
    const wrapperRef = useRef<HTMLDivElement>(null);
    const debounceRef = useRef<NodeJS.Timeout | null>(null);
    const router = useRouter();

    // Handle click outside to close dropdown
    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (wrapperRef.current && !wrapperRef.current.contains(event.target as Node)) {
                setShowDropdown(false);
            }
        };
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    // Debounced API search
    const searchStocks = useCallback(async (searchTerm: string) => {
        if (searchTerm.length < 2) {
            setSuggestions([]);
            setShowDropdown(false);
            setLoading(false);
            return;
        }

        setLoading(true);
        try {
            const response = await stocksAPI.search(searchTerm);
            const results = response.data || [];

            // Transform to SearchResult format
            const formattedResults: SearchResult[] = results.map((ticker: string) => ({
                ticker,
                name: ticker.replace('.NS', ' (NSE)').replace('.BO', ' (BSE)'),
                exchange: ticker.endsWith('.NS') ? 'NSE' : ticker.endsWith('.BO') ? 'BSE' : 'Unknown'
            }));

            setSuggestions(formattedResults.slice(0, 10));
            setShowDropdown(formattedResults.length > 0);
        } catch (err) {
            console.error('Search error:', err);
            // Fallback: Generate suggestions based on query
            const fallbackResults: SearchResult[] = [
                { ticker: `${searchTerm.toUpperCase()}.NS`, name: `${searchTerm.toUpperCase()} (NSE)`, exchange: 'NSE' },
                { ticker: `${searchTerm.toUpperCase()}.BO`, name: `${searchTerm.toUpperCase()} (BSE)`, exchange: 'BSE' },
            ];
            setSuggestions(fallbackResults);
            setShowDropdown(true);
        } finally {
            setLoading(false);
        }
    }, []);

    // Handle query change with debounce
    useEffect(() => {
        if (debounceRef.current) {
            clearTimeout(debounceRef.current);
        }

        if (query.length < 1) {
            setSuggestions([]);
            setShowDropdown(false);
            return;
        }

        setLoading(true);
        debounceRef.current = setTimeout(() => {
            searchStocks(query);
        }, 300); // 300ms debounce

        return () => {
            if (debounceRef.current) {
                clearTimeout(debounceRef.current);
            }
        };
    }, [query, searchStocks]);

    const handleSelect = (ticker: string) => {
        setQuery('');
        setSuggestions([]);
        setShowDropdown(false);

        if (onSelect) {
            onSelect(ticker);
        } else if (showNavigate) {
            router.push(`/stocks/${ticker}`);
        }
    };

    return (
        <div ref={wrapperRef} className={`stock-search ${className}`} style={{ position: 'relative' }}>
            <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onFocus={() => suggestions.length > 0 && setShowDropdown(true)}
                placeholder={placeholder}
                className="input-field"
                style={{ width: '100%' }}
            />

            {showDropdown && (
                <div className="search-dropdown" style={{
                    position: 'absolute',
                    top: '100%',
                    left: 0,
                    right: 0,
                    maxHeight: '300px',
                    overflowY: 'auto',
                    background: 'var(--bg-card)',
                    border: '1px solid var(--border)',
                    borderRadius: '8px',
                    boxShadow: '0 8px 24px rgba(0,0,0,0.3)',
                    zIndex: 1000,
                    marginTop: '4px'
                }}>
                    {loading ? (
                        <div style={{ padding: '12px', textAlign: 'center', color: 'var(--text-muted)' }}>
                            Searching...
                        </div>
                    ) : suggestions.length > 0 ? (
                        suggestions.map((result) => (
                            <div
                                key={result.ticker}
                                onClick={() => handleSelect(result.ticker)}
                                style={{
                                    padding: '12px 16px',
                                    cursor: 'pointer',
                                    display: 'flex',
                                    justifyContent: 'space-between',
                                    alignItems: 'center',
                                    borderBottom: '1px solid var(--border)',
                                    transition: 'background 0.2s'
                                }}
                                onMouseEnter={(e) => e.currentTarget.style.background = 'var(--bg-hover)'}
                                onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}
                            >
                                <div>
                                    <div style={{ fontWeight: 600, color: 'var(--blue)' }}>
                                        {result.ticker.replace('.NS', '').replace('.BO', '')}
                                    </div>
                                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                                        {result.exchange}
                                    </div>
                                </div>
                                <div style={{
                                    fontSize: '0.75rem',
                                    color: 'var(--text-muted)',
                                    textAlign: 'right'
                                }}>
                                    Click to {onSelect ? 'add' : 'view'}
                                </div>
                            </div>
                        ))
                    ) : (
                        <div style={{ padding: '12px', textAlign: 'center', color: 'var(--text-muted)' }}>
                            No stocks found
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}
