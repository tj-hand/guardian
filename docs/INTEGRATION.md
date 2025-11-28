# Email Token Authentication - Integration Guide

## Overview

This document defines how to integrate the Email Token Authentication system into other projects. Like the Nginx API Gateway, this system is designed to be imported and customized without modifying core functionality.

**Integration Philosophy:**
- **Pull, don't fork** - Import this repository as a module/submodule
- **Configure, don't modify** - Use environment variables and configuration files
- **Extend via APIs** - Build on top of authentication endpoints
- **Update easily** - Pull latest changes without losing customizations

---

## File Classification System

### 🔒 CORE FILES (IMMUTABLE - DO NOT MODIFY)

These files contain core business logic and should **NEVER** be modified when importing into other projects. Any changes needed should be contributed back to this repository.

#### Backend Core Files

**API Routes:**
- `backend/app/api/routes/auth.py` - Authentication endpoints
- `backend/app/api/routes/health.py` - Health check endpoints
- `backend/app/api/dependencies.py` - API dependencies

**Business Logic:**
- `backend/app/services/token_service.py` - 6-digit token generation/validation
- `backend/app/services/jwt_service.py` - JWT token management
- `backend/app/services/email_service.py` - Email sending logic
- `backend/app/services/rate_limit_service.py` - Rate limiting logic
- `backend/app/services/template_service.py` - Template rendering logic
- `backend/app/services/cleanup_service.py` - Background cleanup for expired tokens

**Data Models:**
- `backend/app/models/user.py` - User database model
- `backend/app/models/token.py` - Token database model
- `backend/app/schemas/*.py` - All Pydantic schemas

**Core Configuration:**
- `backend/app/core/config.py` - Settings class (structure only)
- `backend/app/core/database.py` - Database connection management
- `backend/app/core/security.py` - Security utilities

**Application Entry:**
- `backend/app/main.py` - FastAPI application factory
- `backend/app/__init__.py` - Package initialization

**Migrations:**
- `backend/alembic/` - Database migrations (all files)

**Tests:**
- `backend/tests/` - All test files (for reference and CI)

**Docker Configuration:**
- `backend/Dockerfile` - Backend container build
- `backend/requirements.txt` - Python dependencies

#### Frontend Core Files

**Components:**
- `frontend/src/components/auth/EmailInput.vue` - Email input component
- `frontend/src/components/auth/TokenInput.vue` - 6-digit token input with auto-submit
- `frontend/src/components/layout/AppHeader.vue` - Application header
- `frontend/src/components/layout/AppFooter.vue` - Application footer
- `frontend/src/components/layout/AppLayout.vue` - Main layout wrapper

**Views:**
- `frontend/src/views/Login.vue` - Login page
- `frontend/src/views/Dashboard.vue` - Protected dashboard
- `frontend/src/views/Home.vue` - Home/landing page

**Composables:**
- `frontend/src/composables/useApi.ts` - API client composable
- `frontend/src/composables/useTheme.ts` - Theme composable

**Stores:**
- `frontend/src/stores/auth.ts` - Authentication state management

**Configuration:**
- `frontend/src/config/branding.ts` - Branding configuration

**Router:**
- `frontend/src/router/index.ts` - Vue Router configuration

**Application Entry:**
- `frontend/src/main.ts` - Vue app initialization
- `frontend/src/App.vue` - Root component

**Type Definitions:**
- `frontend/src/types/index.ts` - TypeScript type definitions

**Build Configuration:**
- `frontend/vite.config.ts` - Vite configuration
- `frontend/tsconfig.json` - TypeScript configuration
- `frontend/package.json` - Dependencies
- `frontend/Dockerfile` - Frontend container build

#### Root Configuration

- `docker-compose.yml` - Multi-container orchestration
- `.gitignore` - Git ignore patterns
- `CLAUDE.md` - Project specification

---

### ⚙️ CONFIGURATION FILES (CUSTOMIZABLE - MUST MODIFY)

These files **MUST** be customized for each deployment. They contain deployment-specific settings.

#### Backend Configuration

**Environment Configuration:**
- `backend/.env` - **PRIMARY CONFIGURATION FILE**
  - Copy from `backend/.env.example`
  - **CRITICAL:** Change `SECRET_KEY` in production
  - **CRITICAL:** Set strong `POSTGRES_PASSWORD`
  - Configure Mailgun credentials
  - Adjust all timing parameters

**Key Customizable Parameters in .env:**

```bash
# Application Identity
APP_NAME=Your App Name                    # Displayed in emails and UI
APP_ENV=production                        # Environment: development/staging/production
SECRET_KEY=<generate-with-openssl>        # JWT signing key (MUST CHANGE!)

# Authentication Timing
TOKEN_EXPIRY_MINUTES=15                   # 6-digit token validity (1-60)
SESSION_EXPIRY_DAYS=7                     # JWT session duration (1-30)

# For detailed JWT configuration guide, security implications, and environment-specific
# recommendations, see README.md "Authentication & Security" section

# Rate Limiting
RATE_LIMIT_REQUESTS=3                     # Max token requests per window
RATE_LIMIT_WINDOW_MINUTES=15              # Rate limit window duration

# Token Format
TOKEN_LENGTH=6                            # Digit count (4-8)

# Database (MUST CONFIGURE)
POSTGRES_USER=your_user
POSTGRES_PASSWORD=strong_password_here    # CHANGE THIS!
POSTGRES_HOST=database                    # Or external DB host
POSTGRES_PORT=5432
POSTGRES_DB=your_db_name

# Email Service (MUST CONFIGURE)
MAILGUN_API_KEY=key-xxxxxxxxx
MAILGUN_DOMAIN=mg.yourdomain.com
MAILGUN_FROM_EMAIL=noreply@yourdomain.com
MAILGUN_FROM_NAME=Your App Name

# Security
ALLOWED_ORIGINS=https://yourfrontend.com  # Frontend URLs (comma-separated)

# White-Label Branding
COMPANY_NAME=Your Company
SUPPORT_EMAIL=support@yourdomain.com
BRAND_PRIMARY_COLOR=#007bff
```

#### Frontend Configuration

**Environment Configuration:**
- `frontend/.env` - **FRONTEND CONFIGURATION**
  - Copy from `frontend/.env.example`
  - Configure API URL
  - Set branding variables

**Key Customizable Parameters in .env:**

```bash
# API Connection
VITE_API_BASE_URL=https://api.yourdomain.com

# Application Identity
VITE_APP_NAME=Your App Name

# Branding
VITE_BRAND_PRIMARY_COLOR=#007bff
VITE_BRAND_LOGO_URL=/branding/logo.png

# Token Configuration (must match backend)
VITE_TOKEN_LENGTH=6
```

---

### 🎨 TEMPLATE FILES (CUSTOMIZABLE - WHITE-LABEL)

These files are designed for white-label customization per deployment.

#### Backend Templates

**Email Templates:**
- `backend/app/templates/email/` directory
  - **Default (immutable):** `default_token.txt` - Fallback template
  - **Customizable:** Create custom templates matching your brand
  - **Format:** Plain text with `{token}` placeholder
  - **Gitignored:** Custom templates not committed to repo

**Example Custom Template:**
```
Welcome to {app_name}!

Your verification code is:

{token}

This code expires in {expiry_minutes} minutes.

Need help? Contact {support_email}

{company_name}
```

#### Frontend Templates

**Branding Assets:**
- `frontend/src/assets/branding/` directory
  - **Add:** `logo.png`, `logo-light.png`, `logo-dark.png`
  - **Add:** `favicon.ico`, `favicon-32x32.png`
  - **Add:** Custom images, backgrounds
  - **Gitignored:** All files in this directory

**Theme Configuration:**
- `frontend/src/config/branding.json` (if exists)
  - Custom theme overrides
  - Color palettes
  - Font selections

---

### 🚫 LOCAL FILES (IGNORED - DO NOT IMPORT)

These files are local to each deployment and should not be imported or committed.

**Always Gitignored:**
- `.env` files (all environments)
- `node_modules/`
- `__pycache__/`, `*.pyc`
- `dist/`, `build/`
- `.vscode/`, `.idea/` (IDE settings)
- `logs/`, `*.log`
- `coverage/` (test coverage)
- `database/` volumes (Docker volumes)

**Gateway-Specific Ignores:**
- `gateway/test-frontend/`, `gateway/test-backend/` (not needed)
- `gateway/volumes/`, `gateway/uploads/`
- `gateway/.env`, `gateway/*.log`

---

## Integration Process

### Step 1: Import Repository

**Option A: Git Submodule (Recommended)**
```bash
cd your-project/
git submodule add <this-repo-url> modules/email-auth
git submodule update --init --recursive
```

**Option B: Clone Separately**
```bash
git clone <this-repo-url> email-auth-module
```

### Step 2: Copy Configuration Files

```bash
# Backend configuration
cp modules/email-auth/backend/.env.example backend/.env

# Frontend configuration
cp modules/email-auth/frontend/.env.example frontend/.env

# Gateway configuration (if using)
cp modules/email-auth/gateway/.env.example gateway/.env
```

### Step 3: Customize Configuration

**Edit `backend/.env`:**
1. **Generate secure SECRET_KEY:**
   ```bash
   openssl rand -hex 32
   ```
2. Set production `APP_ENV=production`
3. Configure database credentials
4. Set Mailgun API credentials
5. Adjust timing parameters:
   - `TOKEN_EXPIRY_MINUTES` (default: 15)
   - `SESSION_EXPIRY_DAYS` (default: 7)
   - `RATE_LIMIT_REQUESTS` (default: 3)
   - `RATE_LIMIT_WINDOW_MINUTES` (default: 15)
6. Set branding variables

**Edit `frontend/.env`:**
1. Set `VITE_API_BASE_URL` to your backend URL
2. Configure branding variables
3. Ensure `VITE_TOKEN_LENGTH` matches backend

### Step 4: Add White-Label Assets

```bash
# Add your branding assets
cp your-logo.png frontend/src/assets/branding/logo.png
cp your-favicon.ico frontend/public/favicon.ico

# Customize email templates
cp your-email-template.txt backend/app/templates/email/custom_token.txt
```

### Step 5: Update Docker Compose

If integrating into larger Docker Compose setup, merge the services:

```yaml
# your-project/docker-compose.yml
services:
  # Your existing services...

  # Email Auth Backend
  auth-backend:
    build: ./modules/email-auth/backend
    env_file: ./modules/email-auth/backend/.env
    depends_on:
      - auth-database

  # Email Auth Frontend
  auth-frontend:
    build: ./modules/email-auth/frontend
    env_file: ./modules/email-auth/frontend/.env

  # Email Auth Database
  auth-database:
    image: postgres:18-alpine
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
```

### Step 6: Database Migration

```bash
# Run initial migrations
docker-compose exec auth-backend alembic upgrade head
```

### Step 7: Test Integration

```bash
# Start services
docker-compose up -d

# Test health check
curl http://localhost:8000/api/v1/health

# Test authentication flow
# 1. Request token
# 2. Receive email
# 3. Validate token
# 4. Receive JWT
```

---

## Updating from Source

When the source repository has updates:

### Git Submodule Method
```bash
cd your-project/
git submodule update --remote modules/email-auth
```

### Manual Update
```bash
cd email-auth-module/
git pull origin main

# Re-run migrations if schema changed
docker-compose exec auth-backend alembic upgrade head
```

**IMPORTANT:** Never modify core files directly. Configuration changes persist in your `.env` files.

---

## Configuration Matrix

### Timing Configuration Recommendations

| Use Case | Token Expiry | Session Expiry | Rate Limit | Window |
|----------|--------------|----------------|------------|--------|
| **High Security** | 5 min | 1 day | 2 requests | 10 min |
| **Standard** | 15 min | 7 days | 3 requests | 15 min |
| **Low Friction** | 30 min | 30 days | 5 requests | 30 min |
| **Internal Tools** | 60 min | 30 days | 10 requests | 60 min |

### Security Levels

| Level | SECRET_KEY | Password | Token Length | Expiry |
|-------|------------|----------|--------------|--------|
| **Development** | Default | Simple | 4 digits | 60 min |
| **Staging** | 32+ chars | Strong | 6 digits | 15 min |
| **Production** | 64+ chars | Very Strong | 6-8 digits | 10 min |

---

## API Integration

### Endpoints Exposed

After integration, your application can use these endpoints:

**Authentication:**
- `POST /api/v1/auth/request-token` - Request 6-digit token
- `POST /api/v1/auth/validate-token` - Validate token, get JWT
- `POST /api/v1/auth/refresh` - Refresh JWT token
- `POST /api/v1/auth/logout` - Logout (client-side)
- `GET /api/v1/auth/me` - Get current user (requires JWT)

**Health:**
- `GET /api/v1/health` - Service health check
- `GET /api/v1/health/db` - Database health check

### Using from Your Application

**JavaScript/TypeScript:**
```typescript
// Request token
const response = await fetch('http://your-api/api/v1/auth/request-token', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ email: 'user@example.com' })
});

// Validate token
const authResponse = await fetch('http://your-api/api/v1/auth/validate-token', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    email: 'user@example.com',
    token: '123456'
  })
});

const { access_token } = await authResponse.json();

// Use JWT for authenticated requests
const userResponse = await fetch('http://your-api/api/v1/auth/me', {
  headers: { 'Authorization': `Bearer ${access_token}` }
});
```

---

## Troubleshooting

### Common Integration Issues

**1. Secret Key Not Set**
- Error: "SECRET_KEY must be changed from default value in production"
- Solution: Generate with `openssl rand -hex 32` and set in `.env`

**2. Database Connection Failed**
- Check `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_USER`, `POSTGRES_PASSWORD`
- Ensure database service is running
- Verify network connectivity between containers

**3. Emails Not Sending**
- Check `MAILGUN_API_KEY` and `MAILGUN_DOMAIN` are correct
- Verify Mailgun domain is verified in Mailgun dashboard
- Check logs: `docker-compose logs auth-backend`

**4. CORS Errors**
- Add frontend URL to `ALLOWED_ORIGINS` in backend `.env`
- Format: `https://frontend.com,https://app.frontend.com`

**5. Token Expiry Too Short/Long**
- Adjust `TOKEN_EXPIRY_MINUTES` in backend `.env`
- Restart backend service: `docker-compose restart auth-backend`

**6. Rate Limiting Too Restrictive**
- Increase `RATE_LIMIT_REQUESTS` in backend `.env`
- Increase `RATE_LIMIT_WINDOW_MINUTES` for longer window

---

## Best Practices

### DO ✅
- Use Git submodules for version-controlled imports
- Always copy `.env.example` to `.env` before customizing
- Generate unique `SECRET_KEY` per environment
- Test authentication flow after configuration changes
- Document your specific customizations
- Use separate `.env` for dev/staging/production
- Store secrets in secure vaults (Azure Key Vault, AWS Secrets Manager)

### DON'T ❌
- Modify core business logic files
- Commit `.env` files to version control
- Use default `SECRET_KEY` in production
- Share secrets between environments
- Hard-code configuration values
- Skip database migrations
- Bypass rate limiting in production

---

## Support and Contributions

### Requesting Features
If you need functionality not available through configuration:
1. Check if it can be implemented via API extension
2. If core changes needed, open issue in source repository
3. Contribute back via pull request

### Reporting Bugs
1. Verify issue exists in source repository
2. Check if issue is configuration-related
3. Open issue with reproduction steps

### Contributing Improvements
1. Fork source repository
2. Make changes to core functionality
3. Submit pull request
4. Update integration guide if needed

---

## Version Compatibility

| Email Auth Version | Min Python | Min Node | Min PostgreSQL | Min Docker |
|--------------------|------------|----------|----------------|------------|
| 1.x.x              | 3.13       | 22.x     | 18.x           | 20.x       |

---

## File Import Checklist

When importing into your project, import these file categories:

- ✅ **Core Files** - Import all (read-only)
- ✅ **Configuration Examples** - Import `.env.example` files
- ✅ **Docker Configuration** - Import Dockerfiles and compose files
- ✅ **Documentation** - Import README.md, INTEGRATION.md, CLAUDE.md
- ❌ **Environment Files** - Do NOT import `.env` files
- ❌ **Local Development** - Do NOT import `node_modules/`, `__pycache__/`
- ❌ **IDE Settings** - Do NOT import `.vscode/`, `.idea/`
- ❌ **Gateway Test Services** - Do NOT import `gateway/test-*/`

---

## Summary

This Email Token Authentication system is designed for easy integration:

1. **Import via Git submodule** or clone
2. **Configure via .env files** (no code changes)
3. **Customize via templates** (white-label)
4. **Extend via APIs** (build on top)
5. **Update easily** (pull latest changes)

**Remember:** Core files are immutable. All customization happens through configuration, templates, and API integration.

For detailed configuration options, see:
- [Backend Configuration](backend/.env.example)
- [Frontend Configuration](frontend/.env.example)
- [Project Specification](CLAUDE.md)
- [JWT & Security Guide](README.md#authentication--security) - JWT lifecycle, refresh tokens, security implications
