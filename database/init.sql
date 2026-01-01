-- Stock Market Dashboard Database Schema
-- PostgreSQL initialization script

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =====================================================
-- STOCKS TABLE
-- Daily OHLCV data with composite primary key
-- =====================================================
CREATE TABLE IF NOT EXISTS stocks (
    ticker VARCHAR(20) NOT NULL,
    date DATE NOT NULL,
    open DECIMAL(12, 4) NOT NULL,
    high DECIMAL(12, 4) NOT NULL,
    low DECIMAL(12, 4) NOT NULL,
    close DECIMAL(12, 4) NOT NULL,
    volume BIGINT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (ticker, date)
);

-- Index for faster ticker lookups
CREATE INDEX IF NOT EXISTS idx_stocks_ticker ON stocks(ticker);
CREATE INDEX IF NOT EXISTS idx_stocks_date ON stocks(date DESC);

-- =====================================================
-- STOCK METRICS TABLE
-- Technical indicators: MA, RSI, MACD, Bollinger, etc.
-- =====================================================
CREATE TABLE IF NOT EXISTS stock_metrics (
    ticker VARCHAR(20) NOT NULL,
    date DATE NOT NULL,
    ma_10 DECIMAL(12, 4),
    ma_20 DECIMAL(12, 4),
    ma_50 DECIMAL(12, 4),
    ma_200 DECIMAL(12, 4),
    rsi_14 DECIMAL(8, 4),
    macd DECIMAL(12, 4),
    macd_signal DECIMAL(12, 4),
    macd_histogram DECIMAL(12, 4),
    bollinger_upper DECIMAL(12, 4),
    bollinger_middle DECIMAL(12, 4),
    bollinger_lower DECIMAL(12, 4),
    volatility DECIMAL(8, 4),
    volume_ma_20 DECIMAL(18, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (ticker, date),
    FOREIGN KEY (ticker, date) REFERENCES stocks(ticker, date) ON DELETE CASCADE
);

-- =====================================================
-- PREDICTION TEMPLATES TABLE
-- Configurable model parameters for reuse
-- =====================================================
CREATE TABLE IF NOT EXISTS prediction_templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL UNIQUE,
    model_type VARCHAR(50) NOT NULL,
    parameters JSONB NOT NULL DEFAULT '{}',
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert default templates
INSERT INTO prediction_templates (name, model_type, parameters, description) VALUES
    ('ARIMA Default', 'arima', '{"order": [5, 1, 0]}', 'Default ARIMA(5,1,0) model'),
    ('Linear Regression', 'linear_regression', '{"normalize": true}', 'Simple linear regression'),
    ('Random Forest', 'random_forest', '{"n_estimators": 100, "max_depth": 10}', 'Random Forest regressor'),
    ('XGBoost', 'xgboost', '{"n_estimators": 100, "learning_rate": 0.1, "max_depth": 6}', 'XGBoost regressor'),
    ('LSTM', 'lstm', '{"units": 50, "epochs": 50, "batch_size": 32}', 'LSTM neural network'),
    ('Prophet', 'prophet', '{"yearly_seasonality": true, "weekly_seasonality": true}', 'Facebook Prophet'),
    ('Exponential Smoothing', 'exp_smoothing', '{"trend": "add", "seasonal": "add", "seasonal_periods": 5}', 'Holt-Winters')
ON CONFLICT (name) DO NOTHING;

-- =====================================================
-- PREDICTIONS TABLE
-- ML model predictions with horizons
-- =====================================================
CREATE TABLE IF NOT EXISTS predictions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ticker VARCHAR(20) NOT NULL,
    prediction_date DATE NOT NULL,
    target_date DATE NOT NULL,
    model_type VARCHAR(50) NOT NULL,
    horizon VARCHAR(20) NOT NULL,  -- '1h', '4h', '1d', '3d', '1w', '1m'
    predicted_price DECIMAL(12, 4) NOT NULL,
    predicted_change_pct DECIMAL(8, 4),
    confidence DECIMAL(5, 4),
    template_id UUID REFERENCES prediction_templates(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (ticker, prediction_date, model_type, horizon)
);

CREATE INDEX IF NOT EXISTS idx_predictions_ticker ON predictions(ticker);
CREATE INDEX IF NOT EXISTS idx_predictions_date ON predictions(prediction_date DESC);
CREATE INDEX IF NOT EXISTS idx_predictions_model ON predictions(model_type);

-- =====================================================
-- SENTIMENT SCORES TABLE
-- Hugging Face sentiment analysis results
-- =====================================================
CREATE TABLE IF NOT EXISTS sentiment_scores (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ticker VARCHAR(20) NOT NULL,
    date DATE NOT NULL,
    positive_score DECIMAL(5, 4) NOT NULL,
    negative_score DECIMAL(5, 4) NOT NULL,
    neutral_score DECIMAL(5, 4) NOT NULL,
    overall_sentiment VARCHAR(20) NOT NULL,
    source TEXT,
    headline TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (ticker, date, headline)
);

CREATE INDEX IF NOT EXISTS idx_sentiment_ticker ON sentiment_scores(ticker);
CREATE INDEX IF NOT EXISTS idx_sentiment_date ON sentiment_scores(date DESC);

-- =====================================================
-- USERS TABLE
-- User authentication with hashed passwords
-- =====================================================
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) NOT NULL UNIQUE,
    username VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- =====================================================
-- PORTFOLIOS TABLE
-- User stock holdings with buy price
-- =====================================================
CREATE TABLE IF NOT EXISTS portfolios (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    ticker VARCHAR(20) NOT NULL,
    quantity DECIMAL(12, 4) NOT NULL,
    buy_price DECIMAL(12, 4) NOT NULL,
    buy_date DATE NOT NULL,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (user_id, ticker, buy_date)
);

CREATE INDEX IF NOT EXISTS idx_portfolios_user ON portfolios(user_id);
CREATE INDEX IF NOT EXISTS idx_portfolios_ticker ON portfolios(ticker);

-- =====================================================
-- WISHLISTS TABLE
-- User watchlists
-- =====================================================
CREATE TABLE IF NOT EXISTS wishlists (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    ticker VARCHAR(20) NOT NULL,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,
    UNIQUE (user_id, ticker)
);

CREATE INDEX IF NOT EXISTS idx_wishlists_user ON wishlists(user_id);

-- =====================================================
-- NIFTY INDEX CONSTITUENTS TABLE
-- Track Nifty 50/100 membership
-- =====================================================
CREATE TABLE IF NOT EXISTS nifty_constituents (
    ticker VARCHAR(20) PRIMARY KEY,
    company_name VARCHAR(255) NOT NULL,
    sector VARCHAR(100),
    index_name VARCHAR(20) NOT NULL,  -- 'NIFTY50' or 'NIFTY100'
    weight DECIMAL(6, 4),
    is_active BOOLEAN DEFAULT TRUE,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- Update timestamp trigger function
-- =====================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply trigger to tables with updated_at
CREATE TRIGGER update_stocks_updated_at BEFORE UPDATE ON stocks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_portfolios_updated_at BEFORE UPDATE ON portfolios
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_templates_updated_at BEFORE UPDATE ON prediction_templates
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
