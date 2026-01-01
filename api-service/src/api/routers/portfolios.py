"""
Portfolios router - endpoints for portfolio and wishlist management.
"""

from flask import Blueprint, jsonify, request, g
from datetime import date
import structlog

from ..auth import require_auth
from ..database import execute_query, execute_one, execute_insert, get_connection

logger = structlog.get_logger(__name__)

portfolios_bp = Blueprint("portfolios", __name__, url_prefix="/api")


# =====================================================
# Portfolio Endpoints
# =====================================================

@portfolios_bp.route("/portfolio", methods=["GET"])
@require_auth
def get_portfolio():
    """Get user's portfolio with current values."""
    user_id = g.current_user["id"]
    
    query = """
        SELECT p.id, p.ticker, p.quantity, p.buy_price, p.buy_date, p.notes,
               s.close as current_price, s.date as price_date
        FROM portfolios p
        LEFT JOIN LATERAL (
            SELECT close, date
            FROM stocks
            WHERE ticker = p.ticker
            ORDER BY date DESC
            LIMIT 1
        ) s ON TRUE
        WHERE p.user_id = %s
        ORDER BY p.ticker
    """
    
    holdings = execute_query(query, (user_id,))
    
    # Calculate values and P&L
    total_investment = 0
    total_current_value = 0
    
    for holding in holdings:
        holding["id"] = str(holding["id"])
        
        for key, value in holding.items():
            if hasattr(value, "__float__"):
                holding[key] = float(value)
            if "date" in key and value:
                holding[key] = str(value)
        
        investment = holding["quantity"] * holding["buy_price"]
        current_value = holding["quantity"] * (holding.get("current_price") or holding["buy_price"])
        pnl = current_value - investment
        pnl_pct = (pnl / investment * 100) if investment > 0 else 0
        
        holding["investment"] = round(investment, 2)
        holding["current_value"] = round(current_value, 2)
        holding["pnl"] = round(pnl, 2)
        holding["pnl_pct"] = round(pnl_pct, 2)
        
        total_investment += investment
        total_current_value += current_value
    
    total_pnl = total_current_value - total_investment
    total_pnl_pct = (total_pnl / total_investment * 100) if total_investment > 0 else 0
    
    return jsonify({
        "holdings": holdings,
        "summary": {
            "total_investment": round(total_investment, 2),
            "total_current_value": round(total_current_value, 2),
            "total_pnl": round(total_pnl, 2),
            "total_pnl_pct": round(total_pnl_pct, 2),
        },
    })


@portfolios_bp.route("/portfolio", methods=["POST"])
@require_auth
def add_to_portfolio():
    """Add stock to portfolio."""
    user_id = g.current_user["id"]
    data = request.get_json()
    
    # Validate required fields
    required = ["ticker", "quantity", "buy_price"]
    if not all(field in data for field in required):
        return jsonify({"error": f"Missing required fields: {required}"}), 400
    
    ticker = data["ticker"].upper()
    quantity = float(data["quantity"])
    buy_price = float(data["buy_price"])
    buy_date = data.get("buy_date", str(date.today()))
    notes = data.get("notes", "")
    
    if quantity <= 0 or buy_price <= 0:
        return jsonify({"error": "Quantity and buy_price must be positive"}), 400
    
    try:
        result = execute_insert(
            """
            INSERT INTO portfolios (user_id, ticker, quantity, buy_price, buy_date, notes)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id, ticker, quantity, buy_price, buy_date
            """,
            (user_id, ticker, quantity, buy_price, buy_date, notes)
        )
        
        if result:
            result["id"] = str(result["id"])
            for key, value in result.items():
                if hasattr(value, "__float__"):
                    result[key] = float(value)
                if "date" in key and value:
                    result[key] = str(value)
        
        return jsonify(result), 201
        
    except Exception as e:
        logger.error("portfolio_add_failed", error=str(e))
        return jsonify({"error": "Failed to add to portfolio"}), 500


@portfolios_bp.route("/portfolio/<holding_id>", methods=["DELETE"])
@require_auth
def remove_from_portfolio(holding_id: str):
    """Remove stock from portfolio."""
    user_id = g.current_user["id"]
    
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM portfolios WHERE id = %s AND user_id = %s",
            (holding_id, user_id)
        )
        deleted = cursor.rowcount
        conn.commit()
    
    if deleted == 0:
        return jsonify({"error": "Holding not found"}), 404
    
    return jsonify({"message": "Holding removed"}), 200


@portfolios_bp.route("/portfolio/risk", methods=["GET"])
@require_auth
def get_portfolio_risk():
    """Calculate portfolio risk metrics."""
    user_id = g.current_user["id"]
    
    # Get portfolio with volatility data
    query = """
        SELECT p.ticker, p.quantity, p.buy_price,
               m.volatility, s.close as current_price
        FROM portfolios p
        LEFT JOIN LATERAL (
            SELECT close, date
            FROM stocks
            WHERE ticker = p.ticker
            ORDER BY date DESC
            LIMIT 1
        ) s ON TRUE
        LEFT JOIN stock_metrics m ON p.ticker = m.ticker AND m.date = s.date
        WHERE p.user_id = %s
    """
    
    holdings = execute_query(query, (user_id,))
    
    if not holdings:
        return jsonify({
            "portfolio_volatility": 0,
            "risk_score": 0,
            "risk_level": "None",
            "holdings": [],
        })
    
    # Calculate weighted volatility
    total_value = 0
    weighted_volatility = 0
    holding_risks = []
    
    for h in holdings:
        current_price = float(h.get("current_price") or h["buy_price"])
        value = float(h["quantity"]) * current_price
        volatility = float(h.get("volatility") or 0.2)  # Default 20%
        
        total_value += value
        weighted_volatility += value * volatility
        
        holding_risks.append({
            "ticker": h["ticker"],
            "value": round(value, 2),
            "volatility": round(volatility * 100, 2),
        })
    
    portfolio_volatility = (weighted_volatility / total_value) if total_value > 0 else 0
    
    # Risk score (1-10 scale)
    risk_score = min(10, max(1, int(portfolio_volatility * 20)))
    
    # Risk level
    if risk_score <= 3:
        risk_level = "Low"
    elif risk_score <= 6:
        risk_level = "Medium"
    else:
        risk_level = "High"
    
    return jsonify({
        "portfolio_volatility": round(portfolio_volatility * 100, 2),
        "risk_score": risk_score,
        "risk_level": risk_level,
        "total_value": round(total_value, 2),
        "holdings": holding_risks,
    })


# =====================================================
# Wishlist Endpoints
# =====================================================

@portfolios_bp.route("/wishlist", methods=["GET"])
@require_auth
def get_wishlist():
    """Get user's wishlist."""
    user_id = g.current_user["id"]
    
    query = """
        SELECT w.id, w.ticker, w.added_at, w.notes,
               s.close as current_price, s.date as price_date
        FROM wishlists w
        LEFT JOIN LATERAL (
            SELECT close, date
            FROM stocks
            WHERE ticker = w.ticker
            ORDER BY date DESC
            LIMIT 1
        ) s ON TRUE
        WHERE w.user_id = %s
        ORDER BY w.added_at DESC
    """
    
    items = execute_query(query, (user_id,))
    
    for item in items:
        item["id"] = str(item["id"])
        for key, value in item.items():
            if hasattr(value, "__float__"):
                item[key] = float(value)
            if "date" in key or "at" in key:
                if value:
                    item[key] = str(value)
    
    return jsonify({"data": items})


@portfolios_bp.route("/wishlist", methods=["POST"])
@require_auth
def add_to_wishlist():
    """Add stock to wishlist."""
    user_id = g.current_user["id"]
    data = request.get_json()
    
    if "ticker" not in data:
        return jsonify({"error": "Missing ticker"}), 400
    
    ticker = data["ticker"].upper()
    notes = data.get("notes", "")
    
    # Check if already in wishlist
    existing = execute_one(
        "SELECT id FROM wishlists WHERE user_id = %s AND ticker = %s",
        (user_id, ticker)
    )
    
    if existing:
        return jsonify({"error": "Already in wishlist"}), 409
    
    result = execute_insert(
        """
        INSERT INTO wishlists (user_id, ticker, notes)
        VALUES (%s, %s, %s)
        RETURNING id, ticker, added_at
        """,
        (user_id, ticker, notes)
    )
    
    if result:
        result["id"] = str(result["id"])
        result["added_at"] = str(result["added_at"])
    
    return jsonify(result), 201


@portfolios_bp.route("/wishlist/<item_id>", methods=["DELETE"])
@require_auth
def remove_from_wishlist(item_id: str):
    """Remove stock from wishlist."""
    user_id = g.current_user["id"]
    
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM wishlists WHERE id = %s AND user_id = %s",
            (item_id, user_id)
        )
        deleted = cursor.rowcount
        conn.commit()
    
    if deleted == 0:
        return jsonify({"error": "Item not found"}), 404
    
    return jsonify({"message": "Removed from wishlist"}), 200
