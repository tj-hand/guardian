# Guardian Backend - Layer 1 Module
# Builds a FastAPI module to be mounted into Manifast (Layer 0)

# =============================================================================
# Development Stage
# =============================================================================
FROM python:3.11-slim as development

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port for standalone dev
EXPOSE 8000

# Development command with hot reload
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# =============================================================================
# Build Stage - Package Build
# =============================================================================
FROM python:3.11-slim as build

WORKDIR /app

# Install build tools
RUN pip install --no-cache-dir build

# Copy project files
COPY pyproject.toml .
COPY requirements.txt .
COPY app/ ./app/
COPY alembic/ ./alembic/
COPY alembic.ini .

# Build the package
RUN python -m build --wheel

# =============================================================================
# Layer Output Stage
# Produces the built module for integration with Manifast
# =============================================================================
FROM python:3.11-slim as layer

WORKDIR /guardian

# Copy built wheel package
COPY --from=build /app/dist/*.whl ./dist/

# Copy source code for installation in Manifast
COPY --from=build /app/app ./app
COPY --from=build /app/alembic ./alembic
COPY --from=build /app/alembic.ini .
COPY --from=build /app/pyproject.toml .
COPY --from=build /app/requirements.txt .

# Layer metadata
LABEL layer.name="guardian"
LABEL layer.level="1"
LABEL layer.type="backend"
LABEL layer.description="Passwordless authentication module"

# This image is meant to be used as a source for COPY --from in Manifast's Dockerfile
# Example usage in Manifast Dockerfile:
#   FROM guardian-backend:latest as guardian
#   COPY --from=guardian /guardian /app/layers/guardian
#   RUN pip install /app/layers/guardian/dist/*.whl

# =============================================================================
# Standalone Production Stage (for testing/standalone deployment)
# =============================================================================
FROM python:3.11-slim as production

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 guardian

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set ownership
RUN chown -R guardian:guardian /app

# Switch to non-root user
USER guardian

# Expose port
EXPOSE 8000

# Production command
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
