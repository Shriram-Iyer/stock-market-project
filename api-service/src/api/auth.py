"""
JWT Authentication module.
"""

from datetime import datetime, timedelta, timezone
from functools import wraps
from typing import Any, Callable

import jwt
import bcrypt
from flask import request, jsonify, g
import structlog

from .config import config
from .database import execute_one, execute_insert

logger = structlog.get_logger(__name__)


def hash_password(password: str) -> str:
    """Hash password using bcrypt."""
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')


def verify_password(password: str, password_hash: str) -> bool:
    """Verify password against hash."""
    password_bytes = password.encode('utf-8')
    hash_bytes = password_hash.encode('utf-8')
    return bcrypt.checkpw(password_bytes, hash_bytes)


def create_token(user_id: str, email: str) -> str:
    """
    Create JWT token for user.
    
    Args:
        user_id: User UUID.
        email: User email.
        
    Returns:
        Encoded JWT token.
    """
    payload = {
        "sub": user_id,
        "email": email,
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(hours=config.jwt.expiry_hours),
    }
    
    return jwt.encode(payload, config.jwt.secret, algorithm=config.jwt.algorithm)


def decode_token(token: str) -> dict[str, Any] | None:
    """
    Decode and verify JWT token.
    
    Args:
        token: JWT token string.
        
    Returns:
        Token payload or None if invalid.
    """
    try:
        payload = jwt.decode(
            token,
            config.jwt.secret,
            algorithms=[config.jwt.algorithm],
        )
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("token_expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning("token_invalid", error=str(e))
        return None


def require_auth(f: Callable) -> Callable:
    """
    Decorator to require JWT authentication.
    
    Sets g.current_user with user data.
    """
    @wraps(f)
    def decorated(*args: Any, **kwargs: Any) -> Any:
        auth_header = request.headers.get("Authorization")
        
        if not auth_header:
            return jsonify({"error": "Missing authorization header"}), 401
        
        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return jsonify({"error": "Invalid authorization format"}), 401
        
        token = parts[1]
        payload = decode_token(token)
        
        if not payload:
            return jsonify({"error": "Invalid or expired token"}), 401
        
        # Get user from database
        user = execute_one(
            "SELECT id, email, username FROM users WHERE id = %s AND is_active = TRUE",
            (payload["sub"],)
        )
        
        if not user:
            return jsonify({"error": "User not found"}), 401
        
        g.current_user = user
        return f(*args, **kwargs)
    
    return decorated


def signup_user(email: str, username: str, password: str) -> dict[str, Any] | None:
    """
    Register a new user.
    
    Args:
        email: User email.
        username: Username.
        password: Plain text password.
        
    Returns:
        Created user dict or None if exists.
    """
    # Check if user exists
    existing = execute_one(
        "SELECT id FROM users WHERE email = %s OR username = %s",
        (email, username)
    )
    
    if existing:
        return None
    
    password_hash = hash_password(password)
    
    user = execute_insert(
        """
        INSERT INTO users (email, username, password_hash)
        VALUES (%s, %s, %s)
        RETURNING id, email, username
        """,
        (email, username, password_hash)
    )
    
    return user


def login_user(identifier: str, password: str) -> tuple[dict[str, Any], str] | None:
    """
    Authenticate user and return token.
    
    Args:
        identifier: User email OR username.
        password: Plain text password.
        
    Returns:
        Tuple of (user dict, token) or None if invalid.
    """
    # Try to find user by email or username
    user = execute_one(
        """SELECT id, email, username, password_hash FROM users 
           WHERE (email = %s OR username = %s) AND is_active = TRUE""",
        (identifier, identifier)
    )
    
    if not user:
        return None
    
    if not verify_password(password, user["password_hash"]):
        return None
    
    token = create_token(str(user["id"]), user["email"])
    
    return {
        "id": str(user["id"]),
        "email": user["email"],
        "username": user["username"],
    }, token
