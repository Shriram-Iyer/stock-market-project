"""
Custom exceptions for ETL service.

Provides specific exception types for better error handling and debugging.
"""


class ETLException(Exception):
    """Base exception for all ETL errors."""
    
    def __init__(self, message: str, details: dict | None = None) -> None:
        """
        Initialize ETL exception.
        
        Args:
            message: Human-readable error message.
            details: Additional context for debugging.
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}


class DataFetchError(ETLException):
    """Raised when data fetching from external APIs fails."""
    
    def __init__(
        self,
        message: str,
        ticker: str | None = None,
        source: str = "yfinance",
    ) -> None:
        """Initialize data fetch error with ticker context."""
        super().__init__(
            message,
            details={"ticker": ticker, "source": source},
        )
        self.ticker = ticker
        self.source = source


class DatabaseError(ETLException):
    """Raised when database operations fail."""
    
    def __init__(
        self,
        message: str,
        operation: str | None = None,
        table: str | None = None,
    ) -> None:
        """Initialize database error with operation context."""
        super().__init__(
            message,
            details={"operation": operation, "table": table},
        )
        self.operation = operation
        self.table = table


class ModelError(ETLException):
    """Raised when ML model training or prediction fails."""
    
    def __init__(
        self,
        message: str,
        model_type: str | None = None,
        ticker: str | None = None,
    ) -> None:
        """Initialize model error with model context."""
        super().__init__(
            message,
            details={"model_type": model_type, "ticker": ticker},
        )
        self.model_type = model_type
        self.ticker = ticker


class ConfigurationError(ETLException):
    """Raised when configuration is invalid or missing."""
    
    pass


class ValidationError(ETLException):
    """Raised when data validation fails."""
    
    def __init__(
        self,
        message: str,
        field: str | None = None,
        value: str | None = None,
    ) -> None:
        """Initialize validation error with field context."""
        super().__init__(
            message,
            details={"field": field, "value": value},
        )
        self.field = field
        self.value = value
