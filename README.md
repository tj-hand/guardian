# Guardian

Passwordless authentication service using 6-digit email tokens. Built with Vue 3 frontend and FastAPI backend, running on the Evoke → Bolt → Manifast stack.

## Features

- **Passwordless Authentication** - Users authenticate via 6-digit codes sent to their email
- **JWT Sessions** - Secure session management with configurable expiry
- **Rate Limiting** - Built-in protection against brute-force attacks
- **Email Whitelist** - Optional whitelist mode for controlled access
- **White-Label Ready** - Customizable branding and email templates
- **Docker-First** - Full Docker Compose setup for development and production

## Tech Stack

| Component | Technology |
|-----------|------------|
| Frontend | Vue 3, TypeScript, Vite, Pinia, Vue Router |
| Backend | FastAPI, Python 3.11, SQLAlchemy, Alembic |
| Database | PostgreSQL 17 |
| Email | Mailgun API |
| Auth | JWT tokens with configurable expiry |

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Mailgun account (for sending emails)

### 1. Clone and Configure

```bash
# Clone the repository
git clone <repository-url>
cd guardian

# Copy environment files
cp .env.example .env
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

### 2. Configure Environment

Edit `backend/.env` with your settings:

```bash
# Generate a secure secret key
SECRET_KEY=$(openssl rand -hex 32)

# Configure Mailgun
MAILGUN_API_KEY=your-mailgun-api-key
MAILGUN_DOMAIN=your-domain.com
MAILGUN_FROM_EMAIL=noreply@your-domain.com
```

### 3. Start Services

```bash
# Start all services
docker-compose up -d

# Run database migrations
docker-compose exec backend alembic upgrade head
```

### 4. Access the Application

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## API Endpoints

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/request-token` | Request 6-digit token via email |
| POST | `/api/auth/validate-token` | Validate token and receive JWT |
| POST | `/api/auth/refresh` | Refresh JWT token |
| POST | `/api/auth/logout` | Logout (client-side token removal) |
| GET | `/api/auth/me` | Get current user info (requires JWT) |

### Health

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Service health check |

### Example: Authentication Flow

```bash
# 1. Request a token
curl -X POST http://localhost:8000/api/auth/request-token \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com"}'

# 2. Validate token (use the 6-digit code from email)
curl -X POST http://localhost:8000/api/auth/validate-token \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "token": "123456"}'

# 3. Use the JWT token for authenticated requests
curl http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer <your-jwt-token>"
```

## Configuration

### Backend Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | JWT signing key (change in production!) | - |
| `TOKEN_EXPIRY_MINUTES` | 6-digit token validity | 15 |
| `SESSION_EXPIRY_DAYS` | JWT session duration | 7 |
| `RATE_LIMIT_REQUESTS` | Max token requests per window | 3 |
| `RATE_LIMIT_WINDOW_MINUTES` | Rate limit window duration | 15 |
| `ENABLE_EMAIL_WHITELIST` | Restrict to pre-registered users | false |
| `MAILGUN_API_KEY` | Mailgun API key | - |
| `MAILGUN_DOMAIN` | Mailgun sending domain | - |

### Frontend Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `VITE_API_BASE_URL` | Backend API URL | http://localhost:8000/api |
| `VITE_APP_NAME` | Application name | Guardian |
| `VITE_BRAND_PRIMARY_COLOR` | Primary brand color | #007bff |
| `VITE_TOKEN_LENGTH` | Token length (must match backend) | 6 |

## Development

### Running Tests

```bash
# Backend tests
docker-compose exec backend pytest

# Backend tests with coverage
docker-compose exec backend pytest --cov=app --cov-report=term-missing

# Frontend unit tests
docker-compose exec frontend npm run test

# Frontend E2E tests
docker-compose exec frontend npm run test:e2e
```

### Code Quality

```bash
# Backend formatting and linting
docker-compose exec backend black app/
docker-compose exec backend isort app/
docker-compose exec backend mypy app/

# Frontend linting
docker-compose exec frontend npm run lint
docker-compose exec frontend npm run type-check
```

### Local Development (without Docker)

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

## Project Structure

```
guardian/
├── backend/
│   ├── app/
│   │   ├── api/routes/       # API endpoints
│   │   ├── core/             # Config, database, security
│   │   ├── models/           # SQLAlchemy models
│   │   ├── schemas/          # Pydantic schemas
│   │   └── services/         # Business logic
│   ├── alembic/              # Database migrations
│   ├── tests/                # Backend tests
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/       # Vue components
│   │   ├── views/            # Page views
│   │   ├── stores/           # Pinia stores
│   │   ├── composables/      # Vue composables
│   │   └── router/           # Vue Router config
│   ├── tests/                # Frontend tests
│   └── Dockerfile
├── docs/
│   └── INTEGRATION.md        # Integration guide
├── docker-compose.yml        # Development setup
└── docker-compose.prod.yml   # Production setup
```

## Production Deployment

For production deployment, use the production Docker Compose file:

```bash
docker-compose -f docker-compose.prod.yml up -d
```

Key production considerations:
- Set a strong `SECRET_KEY` (use `openssl rand -hex 64`)
- Use secure database credentials
- Configure `ALLOWED_ORIGINS` for CORS
- Use HTTPS (configure via reverse proxy)
- Review rate limiting settings for your use case

## Documentation

- [Integration Guide](docs/INTEGRATION.md) - How to integrate Guardian into other projects
- [API Documentation](http://localhost:8000/docs) - Interactive API docs (when running)

## License

See [LICENSE](LICENSE) for details.
