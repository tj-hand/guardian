# ========================================
# Guardian Backend Dockerfile
# ========================================
# Multi-stage build for Python 3.11 FastAPI application
# Layer 1 module for Manifast integration
# Optimized for production with development support

# ========================================
# Stage 1: Base Image
# ========================================
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# ========================================
# Stage 2: Dependencies
# ========================================
FROM base as dependencies

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# ========================================
# Stage 3: Layer Target (for Manifast)
# ========================================
# This stage exports just the Guardian authentication module
# Layer 0 containers (Manifast) can use this as a base or copy from it
FROM dependencies as layer

# Copy application code
COPY . .

# Set module metadata
ENV GUARDIAN_MODULE_NAME="guardian-auth" \
    GUARDIAN_MODULE_VERSION="1.0.0" \
    GUARDIAN_MODULE_TYPE="authentication"

# Expose port (for layer testing)
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command for layer testing
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

# ========================================
# Stage 4: Development
# ========================================
FROM dependencies as development

# Install development dependencies
RUN pip install --no-cache-dir \
    pytest \
    pytest-asyncio \
    pytest-cov \
    httpx \
    black \
    isort \
    flake8 \
    mypy

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run with uvicorn hot-reload
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# ========================================
# Stage 5: Production
# ========================================
FROM dependencies as production

# Create non-root user for security
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

# Copy application code
COPY --chown=appuser:appuser . .

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run with uvicorn (production settings)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]

# ========================================
# Build Instructions
# ========================================
#
# Layer target (for Manifast integration):
#   docker build --target layer -t guardian-backend:layer .
#
# Development build:
#   docker build --target development -t guardian-backend:dev .
#
# Production build:
#   docker build --target production -t guardian-backend:prod .
#
# Run development container:
#   docker run -p 8000:8000 -v $(pwd):/app guardian-backend:dev
#
# Run production container:
#   docker run -p 8000:8000 guardian-backend:prod
#
# ========================================
