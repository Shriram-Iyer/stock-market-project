"""
API Configuration module.
"""

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class DatabaseConfig:
    """Database configuration."""
    
    host: str
    port: int
    user: str
    password: str
    database: str


@dataclass(frozen=True)
class JWTConfig:
    """JWT configuration."""
    
    secret: str
    algorithm: str = "HS256"
    expiry_hours: int = 24


@dataclass(frozen=True)
class APIConfig:
    """Main API configuration."""
    
    database: DatabaseConfig
    jwt: JWTConfig
    debug: bool
    cors_origins: list[str]


def load_config() -> APIConfig:
    """Load configuration from environment."""
    db_config = DatabaseConfig(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        user=os.getenv("POSTGRES_USER", ""),
        password=os.getenv("POSTGRES_PASSWORD", ""),
        database=os.getenv("POSTGRES_DB", ""),
    )
    
    jwt_config = JWTConfig(
        secret=os.getenv("JWT_SECRET", "dev-secret-change-me"),
        expiry_hours=int(os.getenv("JWT_EXPIRY_HOURS", "24")),
    )
    
    cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
    
    return APIConfig(
        database=db_config,
        jwt=jwt_config,
        debug=os.getenv("FLASK_DEBUG", "0") == "1",
        cors_origins=cors_origins,
    )


config = load_config()
