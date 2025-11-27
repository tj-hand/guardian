# Guardian

Passwordless authentication service using 6-digit email tokens. A **Layer 1** module for the **Evoke → Bolt → Manifast** architecture.

## Overview

Guardian enables users to authenticate via secure, time-limited 6-digit tokens delivered by email. No passwords required.

```
┌─────────────────────────────────────────────────────────────────┐
│                    LAYERED ARCHITECTURE                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────┐        ┌────────┐        ┌──────────────┐  │
│  │ Frontend        │        │        │        │ Backend      │  │
│  │ Container       │───────►│  Bolt  │───────►│ Container    │  │
│  ├─────────────────┤        │(Gateway)│       ├──────────────┤  │
│  │ L0: Evoke       │        └────────┘        │ L0: Manifast │  │
│  │ L1: Guardian FE │                          │ L1: Guardian │  │
│  └─────────────────┘                          └──────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Layer Architecture

Guardian is designed as a **Layer 1** module that integrates into the base containers:

| Component | Container | Layer | Purpose |
|-----------|-----------|-------|---------|
| guardian-frontend | Evoke | Layer 1 | Login UI, token input forms |
| guardian-backend | Manifast | Layer 1 | Token generation, validation, JWT |

### Flow
```
Guardian (FE) → Evoke (L0) → Bolt → Manifast (L0) → Guardian (BE)
```

## Features

- **Passwordless** - No password fatigue or credential attacks
- **Secure** - 6-digit time-limited tokens, single-use, SHA-256 hashed
- **JWT Sessions** - Stateless authentication with token refresh
- **Rate Limited** - Protection against brute force attacks
- **Email Whitelist** - Optional restriction to pre-registered users
- **Modular** - Independent layer that mounts into base containers

## Integration

### Frontend (Evoke Integration)

```typescript
// In Evoke (Layer 0)
import { guardianRoutes, useAuthStore, installGuardian } from '@guardian/frontend'

// Install plugin
app.use(installGuardian)

// Add routes
guardianRoutes.forEach(route => router.addRoute(route))

// Use navigation guard
router.beforeEach(guardianNavigationGuard)
```

### Backend (Manifast Integration)

```python
# In Manifast (Layer 0)
from guardian.app import setup_guardian, guardian_lifespan

# Option 1: Quick setup
setup_guardian(app, prefix="/api")

# Option 2: Manual router mount
from guardian.app import auth_router
app.include_router(auth_router, prefix="/api")

# Register models for migrations
from guardian.app import get_guardian_models
# Add to Alembic target_metadata
```

## Development

### Prerequisites

- Docker & Docker Compose
- Node.js 20+ (for frontend development)
- Python 3.11+ (for backend development)

### Standalone Development

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Frontend
cd frontend
npm install
npm run dev
```

### Building Layer Images

```bash
# Build frontend layer image
docker build -t guardian-frontend:latest --target layer ./frontend

# Build backend layer image
docker build -t guardian-backend:latest --target layer ./backend
```

### Using in Evoke/Manifast Dockerfiles

```dockerfile
# In Evoke Dockerfile
FROM guardian-frontend:latest as guardian
# ... later in build
COPY --from=guardian /guardian /app/layers/guardian

# In Manifast Dockerfile
FROM guardian-backend:latest as guardian
# ... later in build
COPY --from=guardian /guardian /app/layers/guardian
RUN pip install /app/layers/guardian/dist/*.whl
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/request-token` | Request 6-digit token |
| POST | `/api/auth/validate-token` | Validate token & get JWT |
| GET | `/api/auth/me` | Get current user |
| POST | `/api/auth/refresh` | Refresh JWT |
| POST | `/api/auth/logout` | Logout |

## Authentication Flow

1. **User enters email** → Backend generates 6-digit token
2. **Token sent via email** → User receives code
3. **User enters token** → Backend validates
4. **On success** → JWT session created

## Project Structure

```
guardian/
├── backend/                 # FastAPI Layer 1 module
│   ├── app/
│   │   ├── __init__.py     # Layer exports (routers, models, setup)
│   │   ├── api/routes/     # API endpoints
│   │   ├── core/           # Config, database, security
│   │   ├── models/         # SQLAlchemy models
│   │   ├── schemas/        # Pydantic schemas
│   │   └── services/       # Business logic
│   ├── alembic/            # Database migrations
│   ├── tests/
│   ├── Dockerfile          # Multi-stage with layer output
│   └── pyproject.toml      # Package configuration
├── frontend/               # Vue 3 Layer 1 module
│   └── src/
│       ├── index.ts        # Layer exports (routes, stores, components)
│       ├── components/     # Vue components
│       ├── composables/    # API client
│       ├── stores/         # Pinia stores
│       ├── router/         # Route definitions
│       └── views/          # Page components
│   ├── Dockerfile          # Multi-stage with layer output
│   └── package.json        # npm package with exports
├── database/               # Init scripts
└── docs/                   # Documentation
```

## Exports

### Frontend (@guardian/frontend)

```typescript
// Layer info
export { layerInfo }

// Routes
export { guardianRoutes, guardianNavigationGuard }

// Stores
export { useAuthStore }

// Components
export { EmailInput, TokenInput }

// Views
export { LoginView, DashboardView }

// Plugin
export { installGuardian }
```

### Backend (guardian.app)

```python
# Layer info
layer_info

# Routers
guardian_router, auth_router, health_router

# Setup helpers
setup_guardian(), guardian_lifespan()

# Models
User, AuthToken, Base, get_guardian_models()

# Schemas
TokenRequest, TokenValidationResponse, UserResponse, etc.

# Database
get_db(), init_database(), close_database()

# Services
create_access_token(), decode_access_token()

# Dependencies
get_current_user
```

## License

MIT
