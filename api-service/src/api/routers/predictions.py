"""
Predictions router - endpoints for ML predictions and sentiment.
"""

from flask import Blueprint, jsonify, request
import structlog

from ..database import execute_query, execute_one

logger = structlog.get_logger(__name__)

predictions_bp = Blueprint("predictions", __name__, url_prefix="/api/predictions")


@predictions_bp.route("/<ticker>", methods=["GET"])
def get_predictions(ticker: str):
    """
    Get all predictions for a ticker.
    
    Query params:
        - model: Filter by model type
        - horizon: Filter by horizon
    """
    model_filter = request.args.get("model")
    horizon_filter = request.args.get("horizon")
    
    query = """
        SELECT ticker, prediction_date, target_date, model_type, horizon,
               predicted_price, predicted_change_pct, confidence
        FROM predictions
        WHERE ticker = %s
    """
    params: list = [ticker]
    
    if model_filter:
        query += " AND model_type = %s"
        params.append(model_filter)
    
    if horizon_filter:
        query += " AND horizon = %s"
        params.append(horizon_filter)
    
    query += " ORDER BY prediction_date DESC, model_type, horizon LIMIT 100"
    
    predictions = execute_query(query, tuple(params))
    
    # Convert types
    for pred in predictions:
        for key, value in pred.items():
            if hasattr(value, "__float__"):
                pred[key] = float(value)
            if "date" in key and value:
                pred[key] = str(value)
    
    return jsonify({
        "ticker": ticker,
        "data": predictions,
        "count": len(predictions),
    })


@predictions_bp.route("/<ticker>/latest", methods=["GET"])
def get_latest_predictions(ticker: str):
    """Get latest predictions grouped by model and horizon."""
    query = """
        WITH ranked AS (
            SELECT *,
                   ROW_NUMBER() OVER (
                       PARTITION BY model_type, horizon 
                       ORDER BY prediction_date DESC
                   ) as rn
            FROM predictions
            WHERE ticker = %s
        )
        SELECT ticker, prediction_date, target_date, model_type, horizon,
               predicted_price, predicted_change_pct, confidence
        FROM ranked
        WHERE rn = 1
        ORDER BY model_type, horizon
    """
    
    predictions = execute_query(query, (ticker,))
    
    # Convert types
    for pred in predictions:
        for key, value in pred.items():
            if hasattr(value, "__float__"):
                pred[key] = float(value)
            if "date" in key and value:
                pred[key] = str(value)
    
    # Group by model type
    grouped: dict = {}
    for pred in predictions:
        model = pred["model_type"]
        if model not in grouped:
            grouped[model] = []
        grouped[model].append(pred)
    
    return jsonify({
        "ticker": ticker,
        "predictions": grouped,
    })


@predictions_bp.route("/models", methods=["GET"])
def get_available_models():
    """Get list of available prediction models."""
    query = """
        SELECT DISTINCT model_type
        FROM predictions
        ORDER BY model_type
    """
    
    models = execute_query(query, None)
    
    return jsonify({
        "models": [m["model_type"] for m in models],
    })


@predictions_bp.route("/templates", methods=["GET"])
def get_prediction_templates():
    """Get all prediction templates."""
    query = """
        SELECT id, name, model_type, parameters, description, is_active
        FROM prediction_templates
        WHERE is_active = TRUE
        ORDER BY name
    """
    
    templates = execute_query(query, None)
    
    # Convert UUID to string
    for template in templates:
        template["id"] = str(template["id"])
    
    return jsonify({"data": templates})


@predictions_bp.route("/sentiment/<ticker>", methods=["GET"])
def get_sentiment(ticker: str):
    """
    Get sentiment analysis for a ticker.
    
    Query params:
        - days: Number of days (default: 30)
    """
    days = min(request.args.get("days", 30, type=int), 90)
    
    query = """
        SELECT date, positive_score, negative_score, neutral_score,
               overall_sentiment, headline
        FROM sentiment_scores
        WHERE ticker = %s
        ORDER BY date DESC
        LIMIT %s
    """
    
    sentiments = execute_query(query, (ticker, days))
    
    # Convert types
    for sent in sentiments:
        for key, value in sent.items():
            if hasattr(value, "__float__"):
                sent[key] = float(value)
            if key == "date" and value:
                sent[key] = str(value)
    
    # Calculate aggregate if we have data
    if sentiments:
        avg_positive = sum(s["positive_score"] for s in sentiments) / len(sentiments)
        avg_negative = sum(s["negative_score"] for s in sentiments) / len(sentiments)
        avg_neutral = sum(s["neutral_score"] for s in sentiments) / len(sentiments)
        
        aggregate = {
            "positive": round(avg_positive, 4),
            "negative": round(avg_negative, 4),
            "neutral": round(avg_neutral, 4),
            "overall": "positive" if avg_positive > avg_negative else (
                "negative" if avg_negative > avg_positive else "neutral"
            ),
        }
    else:
        aggregate = None
    
    return jsonify({
        "ticker": ticker,
        "aggregate": aggregate,
        "data": sentiments,
        "count": len(sentiments),
    })
