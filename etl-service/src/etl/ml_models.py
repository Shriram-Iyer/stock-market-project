"""
Traditional ML models for stock prediction.

Includes: ARIMA, Linear Regression, Random Forest, XGBoost, Exponential Smoothing.
"""

from datetime import datetime, timedelta
from typing import Any

import numpy as np
import pandas as pd
import structlog
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.holtwinters import ExponentialSmoothing
import xgboost as xgb

from .exceptions import ModelError

logger = structlog.get_logger(__name__)

# Horizon mapping to days
HORIZON_DAYS: dict[str, int] = {
    "1h": 0,      # Same day (intraday)
    "4h": 0,      # Same day (intraday)
    "1d": 1,
    "3d": 3,
    "1w": 7,
    "1m": 30,
}


def prepare_features(df: pd.DataFrame, target_col: str = "close") -> tuple[np.ndarray, np.ndarray]:
    """
    Prepare features for ML models.
    
    Creates lagged features and technical indicators as features.
    
    Args:
        df: DataFrame with OHLCV and indicator data.
        target_col: Target column for prediction.
        
    Returns:
        Tuple of (features, target) arrays.
    """
    df = df.copy()
    
    # Create lagged features
    for lag in [1, 2, 3, 5, 10]:
        df[f"close_lag_{lag}"] = df["close"].shift(lag)
        df[f"volume_lag_{lag}"] = df["volume"].shift(lag)
    
    # Returns
    df["return_1d"] = df["close"].pct_change(1)
    df["return_5d"] = df["close"].pct_change(5)
    
    # Drop NaN rows
    df = df.dropna()
    
    # Feature columns
    feature_cols = [col for col in df.columns if col not in [
        "date", "ticker", target_col, "open", "high", "low", "created_at", "updated_at"
    ]]
    
    X = df[feature_cols].values
    y = df[target_col].values
    
    return X, y


def train_linear_regression(
    df: pd.DataFrame,
    horizon: str = "1d",
    **kwargs: Any,
) -> dict[str, Any]:
    """
    Train Linear Regression model and make prediction.
    
    Args:
        df: Stock DataFrame with indicators.
        horizon: Prediction horizon.
        **kwargs: Additional model parameters.
        
    Returns:
        Dictionary with prediction results.
    """
    try:
        X, y = prepare_features(df)
        
        if len(X) < 30:
            raise ModelError("Insufficient data for training", model_type="linear_regression")
        
        # Train/test split (use last 20% for validation)
        split_idx = int(len(X) * 0.8)
        X_train, X_test = X[:split_idx], X[split_idx:]
        y_train, y_test = y[:split_idx], y[split_idx:]
        
        # Standardize features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        # Train model
        model = LinearRegression(**kwargs)
        model.fit(X_train_scaled, y_train)
        
        # Predict next value
        last_features = X[-1:].reshape(1, -1)
        last_features_scaled = scaler.transform(last_features)
        predicted_price = float(model.predict(last_features_scaled)[0])
        
        # Calculate metrics
        current_price = float(y[-1])
        predicted_change = ((predicted_price - current_price) / current_price) * 100
        
        # Simple confidence based on R² score
        train_score = model.score(X_train_scaled, y_train)
        
        return {
            "model_type": "linear_regression",
            "horizon": horizon,
            "predicted_price": round(predicted_price, 4),
            "predicted_change_pct": round(predicted_change, 4),
            "confidence": round(max(0, min(1, train_score)), 4),
            "current_price": current_price,
        }
        
    except Exception as e:
        logger.error("linear_regression_failed", error=str(e))
        raise ModelError(f"Linear Regression failed: {str(e)}", model_type="linear_regression") from e


def train_random_forest(
    df: pd.DataFrame,
    horizon: str = "1d",
    n_estimators: int = 100,
    max_depth: int = 10,
    **kwargs: Any,
) -> dict[str, Any]:
    """
    Train Random Forest model and make prediction.
    
    Args:
        df: Stock DataFrame with indicators.
        horizon: Prediction horizon.
        n_estimators: Number of trees.
        max_depth: Maximum tree depth.
        **kwargs: Additional model parameters.
        
    Returns:
        Dictionary with prediction results.
    """
    try:
        X, y = prepare_features(df)
        
        if len(X) < 50:
            raise ModelError("Insufficient data for training", model_type="random_forest")
        
        # Scale features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # Train model
        model = RandomForestRegressor(
            n_estimators=n_estimators,
            max_depth=max_depth,
            random_state=42,
            n_jobs=-1,
            **kwargs,
        )
        model.fit(X_scaled, y)
        
        # Predict
        last_features = scaler.transform(X[-1:].reshape(1, -1))
        predicted_price = float(model.predict(last_features)[0])
        
        current_price = float(y[-1])
        predicted_change = ((predicted_price - current_price) / current_price) * 100
        
        return {
            "model_type": "random_forest",
            "horizon": horizon,
            "predicted_price": round(predicted_price, 4),
            "predicted_change_pct": round(predicted_change, 4),
            "confidence": round(model.score(X_scaled, y), 4),
            "current_price": current_price,
        }
        
    except Exception as e:
        logger.error("random_forest_failed", error=str(e))
        raise ModelError(f"Random Forest failed: {str(e)}", model_type="random_forest") from e


def train_xgboost(
    df: pd.DataFrame,
    horizon: str = "1d",
    n_estimators: int = 100,
    learning_rate: float = 0.1,
    max_depth: int = 6,
    **kwargs: Any,
) -> dict[str, Any]:
    """
    Train XGBoost model and make prediction.
    
    Args:
        df: Stock DataFrame with indicators.
        horizon: Prediction horizon.
        n_estimators: Number of boosting rounds.
        learning_rate: Learning rate.
        max_depth: Maximum tree depth.
        **kwargs: Additional model parameters.
        
    Returns:
        Dictionary with prediction results.
    """
    try:
        X, y = prepare_features(df)
        
        if len(X) < 50:
            raise ModelError("Insufficient data for training", model_type="xgboost")
        
        # Scale features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # Train model
        model = xgb.XGBRegressor(
            n_estimators=n_estimators,
            learning_rate=learning_rate,
            max_depth=max_depth,
            random_state=42,
            verbosity=0,
            **kwargs,
        )
        model.fit(X_scaled, y)
        
        # Predict
        last_features = scaler.transform(X[-1:].reshape(1, -1))
        predicted_price = float(model.predict(last_features)[0])
        
        current_price = float(y[-1])
        predicted_change = ((predicted_price - current_price) / current_price) * 100
        
        return {
            "model_type": "xgboost",
            "horizon": horizon,
            "predicted_price": round(predicted_price, 4),
            "predicted_change_pct": round(predicted_change, 4),
            "confidence": round(model.score(X_scaled, y), 4),
            "current_price": current_price,
        }
        
    except Exception as e:
        logger.error("xgboost_failed", error=str(e))
        raise ModelError(f"XGBoost failed: {str(e)}", model_type="xgboost") from e


def train_arima(
    df: pd.DataFrame,
    horizon: str = "1d",
    order: tuple[int, int, int] = (5, 1, 0),
    **kwargs: Any,
) -> dict[str, Any]:
    """
    Train ARIMA model and make prediction.
    
    Args:
        df: Stock DataFrame.
        horizon: Prediction horizon.
        order: ARIMA order (p, d, q).
        **kwargs: Additional model parameters.
        
    Returns:
        Dictionary with prediction results.
    """
    try:
        # Use close prices
        series = df["close"].values
        
        if len(series) < 30:
            raise ModelError("Insufficient data for ARIMA", model_type="arima")
        
        # Fit ARIMA
        model = ARIMA(series, order=order)
        fitted = model.fit()
        
        # Forecast
        steps = max(1, HORIZON_DAYS.get(horizon, 1))
        forecast = fitted.forecast(steps=steps)
        predicted_price = float(forecast[-1])
        
        current_price = float(series[-1])
        predicted_change = ((predicted_price - current_price) / current_price) * 100
        
        # Use AIC as rough confidence measure (normalized)
        aic = fitted.aic
        confidence = max(0, min(1, 1 / (1 + abs(aic) / 1000)))
        
        return {
            "model_type": "arima",
            "horizon": horizon,
            "predicted_price": round(predicted_price, 4),
            "predicted_change_pct": round(predicted_change, 4),
            "confidence": round(confidence, 4),
            "current_price": current_price,
        }
        
    except Exception as e:
        logger.error("arima_failed", error=str(e))
        raise ModelError(f"ARIMA failed: {str(e)}", model_type="arima") from e


def train_exponential_smoothing(
    df: pd.DataFrame,
    horizon: str = "1d",
    trend: str = "add",
    seasonal: str | None = None,
    seasonal_periods: int = 5,
    **kwargs: Any,
) -> dict[str, Any]:
    """
    Train Exponential Smoothing (Holt-Winters) model.
    
    Args:
        df: Stock DataFrame.
        horizon: Prediction horizon.
        trend: Trend type ('add', 'mul', None).
        seasonal: Seasonal type ('add', 'mul', None).
        seasonal_periods: Number of periods per season.
        **kwargs: Additional model parameters.
        
    Returns:
        Dictionary with prediction results.
    """
    try:
        series = df["close"].values
        
        if len(series) < 30:
            raise ModelError("Insufficient data", model_type="exp_smoothing")
        
        # Fit model
        model = ExponentialSmoothing(
            series,
            trend=trend,
            seasonal=seasonal,
            seasonal_periods=seasonal_periods if seasonal else None,
        )
        fitted = model.fit()
        
        # Forecast
        steps = max(1, HORIZON_DAYS.get(horizon, 1))
        forecast = fitted.forecast(steps=steps)
        predicted_price = float(forecast[-1])
        
        current_price = float(series[-1])
        predicted_change = ((predicted_price - current_price) / current_price) * 100
        
        return {
            "model_type": "exp_smoothing",
            "horizon": horizon,
            "predicted_price": round(predicted_price, 4),
            "predicted_change_pct": round(predicted_change, 4),
            "confidence": 0.5,  # Default confidence for ETS
            "current_price": current_price,
        }
        
    except Exception as e:
        logger.error("exp_smoothing_failed", error=str(e))
        raise ModelError(f"Exp Smoothing failed: {str(e)}", model_type="exp_smoothing") from e


def run_all_ml_models(
    df: pd.DataFrame,
    ticker: str,
    horizons: list[str] = ["1d", "1w"],
) -> list[dict[str, Any]]:
    """
    Run all ML models for a ticker across multiple horizons.
    
    Args:
        df: Stock DataFrame with indicators.
        ticker: Stock ticker symbol.
        horizons: List of prediction horizons.
        
    Returns:
        List of prediction results from all models.
    """
    results: list[dict[str, Any]] = []
    models = [
        ("linear_regression", train_linear_regression),
        ("random_forest", train_random_forest),
        ("xgboost", train_xgboost),
        ("arima", train_arima),
        ("exp_smoothing", train_exponential_smoothing),
    ]
    
    for horizon in horizons:
        for model_name, model_fn in models:
            try:
                result = model_fn(df, horizon=horizon)
                result["ticker"] = ticker
                result["prediction_date"] = datetime.now().date()
                result["target_date"] = (
                    datetime.now() + timedelta(days=HORIZON_DAYS.get(horizon, 1))
                ).date()
                results.append(result)
                
                logger.info(
                    "model_prediction_complete",
                    ticker=ticker,
                    model=model_name,
                    horizon=horizon,
                    predicted_price=result["predicted_price"],
                )
                
            except ModelError as e:
                logger.warning(
                    "model_prediction_failed",
                    ticker=ticker,
                    model=model_name,
                    horizon=horizon,
                    error=str(e),
                )
                continue
    
    return results
