"""
Database loader module.

Handles data persistence with retry logic and structured logging.
"""

from datetime import date
from typing import Any

import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
import structlog
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from .config import get_config
from .exceptions import DatabaseError

logger = structlog.get_logger(__name__)


def get_connection() -> psycopg2.extensions.connection:
    """
    Create database connection.
    
    Returns:
        PostgreSQL connection object.
        
    Raises:
        DatabaseError: If connection fails.
    """
    config = get_config()
    
    try:
        conn = psycopg2.connect(
            host=config.database.host,
            port=config.database.port,
            user=config.database.user,
            password=config.database.password,
            database=config.database.database,
        )
        return conn
    except Exception as e:
        logger.error("database_connection_failed", error=str(e))
        raise DatabaseError(f"Failed to connect to database: {str(e)}") from e


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(psycopg2.OperationalError),
    reraise=True,
)
def load_stock_data(df: pd.DataFrame) -> int:
    """
    Load stock OHLCV data to database.
    
    Uses upsert (ON CONFLICT UPDATE) for idempotency.
    
    Args:
        df: DataFrame with columns: ticker, date, open, high, low, close, volume.
        
    Returns:
        Number of rows inserted/updated.
    """
    if df.empty:
        logger.warning("empty_dataframe_skipped")
        return 0
    
    required_cols = ["ticker", "date", "open", "high", "low", "close", "volume"]
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise DatabaseError(f"Missing columns: {missing}", operation="load_stock_data")
    
    conn = get_connection()
    
    try:
        cursor = conn.cursor()
        
        # Prepare data as list of tuples
        data = df[required_cols].values.tolist()
        
        # Upsert query
        query = """
            INSERT INTO stocks (ticker, date, open, high, low, close, volume)
            VALUES %s
            ON CONFLICT (ticker, date) 
            DO UPDATE SET
                open = EXCLUDED.open,
                high = EXCLUDED.high,
                low = EXCLUDED.low,
                close = EXCLUDED.close,
                volume = EXCLUDED.volume,
                updated_at = CURRENT_TIMESTAMP
        """
        
        execute_values(cursor, query, data)
        rows_affected = cursor.rowcount
        
        conn.commit()
        
        logger.info(
            "stock_data_loaded",
            rows=rows_affected,
            tickers=df["ticker"].nunique(),
        )
        
        return rows_affected
        
    except Exception as e:
        conn.rollback()
        logger.error("stock_data_load_failed", error=str(e))
        raise DatabaseError(f"Failed to load stock data: {str(e)}", table="stocks") from e
    finally:
        conn.close()


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(psycopg2.OperationalError),
    reraise=True,
)
def load_metrics(df: pd.DataFrame) -> int:
    """
    Load stock metrics to database.
    
    Args:
        df: DataFrame with indicator columns.
        
    Returns:
        Number of rows inserted/updated.
    """
    if df.empty:
        return 0
    
    conn = get_connection()
    
    try:
        cursor = conn.cursor()
        
        # Select metric columns
        metric_cols = [
            "ticker", "date", "ma_10", "ma_20", "ma_50", "ma_200",
            "rsi_14", "macd", "macd_signal", "macd_histogram",
            "bollinger_upper", "bollinger_middle", "bollinger_lower",
            "volatility", "volume_ma_20"
        ]
        
        # Filter to existing columns
        available_cols = [col for col in metric_cols if col in df.columns]
        data_df = df[available_cols].copy()
        
        # Replace NaN with None for PostgreSQL
        data_df = data_df.where(pd.notnull(data_df), None)
        data = data_df.values.tolist()
        
        # Build dynamic query
        col_names = ", ".join(available_cols)
        col_updates = ", ".join(
            f"{col} = EXCLUDED.{col}" 
            for col in available_cols 
            if col not in ["ticker", "date"]
        )
        
        query = f"""
            INSERT INTO stock_metrics ({col_names})
            VALUES %s
            ON CONFLICT (ticker, date) 
            DO UPDATE SET {col_updates}
        """
        
        execute_values(cursor, query, data)
        rows_affected = cursor.rowcount
        
        conn.commit()
        
        logger.info("metrics_loaded", rows=rows_affected)
        
        return rows_affected
        
    except Exception as e:
        conn.rollback()
        logger.error("metrics_load_failed", error=str(e))
        raise DatabaseError(f"Failed to load metrics: {str(e)}", table="stock_metrics") from e
    finally:
        conn.close()


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(psycopg2.OperationalError),
    reraise=True,
)
def load_predictions(predictions: list[dict[str, Any]]) -> int:
    """
    Load ML predictions to database.
    
    Args:
        predictions: List of prediction dictionaries.
        
    Returns:
        Number of rows inserted/updated.
    """
    if not predictions:
        return 0
    
    conn = get_connection()
    
    try:
        cursor = conn.cursor()
        
        data = [
            (
                p["ticker"],
                p["prediction_date"],
                p["target_date"],
                p["model_type"],
                p["horizon"],
                p["predicted_price"],
                p.get("predicted_change_pct"),
                p.get("confidence"),
            )
            for p in predictions
        ]
        
        query = """
            INSERT INTO predictions 
            (ticker, prediction_date, target_date, model_type, horizon, 
             predicted_price, predicted_change_pct, confidence)
            VALUES %s
            ON CONFLICT (ticker, prediction_date, model_type, horizon)
            DO UPDATE SET
                target_date = EXCLUDED.target_date,
                predicted_price = EXCLUDED.predicted_price,
                predicted_change_pct = EXCLUDED.predicted_change_pct,
                confidence = EXCLUDED.confidence,
                created_at = CURRENT_TIMESTAMP
        """
        
        execute_values(cursor, query, data)
        rows_affected = cursor.rowcount
        
        conn.commit()
        
        logger.info("predictions_loaded", rows=rows_affected)
        
        return rows_affected
        
    except Exception as e:
        conn.rollback()
        logger.error("predictions_load_failed", error=str(e))
        raise DatabaseError(f"Failed to load predictions: {str(e)}", table="predictions") from e
    finally:
        conn.close()


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(psycopg2.OperationalError),
    reraise=True,
)
def load_sentiment(sentiments: list[dict[str, Any]]) -> int:
    """
    Load sentiment scores to database.
    
    Args:
        sentiments: List of sentiment dictionaries.
        
    Returns:
        Number of rows inserted/updated.
    """
    if not sentiments:
        return 0
    
    conn = get_connection()
    
    try:
        cursor = conn.cursor()
        
        data = [
            (
                s["ticker"],
                s["date"],
                s["positive_score"],
                s["negative_score"],
                s["neutral_score"],
                s["overall_sentiment"],
                s.get("source", "sample"),
                s.get("text", ""),
            )
            for s in sentiments
        ]
        
        query = """
            INSERT INTO sentiment_scores 
            (ticker, date, positive_score, negative_score, neutral_score,
             overall_sentiment, source, headline)
            VALUES %s
            ON CONFLICT (ticker, date, headline)
            DO UPDATE SET
                positive_score = EXCLUDED.positive_score,
                negative_score = EXCLUDED.negative_score,
                neutral_score = EXCLUDED.neutral_score,
                overall_sentiment = EXCLUDED.overall_sentiment
        """
        
        execute_values(cursor, query, data)
        rows_affected = cursor.rowcount
        
        conn.commit()
        
        logger.info("sentiment_loaded", rows=rows_affected)
        
        return rows_affected
        
    except Exception as e:
        conn.rollback()
        logger.error("sentiment_load_failed", error=str(e))
        raise DatabaseError(f"Failed to load sentiment: {str(e)}", table="sentiment_scores") from e
    finally:
        conn.close()


def get_latest_data(ticker: str, limit: int = 365) -> pd.DataFrame:
    """
    Fetch latest stock data from database.
    
    Args:
        ticker: Stock ticker.
        limit: Maximum rows to fetch.
        
    Returns:
        DataFrame with OHLCV data.
    """
    conn = get_connection()
    
    try:
        query = """
            SELECT ticker, date, open, high, low, close, volume
            FROM stocks
            WHERE ticker = %s
            ORDER BY date DESC
            LIMIT %s
        """
        
        df = pd.read_sql(query, conn, params=(ticker, limit))
        df = df.sort_values("date").reset_index(drop=True)
        
        return df
        
    finally:
        conn.close()


def health_check() -> bool:
    """
    Check database connectivity.
    
    Returns:
        True if database is reachable.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        conn.close()
        return True
    except Exception as e:
        logger.error("health_check_failed", error=str(e))
        return False
