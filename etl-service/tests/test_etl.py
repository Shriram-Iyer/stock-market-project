"""
Unit tests for ETL service.
"""

from datetime import datetime, date
from unittest.mock import patch, MagicMock

import numpy as np
import pandas as pd
import pytest


class TestFetcher:
    """Tests for fetcher module."""
    
    def test_get_nifty_tickers_nifty50(self):
        """Test getting Nifty 50 tickers."""
        from etl.fetcher import get_nifty_tickers
        
        tickers = get_nifty_tickers("NIFTY50")
        assert len(tickers) == 50
        assert "RELIANCE.NS" in tickers
        assert "TCS.NS" in tickers
    
    def test_get_nifty_tickers_nifty100(self):
        """Test getting Nifty 100 tickers."""
        from etl.fetcher import get_nifty_tickers
        
        tickers = get_nifty_tickers("NIFTY100")
        assert len(tickers) == 100
    
    def test_get_nifty_tickers_invalid(self):
        """Test invalid index raises error."""
        from etl.fetcher import get_nifty_tickers
        
        with pytest.raises(ValueError):
            get_nifty_tickers("INVALID")


class TestAnalysis:
    """Tests for analysis module."""
    
    @pytest.fixture
    def sample_df(self):
        """Create sample stock DataFrame."""
        dates = pd.date_range(start="2024-01-01", periods=100)
        return pd.DataFrame({
            "date": dates,
            "ticker": "TEST.NS",
            "open": np.random.uniform(100, 110, 100),
            "high": np.random.uniform(110, 120, 100),
            "low": np.random.uniform(90, 100, 100),
            "close": np.random.uniform(100, 110, 100),
            "volume": np.random.randint(1000000, 5000000, 100),
        })
    
    def test_calculate_moving_averages(self, sample_df):
        """Test MA calculation."""
        from etl.analysis import calculate_moving_averages
        
        result = calculate_moving_averages(sample_df, periods=[10, 20])
        
        assert "ma_10" in result.columns
        assert "ma_20" in result.columns
        assert len(result) == len(sample_df)
    
    def test_calculate_rsi(self, sample_df):
        """Test RSI calculation."""
        from etl.analysis import calculate_rsi
        
        result = calculate_rsi(sample_df)
        
        assert "rsi_14" in result.columns
        # RSI should be between 0 and 100
        assert result["rsi_14"].dropna().between(0, 100).all()
    
    def test_calculate_macd(self, sample_df):
        """Test MACD calculation."""
        from etl.analysis import calculate_macd
        
        result = calculate_macd(sample_df)
        
        assert "macd" in result.columns
        assert "macd_signal" in result.columns
        assert "macd_histogram" in result.columns
    
    def test_calculate_bollinger_bands(self, sample_df):
        """Test Bollinger Bands calculation."""
        from etl.analysis import calculate_bollinger_bands
        
        result = calculate_bollinger_bands(sample_df)
        
        assert "bollinger_upper" in result.columns
        assert "bollinger_middle" in result.columns
        assert "bollinger_lower" in result.columns
    
    def test_calculate_all_metrics(self, sample_df):
        """Test all metrics calculation."""
        from etl.analysis import calculate_all_metrics
        
        result = calculate_all_metrics(sample_df)
        
        expected_cols = [
            "ma_10", "ma_20", "ma_50", "ma_200",
            "rsi_14", "macd", "volatility",
        ]
        for col in expected_cols:
            assert col in result.columns


class TestMLModels:
    """Tests for ML models module."""
    
    @pytest.fixture
    def sample_data(self):
        """Create sample data for ML models."""
        dates = pd.date_range(start="2024-01-01", periods=200)
        close = 100 + np.cumsum(np.random.randn(200) * 2)
        
        return pd.DataFrame({
            "date": dates,
            "ticker": "TEST.NS",
            "open": close * 0.99,
            "high": close * 1.02,
            "low": close * 0.98,
            "close": close,
            "volume": np.random.randint(1000000, 5000000, 200),
        })
    
    def test_train_linear_regression(self, sample_data):
        """Test Linear Regression training."""
        from etl.analysis import calculate_all_metrics
        from etl.ml_models import train_linear_regression
        
        data = calculate_all_metrics(sample_data)
        result = train_linear_regression(data)
        
        assert "predicted_price" in result
        assert "confidence" in result
        assert result["model_type"] == "linear_regression"
    
    def test_train_arima(self, sample_data):
        """Test ARIMA training."""
        from etl.ml_models import train_arima
        
        result = train_arima(sample_data)
        
        assert "predicted_price" in result
        assert result["model_type"] == "arima"


class TestExceptions:
    """Tests for exceptions module."""
    
    def test_data_fetch_error(self):
        """Test DataFetchError creation."""
        from etl.exceptions import DataFetchError
        
        error = DataFetchError("Test error", ticker="TEST.NS")
        
        assert error.ticker == "TEST.NS"
        assert error.source == "yfinance"
        assert "TEST.NS" in error.details["ticker"]
    
    def test_database_error(self):
        """Test DatabaseError creation."""
        from etl.exceptions import DatabaseError
        
        error = DatabaseError("Test error", operation="insert", table="stocks")
        
        assert error.operation == "insert"
        assert error.table == "stocks"


class TestConfig:
    """Tests for config module."""
    
    @patch.dict("os.environ", {
        "POSTGRES_HOST": "localhost",
        "POSTGRES_PORT": "5432",
        "POSTGRES_USER": "test",
        "POSTGRES_PASSWORD": "test",
        "POSTGRES_DB": "testdb",
    })
    def test_load_config(self):
        """Test configuration loading."""
        from etl.config import load_config
        
        config = load_config()
        
        assert config.database.host == "localhost"
        assert config.database.port == 5432
        assert config.database.user == "test"
