'use client';

import { useEffect, useRef, useCallback } from 'react';
import { io, Socket } from 'socket.io-client';
import { API_URL } from './api';

interface PriceUpdate {
    ticker: string;
    price: number;
    change: number;
    change_pct: number;
    timestamp: number;
}

export function useSocket(
    tickers: string[],
    onPriceUpdate: (data: PriceUpdate) => void
) {
    const socketRef = useRef<Socket | null>(null);

    useEffect(() => {
        // Connect to Socket.IO server
        socketRef.current = io(API_URL, {
            transports: ['websocket', 'polling'],
        });

        socketRef.current.on('connect', () => {
            console.log('Socket connected');
            // Subscribe to tickers
            if (tickers.length > 0) {
                socketRef.current?.emit('subscribe', { tickers });
            }
        });

        socketRef.current.on('price_update', (data: PriceUpdate) => {
            onPriceUpdate(data);
        });

        socketRef.current.on('disconnect', () => {
            console.log('Socket disconnected');
        });

        return () => {
            if (socketRef.current) {
                socketRef.current.emit('unsubscribe', { tickers });
                socketRef.current.disconnect();
            }
        };
    }, [tickers, onPriceUpdate]);

    const subscribe = useCallback((newTickers: string[]) => {
        socketRef.current?.emit('subscribe', { tickers: newTickers });
    }, []);

    const unsubscribe = useCallback((removeTickers: string[]) => {
        socketRef.current?.emit('unsubscribe', { tickers: removeTickers });
    }, []);

    return { subscribe, unsubscribe };
}
