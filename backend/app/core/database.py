"""
Database configuration and session management.

This module provides SQLAlchemy database configuration, connection pooling,
and session management for the Email Token Authentication system.
"""

import os
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

# Database connection settings from environment variables
# Check for DATABASE_URL first (used in CI), then fall back to individual components
_database_url_env = os.getenv("DATABASE_URL")

if _database_url_env:
    # Use DATABASE_URL directly if provided (e.g., in CI)
    DATABASE_URL = _database_url_env
else:
    # Construct from individual components (development/production)
    POSTGRES_USER = os.getenv("POSTGRES_USER", "authuser")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "authpass123")
    POSTGRES_HOST = os.getenv("POSTGRES_HOST", "database")
    POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
    POSTGRES_DB = os.getenv("POSTGRES_DB", "auth_db")

    DATABASE_URL = (
        f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}"
        f"@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    )

# Create async engine with connection pooling
# For production, adjust pool settings based on expected concurrent connections
engine = create_async_engine(
    DATABASE_URL,
    echo=os.getenv("APP_ENV") == "development",  # SQL logging in development
    future=True,
    pool_size=10,  # Maximum number of connections in the pool
    max_overflow=20,  # Maximum overflow connections beyond pool_size
    pool_pre_ping=True,  # Verify connections before using them
    pool_recycle=3600,  # Recycle connections after 1 hour
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


# Base class for all SQLAlchemy models
class Base(DeclarativeBase):
    """Base class for all database models."""

    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency function to provide database sessions.

    Yields:
        AsyncSession: Database session for request handling

    Usage:
        @app.get("/users")
        async def get_users(db: AsyncSession = Depends(get_db)):
            # Use db session here
            pass
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """
    Initialize database by creating all tables.

    Note: In production, use Alembic migrations instead.
    This is primarily for testing and development.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """
    Close all database connections.

    Call this during application shutdown.
    """
    await engine.dispose()
