# Guardian Integration Guide for mainline_test

This guide explains how to integrate Guardian (Layer 1) into the mainline_test repository, which combines Evoke, Bolt, and Manifast containers.

## Architecture Overview

```
mainline_test/
├── docker-compose.yml          # Orchestrates all containers
├── evoke/                      # Frontend container (Layer 0)
│   └── Dockerfile              # Pulls guardian-frontend layer
├── bolt/                       # Gateway container
│   └── nginx.conf              # Routes /api/* to Manifast
├── manifast/                   # Backend container (Layer 0)
│   └── Dockerfile              # Pulls guardian-backend layer
└── .env                        # Environment configuration
```

## Step 1: Build Guardian Layer Images

In the Guardian repository, build the layer images:

```bash
# Build frontend layer
docker build -t guardian-frontend:latest --target layer ./frontend

# Build backend layer
docker build -t guardian-backend:latest --target layer ./backend
```

Or use a registry:
```bash
docker build -t registry.example.com/guardian-frontend:1.0.0 --target layer ./frontend
docker build -t registry.example.com/guardian-backend:1.0.0 --target layer ./backend
docker push registry.example.com/guardian-frontend:1.0.0
docker push registry.example.com/guardian-backend:1.0.0
```

## Step 2: Integrate Frontend (Evoke + Guardian)

### 2.1 Update Evoke Dockerfile

```dockerfile
# evoke/Dockerfile

# Pull Guardian frontend layer
FROM guardian-frontend:latest as guardian-layer

# Base Evoke build
FROM node:20-alpine as build

WORKDIR /app

# Copy Evoke source
COPY package*.json ./
RUN npm ci

COPY . .

# Copy Guardian layer into Evoke
COPY --from=guardian-layer /guardian/dist ./node_modules/@guardian/frontend/dist
COPY --from=guardian-layer /guardian/package.json ./node_modules/@guardian/frontend/

# Build Evoke with Guardian
RUN npm run build

# Production
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
```

### 2.2 Update Evoke Main Entry Point

```typescript
// evoke/src/main.ts

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { createRouter, createWebHistory } from 'vue-router'
import App from './App.vue'

// Import Guardian Layer 1
import {
  guardianRoutes,
  guardianNavigationGuard,
  installGuardian,
  layerInfo as guardianInfo
} from '@guardian/frontend'

// Create app
const app = createApp(App)
const pinia = createPinia()

app.use(pinia)

// Install Guardian plugin (registers global components)
app.use(installGuardian)

console.log(`Loading ${guardianInfo.name} v${guardianInfo.version} (Layer ${guardianInfo.layer})`)

// Create router with Evoke base routes
const router = createRouter({
  history: createWebHistory(),
  routes: [
    // Evoke Layer 0 routes
    {
      path: '/',
      name: 'home',
      component: () => import('./views/Home.vue'),
    },
    // Add Guardian Layer 1 routes
    ...guardianRoutes,
  ],
})

// Register Guardian navigation guard
router.beforeEach(guardianNavigationGuard)

app.use(router)
app.mount('#app')
```

### 2.3 Update Evoke package.json

Add Guardian as a dependency (if using npm link or local path):

```json
{
  "dependencies": {
    "@guardian/frontend": "file:./node_modules/@guardian/frontend"
  }
}
```

Or if using a registry:
```json
{
  "dependencies": {
    "@guardian/frontend": "^1.0.0"
  }
}
```

## Step 3: Integrate Backend (Manifast + Guardian)

### 3.1 Update Manifast Dockerfile

```dockerfile
# manifast/Dockerfile

# Pull Guardian backend layer
FROM guardian-backend:latest as guardian-layer

# Base Manifast build
FROM python:3.11-slim as production

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 manifast

# Copy Manifast requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy Guardian layer and install
COPY --from=guardian-layer /guardian /app/layers/guardian
RUN pip install --no-cache-dir /app/layers/guardian/dist/*.whl

# Copy Manifast application
COPY . .

# Set ownership
RUN chown -R manifast:manifast /app

USER manifast

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

### 3.2 Update Manifast Main Entry Point

```python
# manifast/app/main.py

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings

# Import Guardian Layer 1
from guardian.app import (
    setup_guardian,
    guardian_lifespan,
    layer_info as guardian_info,
    get_guardian_models,
    init_database as guardian_init_db,
    close_database as guardian_close_db,
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Combined lifespan for Manifast and all layers."""
    logger.info(f"Starting Manifast (Layer 0)")

    # Initialize Guardian Layer 1
    logger.info(f"Loading {guardian_info['name']} v{guardian_info['version']} (Layer {guardian_info['layer']})")
    await guardian_init_db()

    yield

    # Shutdown
    logger.info("Shutting down...")
    await guardian_close_db()


# Create FastAPI application
app = FastAPI(
    title="Manifast + Guardian",
    description="Backend API with Guardian authentication",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup Guardian authentication routes
# This adds /api/auth/* endpoints
setup_guardian(app, prefix="/api", include_health=False)

# Manifast Layer 0 routes
@app.get("/")
async def root():
    return {
        "service": "manifast",
        "layers": [
            {"name": "manifast", "layer": 0},
            guardian_info,
        ]
    }

@app.get("/health")
async def health():
    return {"status": "healthy"}
```

### 3.3 Update Manifast Alembic Configuration

To include Guardian models in migrations:

```python
# manifast/alembic/env.py

from app.core.database import Base

# Import Guardian models for migrations
from guardian.app import get_guardian_models

# Register Guardian models with Base metadata
guardian_models = get_guardian_models()

target_metadata = Base.metadata
```

### 3.4 Update Manifast requirements.txt

```txt
# Manifast Layer 0 dependencies
fastapi>=0.109.0,<1.0.0
uvicorn[standard]>=0.27.0,<1.0.0
sqlalchemy>=2.0.0,<3.0.0
asyncpg>=0.29.0,<1.0.0
alembic>=1.13.0,<2.0.0
pydantic>=2.5.0,<3.0.0
pydantic-settings>=2.1.0,<3.0.0

# Guardian Layer 1 will be installed from wheel in Dockerfile
# guardian-backend  # installed via: pip install /app/layers/guardian/dist/*.whl
```

## Step 4: Configure Bolt Gateway

### 4.1 Update Bolt nginx.conf

```nginx
# bolt/nginx.conf

upstream frontend {
    server evoke:80;
}

upstream backend {
    server manifast:8000;
}

server {
    listen 80;
    server_name _;

    # API routes to Manifast (includes Guardian /api/auth/*)
    location /api/ {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Health check
    location /health {
        proxy_pass http://backend;
    }

    # All other routes to Evoke frontend
    location / {
        proxy_pass http://frontend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Step 5: Docker Compose Configuration

### 5.1 mainline_test docker-compose.yml

```yaml
# mainline_test/docker-compose.yml

version: '3.8'

services:
  # PostgreSQL Database
  database:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: ${DB_USER:-guardian}
      POSTGRES_PASSWORD: ${DB_PASSWORD:-guardian_secret}
      POSTGRES_DB: ${DB_NAME:-guardian}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER:-guardian}"]
      interval: 5s
      timeout: 5s
      retries: 5

  # Frontend: Evoke (Layer 0) + Guardian (Layer 1)
  evoke:
    build:
      context: ./evoke
      dockerfile: Dockerfile
    environment:
      - VITE_API_URL=/api
    depends_on:
      - bolt

  # Gateway: Bolt
  bolt:
    build:
      context: ./bolt
      dockerfile: Dockerfile
    ports:
      - "80:80"
    depends_on:
      - manifast

  # Backend: Manifast (Layer 0) + Guardian (Layer 1)
  manifast:
    build:
      context: ./manifast
      dockerfile: Dockerfile
    environment:
      - DATABASE_URL=postgresql+asyncpg://${DB_USER:-guardian}:${DB_PASSWORD:-guardian_secret}@database:5432/${DB_NAME:-guardian}
      - JWT_SECRET=${JWT_SECRET:-your-super-secret-key-change-in-production}
      - EMAIL_SERVICE_URL=${EMAIL_SERVICE_URL:-http://email-service:8080}
      - DEBUG=${DEBUG:-false}
    depends_on:
      database:
        condition: service_healthy

volumes:
  postgres_data:
```

### 5.2 Environment Variables (.env)

```bash
# mainline_test/.env

# Database
DB_USER=guardian
DB_PASSWORD=change_this_in_production
DB_NAME=guardian

# JWT
JWT_SECRET=your-super-secret-jwt-key-min-32-chars

# Email Service
EMAIL_SERVICE_URL=http://email-service:8080

# Debug
DEBUG=false

# CORS (comma-separated origins)
CORS_ORIGINS=http://localhost,http://localhost:80
```

## Step 6: Run Database Migrations

After starting the database, run Alembic migrations:

```bash
# From manifast container
docker-compose exec manifast alembic upgrade head
```

Or include in Dockerfile/entrypoint:

```dockerfile
# manifast/Dockerfile (add before CMD)
COPY entrypoint.sh .
RUN chmod +x entrypoint.sh
ENTRYPOINT ["./entrypoint.sh"]
```

```bash
# manifast/entrypoint.sh
#!/bin/bash
set -e

# Wait for database
echo "Waiting for database..."
while ! nc -z database 5432; do
  sleep 1
done

# Run migrations
echo "Running migrations..."
alembic upgrade head

# Start server
echo "Starting server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## Step 7: Verification

### 7.1 Start Services

```bash
cd mainline_test
docker-compose up --build -d
```

### 7.2 Verify Endpoints

```bash
# Health check
curl http://localhost/health

# Guardian auth endpoints
curl http://localhost/api/auth/request-token \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com"}'

# Frontend
open http://localhost/login
```

### 7.3 Check Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f manifast
```

## Troubleshooting

### Guardian module not found

```bash
# Verify Guardian is installed in Manifast
docker-compose exec manifast pip list | grep guardian
```

### Database connection errors

```bash
# Check database is healthy
docker-compose ps database

# Check environment variables
docker-compose exec manifast env | grep DATABASE
```

### CORS errors

Ensure `CORS_ORIGINS` in `.env` includes your frontend URL.

### JWT errors

Ensure `JWT_SECRET` is the same across all services and at least 32 characters.

## Layer Version Management

To update Guardian to a new version:

1. Build new Guardian images with updated tag
2. Update image references in Evoke/Manifast Dockerfiles
3. Rebuild and redeploy

```bash
# Build new version
docker build -t guardian-frontend:1.1.0 --target layer ./frontend
docker build -t guardian-backend:1.1.0 --target layer ./backend

# Update Dockerfiles to use :1.1.0
# Rebuild mainline_test
docker-compose up --build -d
```
