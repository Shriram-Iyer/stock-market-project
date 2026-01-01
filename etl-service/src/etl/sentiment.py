"""
Sentiment analysis module.

Uses Hugging Face FinBERT for financial sentiment analysis.
"""

from datetime import datetime
from typing import Any

import structlog

try:
    from transformers import AutoTokenizer, AutoModelForSequenceClassification
    import torch
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

from .config import get_config
from .exceptions import ModelError

logger = structlog.get_logger(__name__)

# Singleton for model caching
_tokenizer = None
_model = None


def load_sentiment_model(model_name: str = "ProsusAI/finbert") -> tuple[Any, Any]:
    """
    Load and cache the sentiment analysis model.
    
    Args:
        model_name: Hugging Face model name.
        
    Returns:
        Tuple of (tokenizer, model).
    """
    global _tokenizer, _model
    
    if not TRANSFORMERS_AVAILABLE:
        raise ModelError("Transformers not installed", model_type="sentiment")
    
    if _tokenizer is None or _model is None:
        config = get_config()
        
        logger.info("loading_sentiment_model", model=model_name)
        
        _tokenizer = AutoTokenizer.from_pretrained(
            model_name,
            token=config.huggingface.token if config.huggingface.token else None,
        )
        _model = AutoModelForSequenceClassification.from_pretrained(
            model_name,
            token=config.huggingface.token if config.huggingface.token else None,
        )
        
        logger.info("sentiment_model_loaded")
    
    return _tokenizer, _model


def analyze_sentiment(text: str) -> dict[str, Any]:
    """
    Analyze sentiment of a single text.
    
    Args:
        text: Text to analyze.
        
    Returns:
        Dictionary with sentiment scores.
    """
    if not TRANSFORMERS_AVAILABLE:
        raise ModelError("Transformers not installed", model_type="sentiment")
    
    try:
        tokenizer, model = load_sentiment_model()
        
        # Tokenize
        inputs = tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=512,
            padding=True,
        )
        
        # Get predictions
        with torch.no_grad():
            outputs = model(**inputs)
            predictions = torch.nn.functional.softmax(outputs.logits, dim=-1)
        
        # FinBERT labels: [positive, negative, neutral]
        scores = predictions[0].tolist()
        
        # Determine overall sentiment
        labels = ["positive", "negative", "neutral"]
        max_idx = scores.index(max(scores))
        overall = labels[max_idx]
        
        return {
            "positive_score": round(scores[0], 4),
            "negative_score": round(scores[1], 4),
            "neutral_score": round(scores[2], 4),
            "overall_sentiment": overall,
            "text": text[:200],  # Truncate for storage
        }
        
    except Exception as e:
        logger.error("sentiment_analysis_failed", error=str(e))
        raise ModelError(f"Sentiment analysis failed: {str(e)}", model_type="sentiment") from e


def analyze_batch_sentiment(texts: list[str]) -> list[dict[str, Any]]:
    """
    Analyze sentiment for multiple texts.
    
    Args:
        texts: List of texts to analyze.
        
    Returns:
        List of sentiment results.
    """
    results: list[dict[str, Any]] = []
    
    for text in texts:
        try:
            result = analyze_sentiment(text)
            results.append(result)
        except ModelError as e:
            logger.warning("batch_sentiment_failed", text=text[:50], error=str(e))
            continue
    
    return results


def get_aggregated_sentiment(
    sentiments: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Aggregate multiple sentiment scores.
    
    Args:
        sentiments: List of sentiment results.
        
    Returns:
        Aggregated sentiment scores.
    """
    if not sentiments:
        return {
            "positive_score": 0.0,
            "negative_score": 0.0,
            "neutral_score": 0.0,
            "overall_sentiment": "neutral",
            "sample_count": 0,
        }
    
    avg_positive = sum(s["positive_score"] for s in sentiments) / len(sentiments)
    avg_negative = sum(s["negative_score"] for s in sentiments) / len(sentiments)
    avg_neutral = sum(s["neutral_score"] for s in sentiments) / len(sentiments)
    
    # Determine overall
    scores = {"positive": avg_positive, "negative": avg_negative, "neutral": avg_neutral}
    overall = max(scores, key=scores.get)  # type: ignore
    
    return {
        "positive_score": round(avg_positive, 4),
        "negative_score": round(avg_negative, 4),
        "neutral_score": round(avg_neutral, 4),
        "overall_sentiment": overall,
        "sample_count": len(sentiments),
    }


# Sample headlines for demo (in production, fetch from news API)
SAMPLE_HEADLINES: dict[str, list[str]] = {
    "RELIANCE.NS": [
        "Reliance Industries reports strong quarterly earnings",
        "Jio gains market share in telecom sector",
        "Reliance Retail expansion continues across India",
    ],
    "TCS.NS": [
        "TCS wins major digital transformation deal",
        "IT sector faces headwinds amid global slowdown",
        "TCS announces dividend for shareholders",
    ],
    "HDFCBANK.NS": [
        "HDFC Bank merger integration progresses smoothly",
        "Banking sector sees improved credit growth",
        "HDFC Bank launches new digital initiatives",
    ],
    "INFY.NS": [
        "Infosys revises guidance amid market uncertainty",
        "Infosys partners with global tech giants",
        "IT stocks face pressure on weak outlook",
    ],
    "DEFAULT": [
        "Stock markets show mixed trends today",
        "Foreign investors continue buying Indian equities",
        "Market volatility continues amid global cues",
    ],
}


def get_stock_sentiment(
    ticker: str,
    headlines: list[str] | None = None,
) -> dict[str, Any]:
    """
    Get sentiment analysis for a stock.
    
    Args:
        ticker: Stock ticker.
        headlines: Optional list of headlines. If None, uses samples.
        
    Returns:
        Aggregated sentiment for the stock.
    """
    if headlines is None:
        # Use sample headlines for demo
        headlines = SAMPLE_HEADLINES.get(
            ticker,
            SAMPLE_HEADLINES["DEFAULT"],
        )
    
    sentiments = analyze_batch_sentiment(headlines)
    aggregated = get_aggregated_sentiment(sentiments)
    
    return {
        "ticker": ticker,
        "date": datetime.now().date(),
        **aggregated,
    }
