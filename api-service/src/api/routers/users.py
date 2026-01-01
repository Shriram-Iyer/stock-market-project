"""
Users router - authentication endpoints.
"""

from flask import Blueprint, jsonify, request, g
import structlog

from ..auth import signup_user, login_user, require_auth

logger = structlog.get_logger(__name__)

users_bp = Blueprint("users", __name__, url_prefix="/api/auth")


@users_bp.route("/signup", methods=["POST"])
def signup():
    """
    Register a new user.
    
    Body:
        - email: User email
        - username: Username
        - password: Password (min 8 chars)
    """
    data = request.get_json()
    
    # Validate required fields
    required = ["email", "username", "password"]
    if not all(field in data for field in required):
        return jsonify({"error": f"Missing required fields: {required}"}), 400
    
    email = data["email"].lower().strip()
    username = data["username"].strip()
    password = data["password"]
    
    # Validate email format
    if "@" not in email or "." not in email:
        return jsonify({"error": "Invalid email format"}), 400
    
    # Validate username
    if len(username) < 3:
        return jsonify({"error": "Username must be at least 3 characters"}), 400
    
    # Validate password
    if len(password) < 8:
        return jsonify({"error": "Password must be at least 8 characters"}), 400
    
    user = signup_user(email, username, password)
    
    if not user:
        return jsonify({"error": "Email or username already exists"}), 409
    
    user["id"] = str(user["id"])
    
    logger.info("user_registered", email=email, username=username)
    
    return jsonify({
        "message": "User registered successfully",
        "user": user,
    }), 201


@users_bp.route("/login", methods=["POST"])
def login():
    """
    Authenticate user and return JWT token.
    
    Body:
        - email/identifier: User email OR username
        - password: Password
    """
    data = request.get_json()
    
    # Accept either 'email' or 'identifier' field for backwards compatibility
    identifier = data.get("identifier") or data.get("email")
    
    if not identifier or not data.get("password"):
        return jsonify({"error": "Email/username and password required"}), 400
    
    identifier = identifier.strip()
    password = data["password"]
    
    result = login_user(identifier, password)
    
    if not result:
        logger.warning("login_failed", identifier=identifier)
        return jsonify({"error": "Invalid email/username or password"}), 401
    
    user, token = result
    
    logger.info("user_logged_in", identifier=identifier)
    
    return jsonify({
        "message": "Login successful",
        "user": user,
        "token": token,
    })


@users_bp.route("/me", methods=["GET"])
@require_auth
def get_current_user():
    """Get current authenticated user."""
    return jsonify({
        "id": str(g.current_user["id"]),
        "email": g.current_user["email"],
        "username": g.current_user["username"],
    })


@users_bp.route("/refresh", methods=["POST"])
@require_auth
def refresh_token():
    """Refresh JWT token."""
    from ..auth import create_token
    
    user = g.current_user
    token = create_token(str(user["id"]), user["email"])
    
    return jsonify({
        "token": token,
    })
