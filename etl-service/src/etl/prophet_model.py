"""
Prophet model for stock price forecasting.

Uses Facebook Prophet for time series with trend and seasonality.
"""

from datetime import datetime, timedelta
from typing import Any

import pandas as pd
import structlog

try:
    from prophet import Prophet
    PROPHET_AVAILABLE = True
except ImportError:
    PROPHET_AVAILABLE = False

from .exceptions import ModelError

logger = structlog.get_logger(__name__)


def train_prophet(
    df: pd.DataFrame,
    horizon: str = "1d",
    yearly_seasonality: bool = True,
    weekly_seasonality: bool = True,
    daily_seasonality: bool = False,
    **kwargs: Any,
) -> dict[str, Any]:
    """
    Train Prophet model and make prediction.
    
    Args:
        df: Stock DataFrame with 'date' and 'close' columns.
        horizon: Prediction horizon ('1d', '3d', '1w', '1m').
        yearly_seasonality: Include yearly seasonality.
        weekly_seasonality: Include weekly seasonality.
        daily_seasonality: Include daily seasonality.
        **kwargs: Additional Prophet parameters.
        
    Returns:
        Dictionary with prediction results.
    """
    if not PROPHET_AVAILABLE:
        raise ModelError("Prophet not installed", model_type="prophet")
    
    try:
        # Prepare data for Prophet (needs 'ds' and 'y' columns)
        prophet_df = df[["date", "close"]].copy()
        prophet_df.columns = ["ds", "y"]
        prophet_df["ds"] = pd.to_datetime(prophet_df["ds"])
        
        if len(prophet_df) < 30:
            raise ModelError("Insufficient data for Prophet", model_type="prophet")
        
        # Suppress Prophet logging
        import logging
        logging.getLogger('cmdstanpy').setLevel(logging.ERROR)
        logging.getLogger('prophet').setLevel(logging.ERROR)
        
        # Create and fit model
        model = Prophet(
            yearly_seasonality=yearly_seasonality,
            weekly_seasonality=weekly_seasonality,
            daily_seasonality=daily_seasonality,
            changepoint_prior_scale=0.05,
        )
        model.fit(prophet_df)
        
        # Determine forecast periods
        horizon_days = {
            "1h": 1,
            "4h": 1,
            "1d": 1,
            "3d": 3,
            "1w": 7,
            "1m": 30,
        }
        periods = horizon_days.get(horizon, 1)
        
        # Make future dataframe and forecast
        future = model.make_future_dataframe(periods=periods)
        forecast = model.predict(future)
        
        # Get prediction
        predicted_price = float(forecast["yhat"].iloc[-1])
        
        # Get confidence interval
        lower_bound = float(forecast["yhat_lower"].iloc[-1])
        upper_bound = float(forecast["yhat_upper"].iloc[-1])
        
        current_price = float(prophet_df["y"].iloc[-1])
        predicted_change = ((predicted_price - current_price) / current_price) * 100
        
        # Confidence based on interval width relative to price
        interval_width = upper_bound - lower_bound
        confidence = max(0, min(1, 1 - (interval_width / current_price)))
        
        return {
            "model_type": "prophet",
            "horizon": horizon,
            "predicted_price": round(predicted_price, 4),
            "predicted_change_pct": round(predicted_change, 4),
            "confidence": round(confidence, 4),
            "current_price": current_price,
            "lower_bound": round(lower_bound, 4),
            "upper_bound": round(upper_bound, 4),
        }
        
    except Exception as e:
        logger.error("prophet_training_failed", error=str(e))
        raise ModelError(f"Prophet training failed: {str(e)}", model_type="prophet") from e


def run_prophet_predictions(
    df: pd.DataFrame,
    ticker: str,
    horizons: list[str] = ["1d", "1w", "1m"],
) -> list[dict[str, Any]]:
    """
    Run Prophet predictions for multiple horizons.
    
    Args:
        df: Stock DataFrame.
        ticker: Stock ticker.
        horizons: List of prediction horizons.
        
    Returns:
        List of prediction results.
    """
    results: list[dict[str, Any]] = []
    
    for horizon in horizons:
        try:
            result = train_prophet(df, horizon=horizon)
            result["ticker"] = ticker
            result["prediction_date"] = datetime.now().date()
            
            horizon_days = {"1h": 0, "4h": 0, "1d": 1, "3d": 3, "1w": 7, "1m": 30}
            days = horizon_days.get(horizon, 1)
            result["target_date"] = (datetime.now() + timedelta(days=days)).date()
            
            results.append(result)
            
            logger.info(
                "prophet_prediction_complete",
                ticker=ticker,
                horizon=horizon,
                predicted_price=result["predicted_price"],
            )
            
        except ModelError as e:
            logger.warning(
                "prophet_prediction_failed",
                ticker=ticker,
                horizon=horizon,
                error=str(e),
            )
            continue
    
    return results
