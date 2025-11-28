"""
Pytest configuration and fixtures.

This module provides shared fixtures for testing the FastAPI application.
"""

from typing import AsyncGenerator
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

from app.main import app
from app.core.database import Base, get_db
from app.core.config import get_settings

# Test database URL
# In CI/testing environments with DATABASE_URL set, use it directly (CI provides a test database)
# In development, append _test suffix to avoid affecting dev data
settings = get_settings()
if settings.database_url_override:
    # CI provides DATABASE_URL pointing to a dedicated test database
    TEST_DATABASE_URL = settings.database_url
else:
    # Development: use separate _test database
    TEST_DATABASE_URL = settings.database_url.replace(
        settings.postgres_db,
        f"{settings.postgres_db}_test"
    )

# Create test engine with NullPool to avoid connection state issues
# NullPool creates a new connection for each use and closes it immediately after
# This prevents "another operation is in progress" errors in asyncpg
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    future=True,
    poolclass=NullPool,
)

# Create test session factory
TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)

# Note: event_loop fixture removed - pytest-asyncio with asyncio_mode=auto handles this automatically


@pytest_asyncio.fixture(scope="function", loop_scope="function")
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
        try:
            yield session
        finally:
            # Proper cleanup to avoid "another operation is in progress" errors
            await session.rollback()
            await session.close()

    # Drop tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    # Dispose engine to ensure all connections are closed
    await test_engine.dispose()


@pytest_asyncio.fixture(scope="function", loop_scope="function")
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

    try:
        # Create client using ASGITransport for httpx 0.28+ compatibility
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac
    finally:
        # Always clear overrides, even if test fails
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


@pytest_asyncio.fixture(loop_scope="function")
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
