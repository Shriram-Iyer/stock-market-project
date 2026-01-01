"""
Socket.IO event handlers for real-time price updates.
"""

import time
from threading import Thread
from typing import Any

import structlog
import yfinance as yf
from flask_socketio import emit, join_room, leave_room

logger = structlog.get_logger(__name__)

# Track subscribed rooms
subscribed_tickers: set[str] = set()


def register_socket_events(socketio: Any) -> None:
    """
    Register Socket.IO event handlers.
    
    Args:
        socketio: Flask-SocketIO instance.
    """
    
    @socketio.on("connect")
    def handle_connect():
        """Handle client connection."""
        logger.info("client_connected")
        emit("connected", {"message": "Connected to price stream"})
    
    @socketio.on("disconnect")
    def handle_disconnect():
        """Handle client disconnection."""
        logger.info("client_disconnected")
    
    @socketio.on("subscribe")
    def handle_subscribe(data: dict):
        """
        Subscribe to price updates for tickers.
        
        Args:
            data: {"tickers": ["RELIANCE.NS", "TCS.NS"]}
        """
        tickers = data.get("tickers", [])
        
        for ticker in tickers:
            join_room(ticker)
            subscribed_tickers.add(ticker)
            logger.info("subscribed", ticker=ticker)
        
        emit("subscribed", {"tickers": tickers})
    
    @socketio.on("unsubscribe")
    def handle_unsubscribe(data: dict):
        """
        Unsubscribe from price updates.
        
        Args:
            data: {"tickers": ["RELIANCE.NS"]}
        """
        tickers = data.get("tickers", [])
        
        for ticker in tickers:
            leave_room(ticker)
            subscribed_tickers.discard(ticker)
            logger.info("unsubscribed", ticker=ticker)
        
        emit("unsubscribed", {"tickers": tickers})


def fetch_live_price(ticker: str) -> dict[str, Any] | None:
    """
    Fetch live price for a ticker.
    
    Args:
        ticker: Stock ticker.
        
    Returns:
        Price data or None.
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        current = info.get("regularMarketPrice") or info.get("previousClose", 0)
        previous = info.get("previousClose", current)
        change = current - previous
        change_pct = (change / previous * 100) if previous > 0 else 0
        
        return {
            "ticker": ticker,
            "price": round(current, 2),
            "change": round(change, 2),
            "change_pct": round(change_pct, 2),
            "timestamp": time.time(),
        }
    except Exception as e:
        logger.warning("price_fetch_failed", ticker=ticker, error=str(e))
        return None


def start_price_broadcaster(socketio: Any) -> None:
    """
    Start background thread for broadcasting prices.
    
    Args:
        socketio: Flask-SocketIO instance.
    """
    def broadcast_prices():
        """Broadcast prices to subscribed rooms."""
        while True:
            for ticker in list(subscribed_tickers):
                price_data = fetch_live_price(ticker)
                if price_data:
                    socketio.emit("price_update", price_data, room=ticker)
            
            # Wait before next update cycle
            time.sleep(10)  # Update every 10 seconds
    
    thread = Thread(target=broadcast_prices, daemon=True)
    thread.start()
    logger.info("price_broadcaster_started")
