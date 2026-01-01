"""
ETL main orchestration module.

Coordinates data fetching, analysis, prediction, and loading.
Includes scheduling for daily runs.
"""

import time
from datetime import datetime

import schedule
import structlog

from .config import get_config, load_config
from .fetcher import get_nifty_tickers, fetch_multiple_stocks
from .analysis import calculate_all_metrics
from .ml_models import run_all_ml_models
from .lstm_model import run_lstm_predictions, TENSORFLOW_AVAILABLE
from .prophet_model import run_prophet_predictions, PROPHET_AVAILABLE
from .sentiment import get_stock_sentiment, TRANSFORMERS_AVAILABLE
from .loader import (
    load_stock_data,
    load_metrics,
    load_predictions,
    load_sentiment,
    health_check,
)
from .exceptions import ETLException, DataFetchError, DatabaseError

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)


def run_etl_pipeline(index: str = "NIFTY50") -> dict:
    """
    Run complete ETL pipeline for specified index.
    
    Steps:
    1. Fetch stock data from yfinance
    2. Calculate technical indicators
    3. Run ML predictions
    4. Run LSTM predictions (if available)
    5. Run Prophet predictions (if available)
    6. Run sentiment analysis (if available)
    7. Load all data to database
    
    Args:
        index: 'NIFTY50' or 'NIFTY100'.
        
    Returns:
        Dictionary with pipeline statistics.
    """
    logger.info("etl_pipeline_started", index=index, timestamp=datetime.now().isoformat())
    
    stats = {
        "start_time": datetime.now(),
        "stocks_fetched": 0,
        "metrics_calculated": 0,
        "predictions_made": 0,
        "sentiment_analyzed": 0,
        "errors": [],
    }
    
    try:
        # Step 1: Fetch stock data
        logger.info("step_1_fetching_data")
        tickers = get_nifty_tickers(index)
        stock_data = fetch_multiple_stocks(tickers)
        stats["stocks_fetched"] = len(stock_data)
        
        # Load raw stock data
        load_stock_data(stock_data)
        
        # Step 2: Calculate technical indicators
        logger.info("step_2_calculating_metrics")
        metrics_data = calculate_all_metrics(stock_data)
        stats["metrics_calculated"] = len(metrics_data)
        
        # Load metrics
        load_metrics(metrics_data)
        
        # Step 3-5: Run predictions for each ticker
        logger.info("step_3_running_predictions")
        all_predictions: list = []
        all_sentiments: list = []
        horizons = ["1d", "1w", "1m"]
        
        for ticker in tickers[:10]:  # Limit for demo
            try:
                ticker_data = metrics_data[metrics_data["ticker"] == ticker].copy()
                
                if len(ticker_data) < 60:
                    logger.warning("insufficient_data", ticker=ticker)
                    continue
                
                # Traditional ML models
                ml_preds = run_all_ml_models(ticker_data, ticker, horizons)
                all_predictions.extend(ml_preds)
                
                # LSTM predictions
                if TENSORFLOW_AVAILABLE:
                    try:
                        lstm_preds = run_lstm_predictions(ticker_data, ticker, horizons)
                        all_predictions.extend(lstm_preds)
                    except Exception as e:
                        logger.warning("lstm_failed", ticker=ticker, error=str(e))
                
                # Prophet predictions
                if PROPHET_AVAILABLE:
                    try:
                        prophet_preds = run_prophet_predictions(ticker_data, ticker, horizons)
                        all_predictions.extend(prophet_preds)
                    except Exception as e:
                        logger.warning("prophet_failed", ticker=ticker, error=str(e))
                
                # Sentiment analysis
                if TRANSFORMERS_AVAILABLE:
                    try:
                        sentiment = get_stock_sentiment(ticker)
                        all_sentiments.append(sentiment)
                    except Exception as e:
                        logger.warning("sentiment_failed", ticker=ticker, error=str(e))
                
            except Exception as e:
                logger.error("ticker_processing_failed", ticker=ticker, error=str(e))
                stats["errors"].append({"ticker": ticker, "error": str(e)})
                continue
        
        stats["predictions_made"] = len(all_predictions)
        stats["sentiment_analyzed"] = len(all_sentiments)
        
        # Load predictions and sentiment
        if all_predictions:
            load_predictions(all_predictions)
        
        if all_sentiments:
            load_sentiment(all_sentiments)
        
        stats["end_time"] = datetime.now()
        stats["duration_seconds"] = (
            stats["end_time"] - stats["start_time"]
        ).total_seconds()
        stats["success"] = True
        
        logger.info(
            "etl_pipeline_completed",
            duration=stats["duration_seconds"],
            stocks=stats["stocks_fetched"],
            predictions=stats["predictions_made"],
        )
        
        return stats
        
    except (DataFetchError, DatabaseError) as e:
        logger.error("etl_pipeline_failed", error=str(e), details=e.details)
        stats["errors"].append({"type": type(e).__name__, "message": str(e)})
        stats["success"] = False
        return stats
        
    except Exception as e:
        logger.error("etl_pipeline_unexpected_error", error=str(e))
        stats["errors"].append({"type": "unexpected", "message": str(e)})
        stats["success"] = False
        return stats


def run_scheduled():
    """Run ETL pipeline as scheduled job."""
    logger.info("scheduled_run_triggered")
    run_etl_pipeline("NIFTY50")


def start_scheduler():
    """
    Start the ETL scheduler.
    
    Runs ETL pipeline daily at market close (3:30 PM IST).
    """
    logger.info("scheduler_starting")
    
    # Wait for database to be ready
    retries = 0
    while not health_check() and retries < 30:
        logger.info("waiting_for_database", retry=retries)
        time.sleep(2)
        retries += 1
    
    if not health_check():
        logger.error("database_not_available")
        return
    
    # Run immediately on startup
    logger.info("running_initial_etl")
    run_etl_pipeline("NIFTY50")
    
    # Schedule daily runs
    schedule.every().day.at("15:30").do(run_scheduled)  # 3:30 PM IST
    
    logger.info("scheduler_started", next_run=schedule.next_run())
    
    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    import sys
    
    # Load configuration
    try:
        load_config()
    except Exception as e:
        logger.error("config_load_failed", error=str(e))
        sys.exit(1)
    
    # Check command line args
    if len(sys.argv) > 1 and sys.argv[1] == "--once":
        # Run once and exit
        result = run_etl_pipeline("NIFTY50")
        sys.exit(0 if result.get("success") else 1)
    else:
        # Start scheduler
        start_scheduler()
