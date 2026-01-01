/**
 * API client for backend communication.
 */

import axios from 'axios';
import Cookies from 'js-cookie';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000';

// Create axios instance
const api = axios.create({
    baseURL: `${API_URL}/api`,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Add auth token to requests
api.interceptors.request.use((config) => {
    const token = Cookies.get('token');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

// Handle auth errors
api.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response?.status === 401) {
            Cookies.remove('token');
            if (typeof window !== 'undefined') {
                window.location.href = '/login';
            }
        }
        return Promise.reject(error);
    }
);

// Types
export interface Stock {
    ticker: string;
    date: string;
    open: number;
    high: number;
    low: number;
    close: number;
    volume: number;
    ma_50?: number;
    rsi_14?: number;
    volatility?: number;
}

export interface Prediction {
    ticker: string;
    model_type: string;
    horizon: string;
    predicted_price: number;
    predicted_change_pct: number;
    confidence: number;
    prediction_date: string;
    target_date: string;
}

export interface PortfolioHolding {
    id: string;
    ticker: string;
    quantity: number;
    buy_price: number;
    buy_date: string;
    current_price?: number;
    pnl?: number;
    pnl_pct?: number;
}

export interface User {
    id: string;
    email: string;
    username: string;
}

// Auth API
export const authAPI = {
    signup: async (email: string, username: string, password: string) => {
        const response = await api.post('/auth/signup', { email, username, password });
        return response.data;
    },

    login: async (email: string, password: string) => {
        const response = await api.post('/auth/login', { email, password });
        if (response.data.token) {
            Cookies.set('token', response.data.token, { expires: 1 });
        }
        return response.data;
    },

    logout: () => {
        Cookies.remove('token');
    },

    me: async (): Promise<User> => {
        const response = await api.get('/auth/me');
        return response.data;
    },
};

// Stocks API
export const stocksAPI = {
    getAll: async (page = 1, limit = 50) => {
        const response = await api.get(`/stocks?page=${page}&limit=${limit}`);
        return response.data;
    },

    getOne: async (ticker: string): Promise<Stock> => {
        const response = await api.get(`/stocks/${ticker}`);
        return response.data;
    },

    getHistory: async (ticker: string, days = 365) => {
        const response = await api.get(`/stocks/${ticker}/history?days=${days}`);
        return response.data;
    },

    getMetrics: async (ticker: string, days = 30) => {
        const response = await api.get(`/stocks/${ticker}/metrics?days=${days}`);
        return response.data;
    },

    search: async (query: string) => {
        const response = await api.get(`/stocks/search?q=${query}`);
        return response.data;
    },
};

// Predictions API
export const predictionsAPI = {
    get: async (ticker: string): Promise<{ predictions: Record<string, Prediction[]> }> => {
        const response = await api.get(`/predictions/${ticker}/latest`);
        return response.data;
    },

    getSentiment: async (ticker: string) => {
        const response = await api.get(`/predictions/sentiment/${ticker}`);
        return response.data;
    },
};

// Portfolio API
export const portfolioAPI = {
    get: async () => {
        const response = await api.get('/portfolio');
        return response.data;
    },

    add: async (ticker: string, quantity: number, buyPrice: number, buyDate?: string) => {
        const response = await api.post('/portfolio', {
            ticker,
            quantity,
            buy_price: buyPrice,
            buy_date: buyDate,
        });
        return response.data;
    },

    remove: async (holdingId: string) => {
        await api.delete(`/portfolio/${holdingId}`);
    },

    getRisk: async () => {
        const response = await api.get('/portfolio/risk');
        return response.data;
    },
};

// Wishlist API
export const wishlistAPI = {
    get: async () => {
        const response = await api.get('/wishlist');
        return response.data;
    },

    add: async (ticker: string) => {
        const response = await api.post('/wishlist', { ticker });
        return response.data;
    },

    remove: async (itemId: string) => {
        await api.delete(`/wishlist/${itemId}`);
    },
};

export { API_URL };
export default api;
