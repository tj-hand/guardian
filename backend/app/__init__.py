"""
Guardian Backend - Layer 1 Authentication Module

This module exports all Guardian authentication components to be
mounted by the Manifast backend container (Layer 0).

Usage in Manifast:
    from guardian.app import (
        guardian_router,
        guardian_lifespan,
        layer_info,
    )

    # Mount Guardian routes
    app.include_router(guardian_router, prefix="/api")

    # Or use the setup function
    from guardian.app import setup_guardian
    setup_guardian(app)
"""

from typing import Any
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI

# Layer metadata
layer_info = {
    "name": "guardian",
    "version": "1.0.0",
    "layer": 1,
    "description": "Passwordless authentication with 6-digit email tokens",
    "routes_prefix": "/api/auth",
}

# Routers
from app.api.routes.auth import router as auth_router
from app.api.routes.health import router as health_router

# Combined router for convenience
from fastapi import APIRouter

guardian_router = APIRouter()
guardian_router.include_router(auth_router)

# Models (for Manifast to register with Alembic)
from app.models.user import User
from app.models.token import AuthToken

# Schemas (for type exports)
from app.schemas.auth import (
    TokenRequest,
    TokenRequestResponse,
    TokenValidation,
    TokenValidationResponse,
    UserResponse,
    LogoutResponse,
)

# Database utilities
from app.core.database import (
    Base,
    get_db,
    init_database,
    close_database,
    get_engine,
)

# Configuration
from app.core.config import settings, Settings

# Services (if Manifast needs to extend)
from app.services.jwt_service import create_access_token, decode_access_token
from app.services.token_service import generate_6_digit_token

# Dependencies
from app.api.dependencies import get_current_user

logger = logging.getLogger(__name__)


@asynccontextmanager
async def guardian_lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Guardian lifecycle handler for database connections.

    Use this in Manifast's lifespan if you want Guardian to manage
    its own database connection, or handle it at Manifast level.
    """
    logger.info(f"Guardian Layer 1 starting (v{layer_info['version']})")

    try:
        await init_database()
        logger.info("Guardian database connection established")
    except Exception as e:
        logger.error(f"Guardian database connection failed: {e}")
        logger.warning("Guardian starting without database")

    yield

    logger.info("Guardian Layer 1 shutting down")
    await close_database()


def setup_guardian(
    app: FastAPI,
    prefix: str = "/api",
    include_health: bool = False,
) -> None:
    """
    Setup Guardian authentication routes on a FastAPI app.

    This is a convenience function for Manifast to quickly mount
    Guardian authentication.

    Args:
        app: The FastAPI application (Manifast)
        prefix: API prefix for auth routes (default: /api)
        include_health: Whether to include Guardian's health endpoint
    """
    logger.info(f"Setting up Guardian authentication at {prefix}/auth")

    # Mount auth router
    app.include_router(auth_router, prefix=prefix)

    if include_health:
        app.include_router(health_router)

    logger.info("Guardian authentication routes registered")


def get_guardian_models() -> list:
    """
    Returns all SQLAlchemy models for Guardian.
    Use this for Alembic migration registration in Manifast.
    """
    return [User, AuthToken]


# Export all public API
__all__ = [
    # Layer metadata
    "layer_info",
    # Routers
    "guardian_router",
    "auth_router",
    "health_router",
    # Setup
    "setup_guardian",
    "guardian_lifespan",
    # Models
    "User",
    "AuthToken",
    "Base",
    "get_guardian_models",
    # Schemas
    "TokenRequest",
    "TokenRequestResponse",
    "TokenValidation",
    "TokenValidationResponse",
    "UserResponse",
    "LogoutResponse",
    # Database
    "get_db",
    "init_database",
    "close_database",
    "get_engine",
    # Config
    "settings",
    "Settings",
    # Services
    "create_access_token",
    "decode_access_token",
    "generate_6_digit_token",
    # Dependencies
    "get_current_user",
]
