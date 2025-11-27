# Guardian

Passwordless authentication service using 6-digit email tokens. Built on the **Evoke → Bolt → Manifast** architecture.

## Overview

Guardian enables users to authenticate via secure, time-limited 6-digit tokens delivered by email. No passwords required.

```
┌─────────────────────────────────────────┐
│              GUARDIAN                   │
│      (Email Token Authentication)       │
├─────────────────────────────────────────┤
│  Frontend  ──►  Bolt  ──►  Backend      │
│  (Evoke)      (Gateway)   (Manifast)    │
└─────────────────────────────────────────┘
```

## Features

- **Passwordless** - No password fatigue or credential attacks
- **Secure** - 6-digit time-limited tokens, single-use, SHA-256 hashed
- **JWT Sessions** - Stateless authentication with token refresh
- **Rate Limited** - Protection against brute force attacks
- **Email Whitelist** - Optional restriction to pre-registered users
- **Modern Stack** - Vue 3 + FastAPI for performance

## Quick Start

```bash
# Clone and navigate
cd guardian

# Start services
docker-compose up -d

# Access application
open http://localhost:5173
```

## Architecture

| Layer | Technology | Purpose |
|-------|------------|---------|
| Frontend | Vue 3 (Evoke) | Login UI, token input forms |
| Gateway | Bolt (NGINX) | Request routing, CORS |
| Backend | FastAPI (Manifast) | Token generation, validation, JWT |

## Authentication Flow

1. **User enters email** → Backend generates 6-digit token
2. **Token sent via email** → User receives code
3. **User enters token** → Backend validates
4. **On success** → JWT session created

## Development

### Prerequisites

- Docker & Docker Compose
- Node.js 20+ (for frontend development)
- Python 3.11+ (for backend development)

### Local Development

```bash
# Start database
docker-compose up -d database

# Backend (terminal 1)
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend (terminal 2)
cd frontend
npm install
npm run dev
```

### Environment Variables

Copy example files and configure:

```bash
cp .env.example .env
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/request-token` | Request 6-digit token |
| POST | `/api/auth/validate-token` | Validate token & get JWT |
| GET | `/api/auth/me` | Get current user |
| POST | `/api/auth/refresh` | Refresh JWT |
| POST | `/api/auth/logout` | Logout |

## Documentation

- [Integration Guide](docs/INTEGRATION.md) - Setup and configuration
- [Architecture](MODULAR_LAYERED_ARCHITECTURE_CONCEPTUAL.md) - System design
- API Docs: http://localhost:8000/api/docs (when running)

## Project Structure

```
guardian/
├── backend/                 # FastAPI (Manifast layer)
│   ├── app/
│   │   ├── api/routes/     # API endpoints
│   │   ├── core/           # Config, database, security
│   │   ├── models/         # SQLAlchemy models
│   │   ├── schemas/        # Pydantic schemas
│   │   └── services/       # Business logic
│   └── tests/
├── frontend/               # Vue 3 (Evoke layer)
│   └── src/
│       ├── components/     # Vue components
│       ├── composables/    # API client
│       ├── stores/         # Pinia stores
│       └── views/          # Page components
├── gateway/                # Bolt configuration
├── database/               # Init scripts
├── docs/                   # Documentation
└── docker-compose.yml      # Container orchestration
```

## License

MIT
