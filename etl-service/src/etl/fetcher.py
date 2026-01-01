"""
Stock data fetcher module.

Fetches Nifty 50/100 stock data from yfinance with retry logic.
"""

from datetime import datetime, timedelta
from typing import Any

import pandas as pd
import structlog
import yfinance as yf
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from .exceptions import DataFetchError

logger = structlog.get_logger(__name__)

# Nifty 50 tickers with .NS suffix for NSE
NIFTY_50_TICKERS: list[str] = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS",
    "HINDUNILVR.NS", "SBIN.NS", "BHARTIARTL.NS", "KOTAKBANK.NS", "ITC.NS",
    "LT.NS", "AXISBANK.NS", "ASIANPAINT.NS", "MARUTI.NS", "HCLTECH.NS",
    "SUNPHARMA.NS", "BAJFINANCE.NS", "TITAN.NS", "ULTRACEMCO.NS", "NTPC.NS",
    "NESTLEIND.NS", "WIPRO.NS", "M&M.NS", "POWERGRID.NS", "TATAMOTORS.NS",
    "JSWSTEEL.NS", "BAJAJFINSV.NS", "ONGC.NS", "TATASTEEL.NS", "ADANIENT.NS",
    "ADANIPORTS.NS", "COALINDIA.NS", "TECHM.NS", "HINDALCO.NS", "GRASIM.NS",
    "DIVISLAB.NS", "BRITANNIA.NS", "CIPLA.NS", "EICHERMOT.NS", "DRREDDY.NS",
    "BPCL.NS", "APOLLOHOSP.NS", "TATACONSUM.NS", "INDUSINDBK.NS", "HEROMOTOCO.NS",
    "SBILIFE.NS", "HDFCLIFE.NS", "BAJAJ-AUTO.NS", "UPL.NS", "LTIM.NS",
]

# Additional Nifty 100 tickers (beyond Nifty 50)
NIFTY_100_ADDITIONAL_TICKERS: list[str] = [
    "ADANIGREEN.NS", "AMBUJACEM.NS", "BANKBARODA.NS", "BERGEPAINT.NS",
    "BOSCHLTD.NS", "CANBK.NS", "CHOLAFIN.NS", "DLF.NS", "DABUR.NS",
    "GODREJCP.NS", "HAVELLS.NS", "ICICIPRULI.NS", "INDIGO.NS", "IOC.NS",
    "IRCTC.NS", "JINDALSTEL.NS", "JSWENERGY.NS", "LICI.NS", "LUPIN.NS",
    "MARICO.NS", "MCDOWELL-N.NS", "MOTHERSON.NS", "NAUKRI.NS", "NHPC.NS",
    "OFSS.NS", "PAGEIND.NS", "PFC.NS", "PIDILITIND.NS", "PIIND.NS",
    "PNB.NS", "RECLTD.NS", "SAIL.NS", "SHREECEM.NS", "SIEMENS.NS",
    "SRF.NS", "TATAPOWER.NS", "TORNTPHARM.NS", "TRENT.NS", "UNIONBANK.NS",
    "VEDL.NS", "ZOMATO.NS", "ZYDUSLIFE.NS", "MUTHOOTFIN.NS", "POLICYBZR.NS",
    "PERSISTENT.NS", "COFORGE.NS", "MAXHEALTH.NS", "ABB.NS", "GAIL.NS",
]


def get_nifty_tickers(index: str = "NIFTY50") -> list[str]:
    """
    Get list of tickers for specified Nifty index.
    
    Args:
        index: Either 'NIFTY50' or 'NIFTY100'.
        
    Returns:
        List of ticker symbols with .NS suffix.
        
    Raises:
        ValueError: If invalid index specified.
    """
    if index == "NIFTY50":
        return NIFTY_50_TICKERS.copy()
    elif index == "NIFTY100":
        return NIFTY_50_TICKERS + NIFTY_100_ADDITIONAL_TICKERS
    else:
        raise ValueError(f"Invalid index: {index}. Use 'NIFTY50' or 'NIFTY100'.")


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((ConnectionError, TimeoutError)),
    reraise=True,
)
def fetch_stock_data(
    ticker: str,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    period: str = "1y",
) -> pd.DataFrame:
    """
    Fetch OHLCV data for a single ticker.
    
    Args:
        ticker: Stock ticker symbol (e.g., 'RELIANCE.NS').
        start_date: Start date for data fetch.
        end_date: End date for data fetch.
        period: Period string if dates not specified (default: '1y').
        
    Returns:
        DataFrame with columns: Open, High, Low, Close, Volume, Ticker.
        
    Raises:
        DataFetchError: If data fetch fails or returns empty.
    """
    logger.info("fetching_stock_data", ticker=ticker)
    
    try:
        stock = yf.Ticker(ticker)
        
        if start_date and end_date:
            df = stock.history(start=start_date, end=end_date)
        else:
            df = stock.history(period=period)
        
        if df.empty:
            raise DataFetchError(
                f"No data returned for ticker {ticker}",
                ticker=ticker,
            )
        
        # Clean and format data
        df = df.reset_index()
        df = df.rename(columns={
            "Date": "date",
            "Open": "open",
            "High": "high",
            "Low": "low",
            "Close": "close",
            "Volume": "volume",
        })
        
        # Select required columns and add ticker
        df = df[["date", "open", "high", "low", "close", "volume"]]
        df["ticker"] = ticker
        df["date"] = pd.to_datetime(df["date"]).dt.date
        
        logger.info(
            "stock_data_fetched",
            ticker=ticker,
            rows=len(df),
            date_range=f"{df['date'].min()} to {df['date'].max()}",
        )
        
        return df
        
    except Exception as e:
        logger.error("fetch_failed", ticker=ticker, error=str(e))
        raise DataFetchError(
            f"Failed to fetch data for {ticker}: {str(e)}",
            ticker=ticker,
        ) from e


def fetch_multiple_stocks(
    tickers: list[str],
    start_date: datetime | None = None,
    end_date: datetime | None = None,
) -> pd.DataFrame:
    """
    Fetch data for multiple tickers and combine.
    
    Args:
        tickers: List of ticker symbols.
        start_date: Start date for data fetch.
        end_date: End date for data fetch (default: today).
        
    Returns:
        Combined DataFrame with all tickers' data.
    """
    if end_date is None:
        end_date = datetime.now()
    if start_date is None:
        start_date = end_date - timedelta(days=365)
    
    all_data: list[pd.DataFrame] = []
    failed_tickers: list[str] = []
    
    for ticker in tickers:
        try:
            df = fetch_stock_data(ticker, start_date, end_date)
            all_data.append(df)
        except DataFetchError as e:
            logger.warning("ticker_fetch_failed", ticker=ticker, error=str(e))
            failed_tickers.append(ticker)
            continue
    
    if failed_tickers:
        logger.warning(
            "some_tickers_failed",
            failed_count=len(failed_tickers),
            failed_tickers=failed_tickers[:10],  # Log first 10
        )
    
    if not all_data:
        raise DataFetchError("No data fetched for any ticker")
    
    combined = pd.concat(all_data, ignore_index=True)
    logger.info(
        "multiple_stocks_fetched",
        total_tickers=len(tickers),
        successful=len(all_data),
        failed=len(failed_tickers),
        total_rows=len(combined),
    )
    
    return combined


def get_stock_info(ticker: str) -> dict[str, Any]:
    """
    Get stock metadata/info.
    
    Args:
        ticker: Stock ticker symbol.
        
    Returns:
        Dictionary with stock info (name, sector, etc.).
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        return {
            "ticker": ticker,
            "name": info.get("longName", info.get("shortName", ticker)),
            "sector": info.get("sector", "Unknown"),
            "industry": info.get("industry", "Unknown"),
            "market_cap": info.get("marketCap", 0),
            "currency": info.get("currency", "INR"),
        }
    except Exception as e:
        logger.warning("info_fetch_failed", ticker=ticker, error=str(e))
        return {
            "ticker": ticker,
            "name": ticker.replace(".NS", ""),
            "sector": "Unknown",
            "industry": "Unknown",
            "market_cap": 0,
            "currency": "INR",
        }
