"""
Stocks router - endpoints for stock data and metrics.
"""

from flask import Blueprint, jsonify, request
import structlog

from ..database import execute_query, execute_one

logger = structlog.get_logger(__name__)

stocks_bp = Blueprint("stocks", __name__, url_prefix="/api/stocks")


@stocks_bp.route("", methods=["GET"])
def get_stocks():
    """
    Get list of all stocks with latest data.
    
    Query params:
        - page: Page number (default: 1)
        - limit: Items per page (default: 50)
        - index: 'NIFTY50' or 'NIFTY100' (default: all)
    """
    page = request.args.get("page", 1, type=int)
    limit = min(request.args.get("limit", 50, type=int), 100)
    offset = (page - 1) * limit
    
    # Get latest data for each ticker
    query = """
        WITH latest AS (
            SELECT ticker, MAX(date) as max_date
            FROM stocks
            GROUP BY ticker
        )
        SELECT s.ticker, s.date, s.open, s.high, s.low, s.close, s.volume,
               m.ma_50, m.rsi_14, m.volatility
        FROM stocks s
        JOIN latest l ON s.ticker = l.ticker AND s.date = l.max_date
        LEFT JOIN stock_metrics m ON s.ticker = m.ticker AND s.date = m.date
        ORDER BY s.ticker
        LIMIT %s OFFSET %s
    """
    
    stocks = execute_query(query, (limit, offset))
    
    # Convert Decimal to float for JSON serialization
    for stock in stocks:
        for key, value in stock.items():
            if hasattr(value, "__float__"):
                stock[key] = float(value)
        if stock.get("date"):
            stock["date"] = str(stock["date"])
    
    return jsonify({
        "data": stocks,
        "page": page,
        "limit": limit,
        "total": len(stocks),
    })


@stocks_bp.route("/<ticker>", methods=["GET"])
def get_stock(ticker: str):
    """
    Get detailed stock information.
    
    Args:
        ticker: Stock ticker symbol.
    """
    # Get latest stock data with metrics
    query = """
        SELECT s.ticker, s.date, s.open, s.high, s.low, s.close, s.volume,
               m.ma_10, m.ma_20, m.ma_50, m.ma_200,
               m.rsi_14, m.macd, m.macd_signal, m.macd_histogram,
               m.bollinger_upper, m.bollinger_middle, m.bollinger_lower,
               m.volatility, m.volume_ma_20
        FROM stocks s
        LEFT JOIN stock_metrics m ON s.ticker = m.ticker AND s.date = m.date
        WHERE s.ticker = %s
        ORDER BY s.date DESC
        LIMIT 1
    """
    
    stock = execute_one(query, (ticker,))
    
    if not stock:
        return jsonify({"error": "Stock not found"}), 404
    
    # Convert types
    for key, value in stock.items():
        if hasattr(value, "__float__"):
            stock[key] = float(value)
        if key == "date" and value:
            stock[key] = str(value)
    
    return jsonify(stock)


@stocks_bp.route("/<ticker>/history", methods=["GET"])
def get_stock_history(ticker: str):
    """
    Get historical OHLCV data for a stock.
    
    Query params:
        - days: Number of days (default: 365, max: 730)
    """
    days = min(request.args.get("days", 365, type=int), 730)
    
    query = """
        SELECT date, open, high, low, close, volume
        FROM stocks
        WHERE ticker = %s
        ORDER BY date DESC
        LIMIT %s
    """
    
    history = execute_query(query, (ticker, days))
    
    # Convert types
    for row in history:
        for key, value in row.items():
            if hasattr(value, "__float__"):
                row[key] = float(value)
            if key == "date" and value:
                row[key] = str(value)
    
    # Reverse to chronological order
    history.reverse()
    
    return jsonify({
        "ticker": ticker,
        "data": history,
        "count": len(history),
    })


@stocks_bp.route("/<ticker>/metrics", methods=["GET"])
def get_stock_metrics(ticker: str):
    """
    Get technical metrics history for a stock.
    
    Query params:
        - days: Number of days (default: 30)
    """
    days = min(request.args.get("days", 30, type=int), 365)
    
    query = """
        SELECT date, ma_10, ma_20, ma_50, ma_200,
               rsi_14, macd, macd_signal, macd_histogram,
               bollinger_upper, bollinger_middle, bollinger_lower,
               volatility, volume_ma_20
        FROM stock_metrics
        WHERE ticker = %s
        ORDER BY date DESC
        LIMIT %s
    """
    
    metrics = execute_query(query, (ticker, days))
    
    # Convert types
    for row in metrics:
        for key, value in row.items():
            if hasattr(value, "__float__"):
                row[key] = float(value)
            if key == "date" and value:
                row[key] = str(value)
    
    metrics.reverse()
    
    return jsonify({
        "ticker": ticker,
        "data": metrics,
        "count": len(metrics),
    })


@stocks_bp.route("/search", methods=["GET"])
def search_stocks():
    """
    Search stocks by ticker or name.
    
    Query params:
        - q: Search query
    """
    query_param = request.args.get("q", "").upper()
    
    if not query_param or len(query_param) < 2:
        return jsonify({"data": []})
    
    query = """
        SELECT DISTINCT ticker
        FROM stocks
        WHERE ticker LIKE %s
        ORDER BY ticker
        LIMIT 20
    """
    
    results = execute_query(query, (f"%{query_param}%",))
    
    return jsonify({
        "data": [r["ticker"] for r in results],
    })
