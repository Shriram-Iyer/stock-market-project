"""
LSTM model for stock price prediction.

Uses TensorFlow/Keras for deep learning time series forecasting.
"""

from datetime import datetime, timedelta
from typing import Any

import numpy as np
import pandas as pd
import structlog

try:
    import tensorflow as tf
    from tensorflow import keras
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import LSTM, Dense, Dropout
    from tensorflow.keras.callbacks import EarlyStopping
    TENSORFLOW_AVAILABLE = True
except ImportError:
    TENSORFLOW_AVAILABLE = False

from .exceptions import ModelError

logger = structlog.get_logger(__name__)


def create_sequences(
    data: np.ndarray,
    sequence_length: int = 60,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Create sequences for LSTM training.
    
    Args:
        data: 1D array of values.
        sequence_length: Number of time steps to look back.
        
    Returns:
        Tuple of (X, y) arrays.
    """
    X, y = [], []
    for i in range(sequence_length, len(data)):
        X.append(data[i - sequence_length:i])
        y.append(data[i])
    return np.array(X), np.array(y)


def build_lstm_model(
    sequence_length: int,
    n_features: int = 1,
    units: int = 50,
    dropout: float = 0.2,
) -> Any:
    """
    Build LSTM model architecture.
    
    Args:
        sequence_length: Input sequence length.
        n_features: Number of features.
        units: LSTM units.
        dropout: Dropout rate.
        
    Returns:
        Compiled Keras model.
    """
    if not TENSORFLOW_AVAILABLE:
        raise ModelError("TensorFlow not available", model_type="lstm")
    
    model = Sequential([
        LSTM(units=units, return_sequences=True, 
             input_shape=(sequence_length, n_features)),
        Dropout(dropout),
        LSTM(units=units, return_sequences=False),
        Dropout(dropout),
        Dense(units=25, activation='relu'),
        Dense(units=1),
    ])
    
    model.compile(optimizer='adam', loss='mse', metrics=['mae'])
    return model


def train_lstm(
    df: pd.DataFrame,
    horizon: str = "1d",
    units: int = 50,
    epochs: int = 50,
    batch_size: int = 32,
    sequence_length: int = 60,
    **kwargs: Any,
) -> dict[str, Any]:
    """
    Train LSTM model and make prediction.
    
    Args:
        df: Stock DataFrame with 'close' column.
        horizon: Prediction horizon.
        units: LSTM units.
        epochs: Training epochs.
        batch_size: Training batch size.
        sequence_length: Sequence length for LSTM.
        **kwargs: Additional parameters.
        
    Returns:
        Dictionary with prediction results.
    """
    if not TENSORFLOW_AVAILABLE:
        raise ModelError("TensorFlow not installed", model_type="lstm")
    
    try:
        # Prepare data
        close_prices = df["close"].values.reshape(-1, 1)
        
        if len(close_prices) < sequence_length + 10:
            raise ModelError(
                f"Insufficient data: need at least {sequence_length + 10} points",
                model_type="lstm",
            )
        
        # Normalize data
        from sklearn.preprocessing import MinMaxScaler
        scaler = MinMaxScaler(feature_range=(0, 1))
        scaled_data = scaler.fit_transform(close_prices)
        
        # Create sequences
        X, y = create_sequences(scaled_data.flatten(), sequence_length)
        X = X.reshape(X.shape[0], X.shape[1], 1)
        
        # Split data
        split_idx = int(len(X) * 0.8)
        X_train, X_test = X[:split_idx], X[split_idx:]
        y_train, y_test = y[:split_idx], y[split_idx:]
        
        # Build and train model
        model = build_lstm_model(sequence_length, units=units)
        
        early_stop = EarlyStopping(
            monitor='val_loss',
            patience=10,
            restore_best_weights=True,
        )
        
        # Suppress TensorFlow logging
        tf.get_logger().setLevel('ERROR')
        
        history = model.fit(
            X_train, y_train,
            epochs=epochs,
            batch_size=batch_size,
            validation_data=(X_test, y_test),
            callbacks=[early_stop],
            verbose=0,
        )
        
        # Make prediction
        last_sequence = scaled_data[-sequence_length:].reshape(1, sequence_length, 1)
        predicted_scaled = model.predict(last_sequence, verbose=0)
        predicted_price = float(scaler.inverse_transform(predicted_scaled)[0, 0])
        
        current_price = float(close_prices[-1])
        predicted_change = ((predicted_price - current_price) / current_price) * 100
        
        # Calculate confidence from validation loss
        val_loss = min(history.history.get('val_loss', [1.0]))
        confidence = max(0, min(1, 1 - val_loss))
        
        return {
            "model_type": "lstm",
            "horizon": horizon,
            "predicted_price": round(predicted_price, 4),
            "predicted_change_pct": round(predicted_change, 4),
            "confidence": round(confidence, 4),
            "current_price": current_price,
        }
        
    except Exception as e:
        logger.error("lstm_training_failed", error=str(e))
        raise ModelError(f"LSTM training failed: {str(e)}", model_type="lstm") from e


def run_lstm_predictions(
    df: pd.DataFrame,
    ticker: str,
    horizons: list[str] = ["1d", "1w"],
) -> list[dict[str, Any]]:
    """
    Run LSTM predictions for multiple horizons.
    
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
            result = train_lstm(df, horizon=horizon)
            result["ticker"] = ticker
            result["prediction_date"] = datetime.now().date()
            
            # Calculate target date based on horizon
            horizon_days = {"1h": 0, "4h": 0, "1d": 1, "3d": 3, "1w": 7, "1m": 30}
            days = horizon_days.get(horizon, 1)
            result["target_date"] = (datetime.now() + timedelta(days=days)).date()
            
            results.append(result)
            
            logger.info(
                "lstm_prediction_complete",
                ticker=ticker,
                horizon=horizon,
                predicted_price=result["predicted_price"],
            )
            
        except ModelError as e:
            logger.warning(
                "lstm_prediction_failed",
                ticker=ticker,
                horizon=horizon,
                error=str(e),
            )
            continue
    
    return results
