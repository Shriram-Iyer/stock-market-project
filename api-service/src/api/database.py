"""
Database connection and operations module.
"""

from contextlib import contextmanager
from typing import Any, Generator

import psycopg2
from psycopg2.extras import RealDictCursor
import structlog

from .config import config

logger = structlog.get_logger(__name__)


@contextmanager
def get_connection() -> Generator[psycopg2.extensions.connection, None, None]:
    """
    Get database connection as context manager.
    
    Yields:
        PostgreSQL connection.
    """
    conn = psycopg2.connect(
        host=config.database.host,
        port=config.database.port,
        user=config.database.user,
        password=config.database.password,
        database=config.database.database,
    )
    try:
        yield conn
    finally:
        conn.close()


def execute_query(
    query: str,
    params: tuple | None = None,
    fetch: bool = True,
) -> list[dict[str, Any]]:
    """
    Execute a query and return results.
    
    Args:
        query: SQL query string.
        params: Query parameters.
        fetch: Whether to fetch results.
        
    Returns:
        List of result dictionaries.
    """
    with get_connection() as conn:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(query, params)
        
        if fetch:
            results = cursor.fetchall()
            return [dict(row) for row in results]
        else:
            conn.commit()
            return []


def execute_one(
    query: str,
    params: tuple | None = None,
) -> dict[str, Any] | None:
    """
    Execute query and return single result.
    
    Args:
        query: SQL query string.
        params: Query parameters.
        
    Returns:
        Result dictionary or None.
    """
    with get_connection() as conn:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(query, params)
        result = cursor.fetchone()
        return dict(result) if result else None


def execute_insert(
    query: str,
    params: tuple,
    returning: bool = True,
) -> dict[str, Any] | None:
    """
    Execute insert query.
    
    Args:
        query: SQL insert query.
        params: Query parameters.
        returning: Whether query has RETURNING clause.
        
    Returns:
        Inserted row or None.
    """
    with get_connection() as conn:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(query, params)
        conn.commit()
        
        if returning:
            result = cursor.fetchone()
            return dict(result) if result else None
        return None


def health_check() -> bool:
    """Check database connectivity."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            return True
    except Exception as e:
        logger.error("db_health_check_failed", error=str(e))
        return False
