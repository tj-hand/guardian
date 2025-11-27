# Guardian Integration Guide

This guide explains how to integrate Guardian with your Evoke → Bolt → Manifast stack.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                      GUARDIAN                            │
│           Passwordless Email Token Authentication        │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────┐     ┌──────────┐     ┌──────────────────┐ │
│  │ Frontend │ ──► │   Bolt   │ ──► │     Backend      │ │
│  │  (Vue 3) │     │ Gateway  │     │    (FastAPI)     │ │
│  └──────────┘     └──────────┘     └──────────────────┘ │
│                                                          │
│  Port: 5173        Port: 8080       Port: 8000          │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

## Quick Start

### 1. Start Guardian Services

```bash
# Start database and backend
docker-compose up -d database backend

# Wait for backend to be healthy
docker-compose logs -f backend

# Start frontend
docker-compose up -d frontend
```

### 2. Access the Application

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/api/docs

### 3. Test the Flow

1. Navigate to http://localhost:5173
2. Click "Get Started" or go to /login
3. Enter your email address
4. Check your terminal logs for the 6-digit code (in dev mode)
5. Enter the code to authenticate

## API Endpoints

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/request-token` | Request 6-digit token |
| POST | `/api/auth/validate-token` | Validate token & get JWT |
| GET | `/api/auth/me` | Get current user info |
| POST | `/api/auth/refresh` | Refresh JWT token |
| POST | `/api/auth/logout` | Logout user |

### Health Checks

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Full health check |
| GET | `/health/live` | Liveness probe |
| GET | `/health/ready` | Readiness probe |

## Configuration

### Backend Environment Variables

```env
# Application
APP_NAME=Guardian
ENVIRONMENT=development
SECRET_KEY=your-secret-key

# Database
POSTGRES_USER=guardian
POSTGRES_PASSWORD=guardian123
POSTGRES_HOST=database
POSTGRES_PORT=5432
POSTGRES_DB=guardian_db

# Token Settings
TOKEN_EXPIRY_MINUTES=10
SESSION_EXPIRY_DAYS=7

# Email (Mailgun)
MAILGUN_API_KEY=your-api-key
MAILGUN_DOMAIN=your-domain
MAILGUN_FROM_EMAIL=noreply@yourdomain.com

# Security
ENABLE_EMAIL_WHITELIST=false
CORS_ORIGINS=http://localhost:5173
```

### Frontend Environment Variables

```env
VITE_API_URL=
VITE_APP_NAME=Guardian
```

## Bolt Gateway Integration

To route Guardian through Bolt gateway:

1. **Enable Gateway Profile**:
```bash
docker-compose --profile gateway up -d
```

2. **Configure Backend for Gateway**:
```env
BOLT_GATEWAY_ENABLED=true
BOLT_GATEWAY_HEADER=X-Forwarded-By
BOLT_GATEWAY_VALUE=bolt-gateway
```

3. **Access via Gateway**: http://localhost:8080

## Development Mode

In development mode without Mailgun configured, tokens are logged to the console:

```
[DEV MODE] Token for t***@example.com: 123456 (Email not sent - Mailgun not configured)
```

## Database Migrations

Run migrations with Alembic:

```bash
# Generate new migration
docker-compose exec backend alembic revision --autogenerate -m "description"

# Apply migrations
docker-compose exec backend alembic upgrade head

# Rollback
docker-compose exec backend alembic downgrade -1
```

## Testing

### Backend Tests

```bash
cd backend
pip install -r requirements.txt
pytest
```

### Frontend Tests

```bash
cd frontend
npm install
npm test
```

## Security Considerations

1. **Change SECRET_KEY** in production
2. **Enable HTTPS** via Bolt gateway
3. **Configure CORS** for your domain
4. **Set up Mailgun** for email delivery
5. **Enable email whitelist** for restricted access
6. **Use strong database credentials**

## Troubleshooting

### Token not received
- Check backend logs for the token (dev mode)
- Verify Mailgun configuration (production)
- Check rate limits (3 requests per 15 minutes)

### Invalid token error
- Tokens expire after 10 minutes (configurable)
- Tokens are single-use
- Check for typos in the 6-digit code

### CORS errors
- Add your frontend URL to `CORS_ORIGINS`
- Ensure credentials are allowed

### Database connection failed
- Verify database is healthy: `docker-compose ps`
- Check database credentials match
- Wait for healthcheck to pass
