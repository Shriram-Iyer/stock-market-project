"""
Configuration module for ETL service.

Loads environment variables and provides typed configuration.
"""

import os
from dataclasses import dataclass
from typing import Optional

from dotenv import load_dotenv

# Load environment variables
load_dotenv()


@dataclass(frozen=True)
class DatabaseConfig:
    """Database connection configuration."""
    
    host: str
    port: int
    user: str
    password: str
    database: str
    
    @property
    def connection_string(self) -> str:
        """Generate PostgreSQL connection string."""
        return (
            f"postgresql://{self.user}:{self.password}"
            f"@{self.host}:{self.port}/{self.database}"
        )


@dataclass(frozen=True)
class HuggingFaceConfig:
    """Hugging Face API configuration."""
    
    token: str
    model_name: str = "ProsusAI/finbert"


@dataclass(frozen=True)
class ETLConfig:
    """Main ETL configuration."""
    
    database: DatabaseConfig
    huggingface: HuggingFaceConfig
    lookback_days: int = 365
    schedule_interval: str = "daily"
    batch_size: int = 50
    retry_attempts: int = 3
    retry_delay: float = 1.0


def load_config() -> ETLConfig:
    """
    Load configuration from environment variables.
    
    Returns:
        ETLConfig: Fully configured ETL settings.
        
    Raises:
        ValueError: If required environment variables are missing.
    """
    # Validate required variables
    required_vars = [
        "POSTGRES_HOST",
        "POSTGRES_USER",
        "POSTGRES_PASSWORD",
        "POSTGRES_DB",
    ]
    
    missing = [var for var in required_vars if not os.getenv(var)]
    if missing:
        raise ValueError(f"Missing required environment variables: {missing}")
    
    db_config = DatabaseConfig(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        user=os.getenv("POSTGRES_USER", ""),
        password=os.getenv("POSTGRES_PASSWORD", ""),
        database=os.getenv("POSTGRES_DB", ""),
    )
    
    hf_config = HuggingFaceConfig(
        token=os.getenv("HF_TOKEN", ""),
        model_name=os.getenv("HF_MODEL", "ProsusAI/finbert"),
    )
    
    return ETLConfig(
        database=db_config,
        huggingface=hf_config,
        lookback_days=int(os.getenv("LOOKBACK_DAYS", "365")),
        batch_size=int(os.getenv("BATCH_SIZE", "50")),
        retry_attempts=int(os.getenv("RETRY_ATTEMPTS", "3")),
        retry_delay=float(os.getenv("RETRY_DELAY", "1.0")),
    )


# Global config instance
config: Optional[ETLConfig] = None


def get_config() -> ETLConfig:
    """Get or create the global configuration instance."""
    global config
    if config is None:
        config = load_config()
    return config
