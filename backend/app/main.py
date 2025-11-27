"""
Guardian - Passwordless Authentication Service
FastAPI Application Entry Point

Guardian provides passwordless authentication via 6-digit email tokens,
built on the Evoke → Bolt → Manifast architecture.
"""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings
from app.core.database import init_database, close_database
from app.api.routes import auth_router, health_router

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan handler.
    Manages startup and shutdown events.
    """
    # Startup
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Debug mode: {settings.debug}")

    try:
        await init_database()
        logger.info("Database connection established")
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        logger.warning("Starting without database connection")

    yield

    # Shutdown
    logger.info(f"Shutting down {settings.app_name}")
    await close_database()
    logger.info("Shutdown complete")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="""
## Guardian - Passwordless Authentication Service

Guardian enables users to authenticate via secure, time-limited 6-digit tokens
delivered by email. No passwords required.

### Authentication Flow

1. User enters email → Guardian generates 6-digit token
2. Token sent via email
3. User enters token → Guardian validates
4. On success, JWT session created

### API Endpoints

- `POST /api/auth/request-token` - Request 6-digit token
- `POST /api/auth/validate-token` - Validate token and get JWT
- `GET /api/auth/me` - Get current user info
- `POST /api/auth/refresh` - Refresh JWT token
- `POST /api/auth/logout` - Logout user

### Architecture

Built on the Evoke → Bolt → Manifast stack:
- Frontend (Evoke): Vue 3 login UI
- Gateway (Bolt): Request routing
- Backend (Manifast): This service
    """,
    version=settings.app_version,
    docs_url=f"{settings.api_prefix}/docs" if settings.debug else None,
    redoc_url=f"{settings.api_prefix}/redoc" if settings.debug else None,
    openapi_url=f"{settings.api_prefix}/openapi.json" if settings.debug else None,
    lifespan=lifespan,
    openapi_tags=[
        {
            "name": "Health",
            "description": "Health check endpoints for monitoring"
        },
        {
            "name": "Authentication",
            "description": "Passwordless 6-digit token authentication"
        }
    ]
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_methods_list,
    allow_headers=settings.cors_headers_list,
)


# Exception handlers

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError
) -> JSONResponse:
    """Handle Pydantic validation errors."""
    logger.warning(f"Validation error on {request.url.path}: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": exc.errors(),
            "message": "Request validation failed"
        }
    )


@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(
    request: Request,
    exc: SQLAlchemyError
) -> JSONResponse:
    """Handle database errors."""
    logger.error(f"Database error on {request.url.path}: {exc}")
    detail = str(exc) if settings.debug else "Database error occurred"
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": detail, "message": "Database error"}
    )


@app.exception_handler(Exception)
async def general_exception_handler(
    request: Request,
    exc: Exception
) -> JSONResponse:
    """Handle uncaught exceptions."""
    logger.error(f"Unhandled error on {request.url.path}: {exc}", exc_info=True)
    detail = str(exc) if settings.debug else "An unexpected error occurred"
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": detail, "message": "Internal server error"}
    )


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests."""
    logger.info(f"{request.method} {request.url.path}")
    response = await call_next(request)
    logger.info(f"{request.method} {request.url.path} -> {response.status_code}")
    return response


# Include routers
app.include_router(health_router)
app.include_router(auth_router, prefix=settings.api_prefix)


# Root endpoint
@app.get("/", tags=["Health"])
async def root() -> dict:
    """Root endpoint with API information."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "description": "Passwordless authentication via 6-digit email tokens",
        "environment": settings.environment,
        "docs": f"{settings.api_prefix}/docs" if settings.debug else None,
        "health": "/health"
    }


@app.get(f"{settings.api_prefix}/", tags=["Health"])
async def api_root() -> dict:
    """API root endpoint."""
    return {
        "service": "guardian",
        "version": settings.app_version,
        "status": "operational"
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.is_development,
        log_level="info"
    )
