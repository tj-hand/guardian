"""
Guardian Layer 1 Backend Exports

This module provides the Layer 1 interface for the Guardian authentication service.
It exports the necessary components for Manifast to mount Guardian as a plugin.
"""

# Router exports for Manifast to mount
from app.api.routes.auth import router as auth_router
from app.api.routes.health import router as health_router

# Model exports for Manifast's Alembic
from app.models import User, Token

# Database utilities
from app.core.database import get_db, init_db as init_database, Base


def setup_guardian(app, prefix="/api/auth"):
    """
    Mount Guardian authentication routes on the FastAPI app.

    This is a convenience function for integrating Guardian into a Manifast application.

    Args:
        app: FastAPI application instance
        prefix: URL prefix for auth routes (default: "/api/auth")

    Example:
        from guardian.app import setup_guardian
        from fastapi import FastAPI

        app = FastAPI()
        setup_guardian(app, prefix="/api/auth")
    """
    app.include_router(auth_router, prefix=prefix, tags=["auth"])
    app.include_router(health_router, prefix="/health", tags=["health"])


__all__ = [
    # Routers
    "auth_router",
    "health_router",

    # Models
    "User",
    "Token",

    # Database
    "get_db",
    "init_database",
    "Base",

    # Setup
    "setup_guardian",
]
