import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import Navbar from '@/components/Navbar';
import { AuthProvider } from '@/utils/AuthContext';
import { ThemeProvider } from '@/utils/ThemeContext';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
    title: 'Stock Market Dashboard | Indian Stocks Analysis',
    description: 'Comprehensive stock market analysis dashboard for Indian stocks with ML predictions',
    keywords: ['stocks', 'nifty', 'indian market', 'trading', 'analysis'],
};

export default function RootLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <html lang="en" suppressHydrationWarning>
            <body className={inter.className}>
                <ThemeProvider>
                    <AuthProvider>
                        <div className="min-h-screen" style={{ background: 'var(--bg-dark)' }}>
                            <Navbar />
                            <main className="container mx-auto px-4 py-6">
                                {children}
                            </main>
                        </div>
                    </AuthProvider>
                </ThemeProvider>
            </body>
        </html>
    );
}
