"""
FastAPI application entry point.

This module initializes and configures the FastAPI application with:
- CORS middleware
- Exception handlers
- Route registration
- Startup/shutdown events
- Database initialization
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from app.api.routes import health
from app.core.config import get_settings
from app.core.database import close_db, engine

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Get settings
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """
    Application lifespan context manager.

    Handles startup and shutdown events:
    - Startup: Test database connection, log configuration
    - Shutdown: Close database connections, cleanup resources

    Args:
        app: FastAPI application instance

    Yields:
        None: Control during application runtime
    """
    # Startup
    logger.info(f"Starting {settings.app_name}...")
    logger.info(f"Environment: {settings.app_env}")
    logger.info(f"API Version 1 Prefix: {settings.api_v1_prefix}")

    # Test database connection
    try:
        async with engine.connect():
            logger.info("Database connection successful")
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        logger.warning("Application starting without database connection")

    logger.info(f"{settings.app_name} started successfully")

    yield  # Application runs

    # Shutdown
    logger.info("Shutting down application...")

    try:
        await close_db()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Error closing database connections: {e}")

    logger.info("Application shutdown complete")


# Initialize FastAPI application
app = FastAPI(
    title=settings.app_name,
    description=(
        "Passwordless authentication system using 6-digit numeric email tokens. "
        "Users receive a secure 6-digit code via email to access the system."
    ),
    version="1.0.0",
    docs_url="/docs" if settings.is_development else None,
    redoc_url="/redoc" if settings.is_development else None,
    lifespan=lifespan,
    openapi_tags=[
        {"name": "Health", "description": "Health check and monitoring endpoints"},
        {
            "name": "Authentication",
            "description": "Email token authentication endpoints (Sprint 2)",
        },
    ],
)


# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,  # Cache preflight requests for 1 hour
)


# Exception Handlers


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """
    Handle Pydantic validation errors.

    Returns user-friendly error messages for invalid request data.

    Args:
        request: The incoming request
        exc: The validation exception

    Returns:
        JSONResponse: Formatted error response
    """
    logger.warning(f"Validation error on {request.url.path}: {exc.errors()}")

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": exc.errors(),
            "body": exc.body,
            "message": "Request validation failed. Please check your input.",
        },
    )


@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    """
    Handle SQLAlchemy database errors.

    Returns generic error message to avoid leaking database details.

    Args:
        request: The incoming request
        exc: The SQLAlchemy exception

    Returns:
        JSONResponse: Generic error response
    """
    logger.error(f"Database error on {request.url.path}: {str(exc)}")

    # Don't expose database details in production
    detail = str(exc) if settings.is_development else "A database error occurred"

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": detail, "message": "An error occurred while processing your request."},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle all uncaught exceptions.

    Logs error details and returns generic error message to client.

    Args:
        request: The incoming request
        exc: The exception

    Returns:
        JSONResponse: Generic error response
    """
    logger.error(
        f"Unhandled exception on {request.url.path}: {type(exc).__name__} - {str(exc)}",
        exc_info=True,
    )

    # Don't expose internal details in production
    detail = str(exc) if settings.is_development else "An unexpected error occurred"

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": detail,
            "message": "An unexpected error occurred. Please try again later.",
        },
    )


# Middleware for request logging


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    Log all incoming requests.

    Args:
        request: The incoming request
        call_next: The next middleware or route handler

    Returns:
        Response: The response from the next handler
    """
    logger.info(f"{request.method} {request.url.path}")

    response = await call_next(request)

    logger.info(f"{request.method} {request.url.path} - Status: {response.status_code}")

    return response


# Include routers

# Health check routes (no prefix - accessible at root level)
app.include_router(health.router)

# Authentication routes (Sprint 2)
from app.api.routes import auth  # noqa: E402

app.include_router(auth.router, prefix=settings.api_v1_prefix)


# Root endpoint


@app.get(
    "/", tags=["Root"], summary="Root Endpoint", description="Welcome message and API information"
)
async def root() -> dict:
    """
    Root endpoint providing API information.

    Returns:
        dict: Welcome message and API details

    Usage:
        GET /
    """
    return {
        "message": f"Welcome to {settings.app_name}",
        "version": "1.0.0",
        "environment": settings.app_env,
        "docs": "/docs" if settings.is_development else None,
        "health": "/health",
    }


if __name__ == "__main__":
    import uvicorn

    # Run with uvicorn for development
    # In production, use: uvicorn app.main:app --host 0.0.0.0 --port 8000
    uvicorn.run(
        "app.main:app", host="0.0.0.0", port=8000, reload=settings.is_development, log_level="info"
    )
