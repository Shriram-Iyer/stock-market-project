"""
Unit tests for API service.
"""

import pytest
from unittest.mock import patch, MagicMock

# Test fixtures
@pytest.fixture
def app():
    """Create test application."""
    from api.app import create_app
    
    app = create_app()
    app.config["TESTING"] = True
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


class TestHealthEndpoint:
    """Tests for health check endpoint."""
    
    @patch("api.app.health_check")
    def test_health_check_healthy(self, mock_health, client):
        """Test health check when database is connected."""
        mock_health.return_value = True
        
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "healthy"
        assert data["database"] == "connected"
    
    @patch("api.app.health_check")
    def test_health_check_degraded(self, mock_health, client):
        """Test health check when database is disconnected."""
        mock_health.return_value = False
        
        response = client.get("/health")
        
        assert response.status_code == 503
        data = response.get_json()
        assert data["status"] == "degraded"


class TestAPIInfo:
    """Tests for API info endpoint."""
    
    def test_api_info(self, client):
        """Test API info returns expected structure."""
        response = client.get("/api")
        
        assert response.status_code == 200
        data = response.get_json()
        assert data["name"] == "Stock Market Dashboard API"
        assert "endpoints" in data
        assert "websocket" in data


class TestStocksEndpoints:
    """Tests for stocks endpoints."""
    
    @patch("api.routers.stocks.execute_query")
    def test_get_stocks(self, mock_query, client):
        """Test getting stock list."""
        mock_query.return_value = [
            {"ticker": "RELIANCE.NS", "close": 2500.0, "date": "2025-01-01"}
        ]
        
        response = client.get("/api/stocks")
        
        assert response.status_code == 200
        data = response.get_json()
        assert "data" in data
        assert "page" in data
    
    @patch("api.routers.stocks.execute_one")
    def test_get_stock_not_found(self, mock_query, client):
        """Test getting non-existent stock."""
        mock_query.return_value = None
        
        response = client.get("/api/stocks/INVALID.NS")
        
        assert response.status_code == 404


class TestAuthEndpoints:
    """Tests for authentication endpoints."""
    
    @patch("api.routers.users.signup_user")
    def test_signup_success(self, mock_signup, client):
        """Test successful user registration."""
        mock_signup.return_value = {
            "id": "123",
            "email": "test@example.com",
            "username": "testuser",
        }
        
        response = client.post("/api/auth/signup", json={
            "email": "test@example.com",
            "username": "testuser",
            "password": "password123",
        })
        
        assert response.status_code == 201
        data = response.get_json()
        assert "user" in data
    
    def test_signup_missing_fields(self, client):
        """Test signup with missing fields."""
        response = client.post("/api/auth/signup", json={
            "email": "test@example.com",
        })
        
        assert response.status_code == 400
    
    @patch("api.routers.users.login_user")
    def test_login_success(self, mock_login, client):
        """Test successful login."""
        mock_login.return_value = (
            {"id": "123", "email": "test@example.com", "username": "testuser"},
            "jwt-token-here",
        )
        
        response = client.post("/api/auth/login", json={
            "email": "test@example.com",
            "password": "password123",
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert "token" in data
    
    @patch("api.routers.users.login_user")
    def test_login_invalid_credentials(self, mock_login, client):
        """Test login with invalid credentials."""
        mock_login.return_value = None
        
        response = client.post("/api/auth/login", json={
            "email": "test@example.com",
            "password": "wrongpassword",
        })
        
        assert response.status_code == 401


class TestAuth:
    """Tests for auth module."""
    
    def test_hash_password(self):
        """Test password hashing."""
        from api.auth import hash_password, verify_password
        
        password = "testpassword123"
        hashed = hash_password(password)
        
        assert hashed != password
        assert verify_password(password, hashed)
        assert not verify_password("wrongpassword", hashed)
    
    @patch("api.auth.config")
    def test_create_token(self, mock_config):
        """Test JWT token creation."""
        from api.auth import create_token, decode_token
        
        mock_config.jwt.secret = "test-secret"
        mock_config.jwt.algorithm = "HS256"
        mock_config.jwt.expiry_hours = 24
        
        token = create_token("user-123", "test@example.com")
        
        assert token is not None
        assert isinstance(token, str)
