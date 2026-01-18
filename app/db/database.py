"""
Read-only database connection with async SQLAlchemy.
Uses connection pooling with limited connections for MVP.
Lazy initialization to allow app to load without valid DB URL.
Updated to use separate DB config parameters to handle special characters in password.
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, AsyncEngine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from sqlalchemy.engine import URL
from typing import AsyncGenerator, Optional
from contextlib import asynccontextmanager
import logging
import os

from app.config import get_settings

logger = logging.getLogger(__name__)

# Lazy-initialized engine
_engine: Optional[AsyncEngine] = None
_session_factory = None


def build_database_url() -> URL:
    """Build database URL from separate config parameters to handle special chars in password."""
    settings = get_settings()
    
    # Try separate DB2 params first (handles special chars better)
    db_host = settings.DB2_HOST
    db_port = settings.DB2_PORT
    db_user = settings.DB2_USERNAME
    db_password = settings.DB2_PASSWORD
    db_database = settings.DB2_DATABASE
    
    if all([db_host, db_user, db_password, db_database]):
        logger.info(f"Using separate DB2 config: {db_host}:{db_port}/{db_database}")
        return URL.create(
            drivername="mysql+aiomysql",
            username=db_user,
            password=db_password,
            host=db_host,
            port=db_port,
            database=db_database
        )
    
    # Fall back to DATABASE_URL
    logger.info("Falling back to DATABASE_URL")
    return settings.DATABASE_URL


def get_engine() -> AsyncEngine:
    """Get or create the database engine (lazy initialization)."""
    global _engine
    if _engine is None:
        settings = get_settings()
        db_url = build_database_url()
        logger.info(f"Creating database engine for host: {os.environ.get('DB_HOST', 'from URL')}")
        _engine = create_async_engine(
            db_url,
            pool_size=settings.DB_POOL_SIZE,
            pool_recycle=settings.DB_POOL_RECYCLE,
            pool_pre_ping=True,
            echo=False,
        )
    return _engine


def get_session_factory():
    """Get or create the session factory."""
    global _session_factory
    if _session_factory is None:
        _session_factory = sessionmaker(
            get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return _session_factory


@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Get an async database session."""
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
        finally:
            await session.close()


async def execute_readonly_query(query: str, params: dict) -> list[dict]:
    """
    Execute a read-only SQL query with parameter binding.
    Returns list of row dictionaries.
    """
    async with get_db_session() as session:
        result = await session.execute(text(query), params)
        rows = result.fetchall()
        columns = result.keys()
        return [dict(zip(columns, row)) for row in rows]


async def validate_mobile_exists(mobile: str) -> bool:
    """
    Check if mobile number exists in query_masters table.
    Uses snake_case table name matching real database schema.
    """
    # Extract last 10 digits for robust matching
    mobile_plain = mobile[-10:] if len(mobile) >= 10 else mobile
    
    query = """
        SELECT EXISTS(
            SELECT 1 FROM query_masters WHERE user_mobile LIKE :m_wild
        ) as exists_flag
    """
    async with get_db_session() as session:
        result = await session.execute(text(query), {"m_wild": f"%{mobile_plain}"})
        row = result.fetchone()
        return bool(row and row[0])
