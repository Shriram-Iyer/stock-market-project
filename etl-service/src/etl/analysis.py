"""
Technical analysis module.

Calculates indicators: MA, RSI, MACD, Bollinger Bands, volatility.
Uses vectorized pandas operations for performance.
"""

import numpy as np
import pandas as pd
import structlog

logger = structlog.get_logger(__name__)


def calculate_moving_averages(
    df: pd.DataFrame,
    periods: list[int] = [10, 20, 50, 200],
) -> pd.DataFrame:
    """
    Calculate simple moving averages for specified periods.
    
    Args:
        df: DataFrame with 'close' column.
        periods: List of MA periods to calculate.
        
    Returns:
        DataFrame with MA columns added.
    """
    df = df.copy()
    for period in periods:
        col_name = f"ma_{period}"
        df[col_name] = df["close"].rolling(window=period, min_periods=1).mean()
    
    return df


def calculate_rsi(
    df: pd.DataFrame,
    period: int = 14,
) -> pd.DataFrame:
    """
    Calculate Relative Strength Index (RSI).
    
    RSI = 100 - (100 / (1 + RS))
    RS = Average Gain / Average Loss
    
    Args:
        df: DataFrame with 'close' column.
        period: RSI period (default: 14).
        
    Returns:
        DataFrame with 'rsi_14' column added.
    """
    df = df.copy()
    
    # Calculate price changes
    delta = df["close"].diff()
    
    # Separate gains and losses
    gains = delta.where(delta > 0, 0)
    losses = (-delta).where(delta < 0, 0)
    
    # Calculate average gains and losses using EMA
    avg_gains = gains.ewm(span=period, adjust=False).mean()
    avg_losses = losses.ewm(span=period, adjust=False).mean()
    
    # Calculate RS and RSI
    rs = avg_gains / avg_losses.replace(0, np.inf)
    df[f"rsi_{period}"] = 100 - (100 / (1 + rs))
    
    return df


def calculate_macd(
    df: pd.DataFrame,
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9,
) -> pd.DataFrame:
    """
    Calculate MACD (Moving Average Convergence Divergence).
    
    MACD Line = Fast EMA - Slow EMA
    Signal Line = EMA of MACD Line
    Histogram = MACD Line - Signal Line
    
    Args:
        df: DataFrame with 'close' column.
        fast_period: Fast EMA period.
        slow_period: Slow EMA period.
        signal_period: Signal line EMA period.
        
    Returns:
        DataFrame with MACD columns added.
    """
    df = df.copy()
    
    # Calculate EMAs
    fast_ema = df["close"].ewm(span=fast_period, adjust=False).mean()
    slow_ema = df["close"].ewm(span=slow_period, adjust=False).mean()
    
    # MACD line
    df["macd"] = fast_ema - slow_ema
    
    # Signal line
    df["macd_signal"] = df["macd"].ewm(span=signal_period, adjust=False).mean()
    
    # Histogram
    df["macd_histogram"] = df["macd"] - df["macd_signal"]
    
    return df


def calculate_bollinger_bands(
    df: pd.DataFrame,
    period: int = 20,
    std_dev: float = 2.0,
) -> pd.DataFrame:
    """
    Calculate Bollinger Bands.
    
    Middle Band = SMA
    Upper Band = SMA + (std_dev * standard deviation)
    Lower Band = SMA - (std_dev * standard deviation)
    
    Args:
        df: DataFrame with 'close' column.
        period: SMA period.
        std_dev: Number of standard deviations.
        
    Returns:
        DataFrame with Bollinger Band columns added.
    """
    df = df.copy()
    
    # Middle band (SMA)
    df["bollinger_middle"] = df["close"].rolling(window=period).mean()
    
    # Standard deviation
    rolling_std = df["close"].rolling(window=period).std()
    
    # Upper and lower bands
    df["bollinger_upper"] = df["bollinger_middle"] + (std_dev * rolling_std)
    df["bollinger_lower"] = df["bollinger_middle"] - (std_dev * rolling_std)
    
    return df


def calculate_volatility(
    df: pd.DataFrame,
    period: int = 20,
) -> pd.DataFrame:
    """
    Calculate historical volatility as rolling standard deviation of returns.
    
    Args:
        df: DataFrame with 'close' column.
        period: Rolling window period.
        
    Returns:
        DataFrame with 'volatility' column added.
    """
    df = df.copy()
    
    # Calculate daily returns
    returns = df["close"].pct_change()
    
    # Rolling volatility (annualized)
    df["volatility"] = returns.rolling(window=period).std() * np.sqrt(252)
    
    return df


def calculate_volume_ma(
    df: pd.DataFrame,
    period: int = 20,
) -> pd.DataFrame:
    """
    Calculate volume moving average.
    
    Args:
        df: DataFrame with 'volume' column.
        period: MA period.
        
    Returns:
        DataFrame with volume MA column added.
    """
    df = df.copy()
    df["volume_ma_20"] = df["volume"].rolling(window=period, min_periods=1).mean()
    return df


def calculate_all_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate all technical indicators for a DataFrame.
    
    Applies all indicator calculations in order.
    DataFrame should have: date, open, high, low, close, volume, ticker.
    
    Args:
        df: Stock OHLCV DataFrame.
        
    Returns:
        DataFrame with all indicator columns added.
    """
    logger.info("calculating_metrics", rows=len(df))
    
    # Sort by date
    df = df.sort_values(["ticker", "date"]).reset_index(drop=True)
    
    # Apply calculations per ticker
    result_dfs: list[pd.DataFrame] = []
    
    for ticker in df["ticker"].unique():
        ticker_df = df[df["ticker"] == ticker].copy()
        
        # Apply all calculations
        ticker_df = calculate_moving_averages(ticker_df)
        ticker_df = calculate_rsi(ticker_df)
        ticker_df = calculate_macd(ticker_df)
        ticker_df = calculate_bollinger_bands(ticker_df)
        ticker_df = calculate_volatility(ticker_df)
        ticker_df = calculate_volume_ma(ticker_df)
        
        result_dfs.append(ticker_df)
    
    result = pd.concat(result_dfs, ignore_index=True)
    
    logger.info("metrics_calculated", rows=len(result))
    return result


def calculate_correlation_matrix(
    df: pd.DataFrame,
    tickers: list[str] | None = None,
) -> pd.DataFrame:
    """
    Calculate correlation matrix between stock returns.
    
    Args:
        df: DataFrame with 'close', 'ticker', 'date' columns.
        tickers: Optional list of tickers to include.
        
    Returns:
        Correlation matrix DataFrame.
    """
    if tickers:
        df = df[df["ticker"].isin(tickers)]
    
    # Pivot to get tickers as columns
    pivot_df = df.pivot(index="date", columns="ticker", values="close")
    
    # Calculate returns
    returns = pivot_df.pct_change().dropna()
    
    # Calculate correlation
    correlation = returns.corr()
    
    logger.info(
        "correlation_calculated",
        tickers=len(correlation.columns),
    )
    
    return correlation
