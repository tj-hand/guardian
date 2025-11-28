"""
Pytest configuration and fixtures.

This module provides shared fixtures for testing the FastAPI application.
"""

import asyncio
from typing import AsyncGenerator, Generator
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.main import app
from app.core.database import Base, get_db
from app.core.config import get_settings

# Test database URL (use separate database for tests)
settings = get_settings()
TEST_DATABASE_URL = settings.database_url.replace(
    settings.postgres_db,
    f"{settings.postgres_db}_test"
)

# Create test engine
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    future=True,
)

# Create test session factory
TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """
    Create event loop for async tests.

    Yields:
        asyncio.AbstractEventLoop: Event loop for test session
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Create database session for each test.

    Creates all tables before test and drops them after.

    Yields:
        AsyncSession: Database session for testing
    """
    # Create tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session
    async with TestSessionLocal() as session:
        yield session
        await session.rollback()

    # Drop tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Create test client with database session override.

    Args:
        db_session: Database session fixture

    Yields:
        AsyncClient: HTTP client for testing FastAPI endpoints
    """

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        """Override database dependency with test session."""
        yield db_session

    # Override dependency
    app.dependency_overrides[get_db] = override_get_db

    # Create client
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

    # Clear overrides
    app.dependency_overrides.clear()


@pytest.fixture
def async_client(client):
    """
    Alias for client fixture to match test expectations.

    Args:
        client: The AsyncClient fixture

    Returns:
        AsyncClient: HTTP client for testing
    """
    return client


@pytest.fixture
async def sample_user(db_session: AsyncSession):
    """
    Create a sample user for testing.

    Args:
        db_session: Database session

    Returns:
        User: Sample user object
    """
    from app.models.user import User

    user = User(
        email="test@example.com",
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    return user


@pytest.fixture
def auth_headers(sample_user):
    """
    Create authentication headers with valid JWT token.

    Args:
        sample_user: Sample user fixture

    Returns:
        dict: Headers with Authorization Bearer token
    """
    from app.services import jwt_service

    token = jwt_service.create_access_token(sample_user)
    return {"Authorization": f"Bearer {token}"}
