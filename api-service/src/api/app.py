"""
Flask API Application with Socket.IO.

Main entry point for the API service.
"""

import os

from flask import Flask, jsonify
from flask_socketio import SocketIO
from flask_cors import CORS
import structlog

from .config import config
from .database import health_check
from .routers.stocks import stocks_bp
from .routers.predictions import predictions_bp
from .routers.portfolios import portfolios_bp
from .routers.users import users_bp
from .socket_events import register_socket_events, start_price_broadcaster

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


def create_app() -> Flask:
    """
    Create and configure Flask application.
    
    Returns:
        Configured Flask app instance.
    """
    app = Flask(__name__)
    
    # Configuration
    app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY", "dev-secret")
    app.config["DEBUG"] = config.debug
    
    # CORS
    CORS(app, origins=config.cors_origins, supports_credentials=True)
    
    # Register blueprints
    app.register_blueprint(stocks_bp)
    app.register_blueprint(predictions_bp)
    app.register_blueprint(portfolios_bp)
    app.register_blueprint(users_bp)
    
    # Health check endpoint
    @app.route("/health", methods=["GET"])
    def health():
        """Health check endpoint."""
        db_healthy = health_check()
        
        return jsonify({
            "status": "healthy" if db_healthy else "degraded",
            "database": "connected" if db_healthy else "disconnected",
        }), 200 if db_healthy else 503
    
    # API info endpoint
    @app.route("/api", methods=["GET"])
    def api_info():
        """API information endpoint."""
        return jsonify({
            "name": "Stock Market Dashboard API",
            "version": "1.0.0",
            "endpoints": {
                "stocks": "/api/stocks",
                "predictions": "/api/predictions",
                "sentiment": "/api/predictions/sentiment/<ticker>",
                "portfolio": "/api/portfolio",
                "wishlist": "/api/wishlist",
                "auth": "/api/auth",
            },
            "websocket": {
                "events": ["subscribe", "unsubscribe", "price_update"],
            },
        })
    
    # Error handlers
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({"error": "Bad request"}), 400
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"error": "Not found"}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        logger.error("internal_error", error=str(error))
        return jsonify({"error": "Internal server error"}), 500
    
    logger.info("app_created")
    
    return app


def create_socketio(app: Flask) -> SocketIO:
    """
    Create and configure Socket.IO instance.
    
    Args:
        app: Flask application.
        
    Returns:
        Configured SocketIO instance.
    """
    socketio = SocketIO(
        app,
        cors_allowed_origins=config.cors_origins,
        async_mode="eventlet",
        logger=False,
        engineio_logger=False,
    )
    
    # Register socket events
    register_socket_events(socketio)
    
    return socketio


# Create application instances
app = create_app()
socketio = create_socketio(app)


if __name__ == "__main__":
    import eventlet
    eventlet.monkey_patch()
    
    # Start price broadcaster
    start_price_broadcaster(socketio)
    
    # Run server
    logger.info("starting_server", host="0.0.0.0", port=5000)
    socketio.run(app, host="0.0.0.0", port=5000, debug=config.debug)
