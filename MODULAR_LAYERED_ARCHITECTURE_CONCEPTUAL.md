# Modular Layered Architecture - Conceptual Guide
## A Composable, Multi-Tenant System with Environment-Specific Deployment

---

## Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [Core Concepts](#core-concepts)
3. [Layer Structure](#layer-structure)
4. [Development vs Production Deployment](#development-vs-production-deployment)
5. [Frontend Layer Composition](#frontend-layer-composition)
6. [Backend Layer Composition](#backend-layer-composition)
7. [White-Label Theming System](#white-label-theming-system)
8. [Multi-Tenant RBAC](#multi-tenant-rbac)
9. [Database Architecture](#database-architecture)
10. [Container Orchestration](#container-orchestration)
11. [Development Workflow](#development-workflow)
12. [Deployment Strategies](#deployment-strategies)

---

## 1. Architecture Overview

### The Vision
A **plugin-based, layered architecture** where functional modules (layers) can be:
- Developed independently in isolated containers
- Composed dynamically based on project needs
- Deployed as optimized, merged containers in production
- Added, removed, or replaced without affecting other layers

### Key Principles
- **Modularity**: Each layer is self-contained and independently deployable
- **Composability**: Layers stack on top of each other, building complexity incrementally
- **Flexibility**: Skip, replace, or add layers per project requirements
- **Performance**: Merge layers in production for optimal resource usage
- **White-Label**: Theme system allows per-project customization

---

## 2. Core Concepts

### What is a "Layer"?
A **layer** is a functional module that provides a specific capability to the system. Each layer has:
- **Frontend component** (Vue.js views, components, routes)
- **Backend component** (FastAPI routes, services, models)
- **Layer number** (defines its position in the dependency stack)
- **Optional dependencies** on lower layers

### Layer Dependency Stack
```
Layer 5: Comprehensive Logging   ← Cross-cutting (all layers)
Layer 4: Languages (i18n)        ← Depends on Layer 1
Layer 3: Authenticated Area      ← Depends on Layer 2
Layer 2: Multitenant/RBAC        ← Depends on Layer 1
Layer 1: Authentication          ← Depends on Layer 0
Layer 0: Core Infrastructure     ← Foundation
```

### Environment Strategies

#### Development Environment
```
┌─────────────┐
│   NGINX     │ ← Port 80/443
│  Gateway    │
└──────┬──────┘
       │
   ┌───┴────────────────────────┐
   │                            │
┌──▼──────┐                ┌────▼─────┐
│ Frontend│                │ Backend  │
│Container│                │Container │
│         │                │          │
│ Layer 0 │                │ Layer 0  │
│ Layer 1 │                │ Layer 1  │
│ Layer 2 │                │ Layer 2  │
│ Layer 3 │                │ Layer 3  │
│ Layer 4 │                │ Layer 4  │
│ Layer 5 │                │ Layer 5  │
└─────────┘                └──────────┘
(Hot reload)               (Hot reload)
```

#### Production Environment
```
┌─────────────┐
│   NGINX     │ ← Port 80/443
│  Gateway    │ (Single container)
└──────┬──────┘
       │
   ┌───┴────────────────────────┐
   │                            │
┌──▼──────┐                ┌────▼─────┐
│Frontend │                │ Backend  │
│ MERGED  │                │ MERGED   │
│         │                │          │
│All layers│               │All layers│
│compiled │                │mounted   │
│into SPA │                │as routes │
└────┬────┘                └────┬─────┘
     │                          │
     └──────────┬───────────────┘
                │
    ┌───────────▼──────────┐
    │                      │
┌───▼────┐  ┌──────┐  ┌───▼────┐
│Postgres│  │Redis │  │ Other  │
│Database│  │Cache │  │Services│
└────────┘  └──────┘  └────────┘
```

---

## 3. Layer Structure

### Layer 0: Core Infrastructure

#### Gateway (NGINX)
**Container**: `gateway`  
**Purpose**: Single entry point for all requests

**Responsibilities**:
- Route frontend requests to Frontend container
- Route API requests to Backend container
- SSL/TLS termination
- Rate limiting
- CORS handling
- Static file serving (prod)

**Key Configuration**:
- Upstream: frontend service on port 3000 (dev) or static files (prod)
- Upstream: backend service on port 8000
- Location `/` → frontend
- Location `/api/` → backend
- Location `/health` → health check endpoint

---

#### Frontend API Service
**Container**: `frontend`  
**Purpose**: Client-side abstraction layer for API calls

**Responsibilities**:
- Centralized API client configuration (axios/fetch)
- Route definitions and type safety
- Request/response interceptors
- Error handling
- Token management

**Key Components**:
- API client with base URL configuration
- Request interceptor: adds auth token to headers
- Response interceptor: handles 401 errors, redirects to login
- Configurable timeout and credentials

---

#### Backend Core (FastAPI)
**Container**: `backend`  
**Purpose**: Core API framework

**Responsibilities**:
- FastAPI application initialization
- Middleware setup (CORS, logging, etc.)
- Database connections
- Health checks
- Layer router mounting

**Key Setup**:
- CORS middleware for cross-origin requests
- Health endpoint at `/health`
- Dynamic router mounting based on enabled layers
- OpenAPI documentation at `/api/docs`

---

### Layer 1: Email Token Authentication

**Repositories**: 
- `layer-1-auth-frontend`
- `layer-1-auth-backend`

**Purpose**: Email-based authentication with 6-digit OTP

#### Frontend Component

**Features**:
- Login form (email input)
- OTP verification form
- Token storage and validation
- Route guards
- White-label login UI

**File Structure**:
```
layer-1-auth-frontend/
├── src/
│   ├── views/           # LoginView, OTPVerifyView
│   ├── components/      # LoginForm, OTPInput
│   ├── composables/     # useAuth
│   ├── stores/          # auth (Pinia)
│   ├── router/          # auth-routes
│   ├── services/        # authService
│   └── theme/           # default.scss, _variables.scss
├── public/
│   └── layer-1-config.json
└── package.json
```

**Key Services**:
- `authService.requestOTP(email)`: Request OTP code
- `authService.verifyOTP(email, otp)`: Verify code and get JWT
- `authService.logout()`: Clear token and logout

**Routes**:
- `/login` → LoginView (guest only)
- `/verify-otp` → OTPVerifyView (guest only)

---

#### Backend Component

**Features**:
- OTP generation and validation (6-digit, 10min expiry)
- Email sending (via SMTP or service)
- JWT token generation
- Rate limiting on OTP requests

**File Structure**:
```
layer-1-auth-backend/
├── app/
│   ├── models/          # auth.py (OTPCode, User)
│   ├── routes/          # auth.py (API endpoints)
│   ├── services/        # otp_service, email_service
│   ├── schemas/         # auth.py (Pydantic models)
│   └── dependencies/    # auth.py (get_current_user)
├── tests/
└── requirements.txt
```

**Database Models**:
- `auth_otp_codes`: Stores OTP with email, code, expiration, used flag
- `auth_users`: User accounts with email, created_at, last_login

**Key Endpoints**:
- `POST /api/auth/request-otp`: Generate and send OTP
- `POST /api/auth/verify-otp`: Verify OTP and return JWT
- `POST /api/auth/logout`: Logout user

**Authentication Flow**:
1. User enters email
2. System generates 6-digit OTP
3. OTP stored in database with 10min expiry
4. Email sent with OTP
5. User enters OTP
6. System validates OTP (not used, not expired)
7. JWT token generated and returned
8. OTP marked as used

---

### Layer 2: Multitenant Scope Authorization

**Repositories**:
- `layer-2-multitenant-frontend`
- `layer-2-multitenant-backend`

**Purpose**: Multi-tenant RBAC with polymorphic permissions

#### User Hierarchy

```
┌─────────────────────────────────────────────────────┐
│ Superadmin                                          │
│ - Access to ALL tenants                             │
│ - System-level configuration                        │
│ - User management across tenants                    │
└─────────────────────────────────────────────────────┘
                      │
        ┌─────────────┼─────────────┐
        │                           │
┌───────▼────────┐         ┌────────▼───────┐
│ Tenant A       │         │ Tenant B       │
│                │         │                │
│ Account Admin  │         │ Regular User   │
│ - Full access  │         │ - Limited      │
│   in Tenant A  │         │   access in    │
│                │         │   Tenant B     │
└────────────────┘         └────────────────┘

Same user can have different roles in different tenants
```

#### Three-Level Access Control

**Global Level (Superadmin)**
- Cross-tenant navigation
- System configuration
- Audit logs

**Tenant Level (Account Admin)**
- Tenant-wide settings
- User management within tenant
- Resource allocation

**Resource Level (Regular User)**
- Client-specific data
- Project-scoped permissions
- Feature access based on role

#### Database Schema

**Tables**:
- `tenants`: Tenant information (name, slug, settings, is_active)
- `roles`: Role definitions (name, description, is_system_role)
- `tenant_user_roles`: User-role mappings per tenant (user, tenant, role)
- `permissions`: Permission definitions (name, resource, action)
- `role_permissions`: Role-permission mappings
- `resource_policies`: Polymorphic resource-level access (user, tenant, resource_type, resource_id, can_view, can_edit, can_delete)

**Permission Convention**: `resource.action` or `resource.action.scope`
Examples:
- `client.view` - View clients
- `client.create` - Create clients
- `client.edit.own` - Edit own clients only
- `client.edit.all` - Edit all clients in tenant
- `report.export` - Export reports

**Default Roles**:
- `superadmin`: All permissions
- `account_admin`: Full tenant access
- `user`: Limited access with resource policies
- `viewer`: Read-only access

#### Backend Permission Checking

**Key Functions**:
- `get_current_user()`: Extract user from JWT token
- `require_tenant_access(tenant_slug)`: Check tenant membership
- `require_permission(permission_name)`: Decorator for endpoint protection
- `is_superadmin(user)`: Check if user is superadmin

**Permission Check Flow**:
1. Check if superadmin → allow all
2. Check role-level permission in tenant
3. Check resource-level policy if needed
4. Deny if no permission found

#### Frontend Tenant Switching

**Key Features**:
- Load available tenants on login
- Switch between tenants
- Persist current tenant in localStorage
- Reload permissions on tenant change
- Tenant switcher UI component

**Stores**:
- `useTenantStore()`: Manage current tenant, available tenants, user role
- `hasPermission(permission)`: Check if user has permission in current tenant

---

### Layer 3: Authenticated Area

**Repositories**:
- `layer-3-authenticated-frontend`
- `layer-3-authenticated-backend`

**Purpose**: Protected user interface with full functionality

#### Frontend Component

**Features**:
- Main application layout
- Dashboard
- Navigation menu
- User profile
- Settings
- Tenant switcher (if Layer 2 is present)

**File Structure**:
```
layer-3-authenticated-frontend/
├── src/
│   ├── layouts/         # AppLayout, DashboardLayout
│   ├── views/           # DashboardView, ProfileView, SettingsView
│   ├── components/      # Navigation, TenantSwitcher, UserMenu
│   └── router/          # authenticated-routes.ts
```

**Route Guards**:
- `authGuard`: Redirect to login if not authenticated
- `permissionGuard`: Check permissions before allowing access

#### Backend Component

**Features**:
- Protected endpoints (require authentication)
- User profile management
- Settings persistence
- Activity logging

**Key Patterns**:
- All routes require `Depends(get_current_user)`
- Tenant-scoped queries
- Audit logging for sensitive operations

---

### Layer 4: Languages (Internationalization)

**Repositories**:
- `layer-4-languages-frontend`
- `layer-4-languages-backend`

**Purpose**: Multi-language support with dynamic translation management

#### Frontend Component

**Features**:
- Vue i18n integration
- Language switcher UI with flags
- Automatic locale detection (localStorage → browser → default)
- RTL (Right-to-Left) support for Arabic/Hebrew
- Date/time/currency formatting per locale
- Pluralization support
- Dynamic translation loading from backend

**File Structure**:
```
layer-4-languages-frontend/
├── src/
│   ├── i18n/
│   │   ├── index.ts              # i18n configuration
│   │   ├── locales/              # JSON translation files
│   │   │   ├── pt-BR.json
│   │   │   ├── en-US.json
│   │   │   └── es-ES.json
│   │   └── rules.ts              # Pluralization rules
│   ├── components/
│   │   ├── LanguageSwitcher.vue  # Language selector UI
│   │   └── LocaleSelector.vue
│   ├── composables/
│   │   └── useI18n.ts            # i18n composable
│   ├── stores/
│   │   └── language.ts           # Language state (Pinia)
│   └── services/
│       └── translationService.ts # API calls for translations
```

**Supported Locales** (default):
- `pt-BR`: Português (Brasil) - Default
- `en-US`: English (United States)
- `es-ES`: Español (España)
- Easily extensible to other languages

**Locale Detection Logic**:
1. Check localStorage for saved preference
2. Check browser language
3. Match language code (e.g., 'pt' matches 'pt-BR')
4. Fall back to default ('pt-BR')

**Translation Structure**: Nested JSON format
```json
{
  "common": { "yes": "Sim", "no": "Não", "save": "Salvar" },
  "auth": { "login": "Entrar", "logout": "Sair" },
  "dashboard": { "welcome": "Bem-vindo, {name}!" }
}
```

**Date/Time/Currency Formatting**:
- Date formats per locale (short, long)
- Number formats (decimal, currency)
- Currency symbols (BRL, USD, EUR)

**Key Features**:
- Reactive language switching
- Persist user preference in localStorage and backend
- Update HTML lang and dir attributes
- Pluralization: "0 items | 1 item | {count} items"
- Parameter interpolation: "Welcome, {name}!"

#### Backend Component

**Features**:
- Translation storage with versioning
- Missing translation tracking
- Redis caching (1 hour TTL)
- Admin interface for translation management
- CSV import/export for translations
- Translation history and audit trail
- Dynamic translation loading API

**File Structure**:
```
layer-4-languages-backend/
├── app/
│   ├── models/
│   │   ├── translation.py        # Translation, TranslationHistory
│   │   └── locale.py             # Locale, MissingTranslation
│   ├── routes/
│   │   ├── i18n.py               # Public translation API
│   │   └── admin_translations.py # Admin management
│   ├── services/
│   │   ├── translation_service.py   # CRUD + caching
│   │   └── translation_cache.py     # Redis integration
│   ├── schemas/
│   │   └── translation.py        # Pydantic models
│   └── dependencies/
│       └── i18n.py               # Locale detection
```

**Database Tables**:
- `i18n_locales`: Available languages (code, name, is_active, is_rtl)
- `i18n_translations`: Key-value pairs (locale, key, value, namespace, version)
- `i18n_translation_history`: Change tracking (old_value, new_value, changed_by)
- `i18n_missing_translations`: Monitor untranslated keys (locale, key, request_count)

**Key Endpoints**:
- `GET /api/i18n/translations/{locale}`: Get all translations for locale
- `GET /api/i18n/translations/{locale}/{key}`: Get specific translation
- `PUT /api/users/me/locale`: Update user's preferred locale
- `GET /api/i18n/locales`: Get available locales
- `GET /admin/i18n/missing`: Get missing translations (admin)
- `POST /admin/i18n/import`: Import translations from CSV (admin)
- `GET /admin/i18n/export`: Export translations to CSV (admin)

**Translation Service with Caching**:
- Cache all translations per locale in Redis
- Invalidate cache on translation updates
- Track missing translations automatically
- Log requests for untranslated keys
- Support namespace filtering

**Missing Translation Workflow**:
1. Frontend requests translation key
2. Backend checks database
3. If not found, log to `i18n_missing_translations`
4. Increment request count
5. Admin can view most-requested missing translations
6. Admin adds translation
7. Missing translation marked as resolved

---

### Layer 5: Comprehensive Logging

**Repositories**:
- `layer-5-logging-frontend`
- `layer-5-logging-backend`

**Purpose**: Complete logging, monitoring, and audit trail system

**Note**: This is a **cross-cutting layer** that integrates with ALL other layers

#### Frontend Component

**Features**:
- Global error handler (unhandled errors & promise rejections)
- User activity tracking (page views, clicks, form submits)
- Performance monitoring (page load, API timing)
- Breadcrumb system (last 50 actions for context)
- Session tracking with unique IDs
- Batch log sending (every 5s or 10 logs, whichever comes first)
- Console log capture in production

**File Structure**:
```
layer-5-logging-frontend/
├── src/
│   ├── logger/
│   │   ├── index.ts              # Main Logger class
│   │   ├── errorHandler.ts       # Global error handling
│   │   ├── activityLogger.ts     # User activity tracking
│   │   └── performanceMonitor.ts # Performance metrics
│   ├── services/
│   │   └── logService.ts         # API calls to backend
│   ├── composables/
│   │   └── useLogger.ts          # Vue composable
│   └── plugins/
│       └── logging.ts            # Vue plugin registration
```

**Log Levels**:
- `DEBUG`: Development debugging info
- `INFO`: General information events
- `WARN`: Warning messages
- `ERROR`: Error events
- `FATAL`: Critical failures (auto-flush immediately)

**What Gets Logged**:

1. **Page Events**:
   - Page views with route info
   - Time spent on each page
   - Navigation between pages

2. **User Interactions**:
   - Button clicks
   - Form submissions
   - Search queries
   - Custom user actions

3. **API Calls**:
   - Endpoint, method, duration
   - Status codes (success/failure)
   - Request/response timing

4. **Errors**:
   - Unhandled JavaScript errors
   - Promise rejections
   - Network errors
   - Stack traces with breadcrumbs

5. **Performance Metrics**:
   - Page load time
   - DOM content loaded
   - DNS, TCP, TTFB timing
   - Resource loading

**Breadcrumb System**:
- Last 50 user actions stored
- Automatically included with error logs
- Format: timestamp + action description
- Examples: "Viewed: Dashboard", "Action: click", "API Request: POST /api/clients"

**Log Entry Structure**:
- Level (DEBUG, INFO, WARN, ERROR, FATAL)
- Message
- Timestamp
- Context (custom metadata)
- User ID (if authenticated)
- Session ID (unique per browser session)
- URL (current page)
- User Agent (browser info)
- Stack Trace (for errors)
- Breadcrumbs (last 10 actions)

**Batching Strategy**:
- Queue logs in memory
- Auto-flush every 5 seconds
- Auto-flush when 10 logs queued
- Auto-flush immediately for ERROR and FATAL levels
- Retry failed sends (prevent infinite loops)

**Performance Monitoring**:
- Automatic on page load
- Navigation Timing API
- Resource Timing API
- Track: loadTime, domContentLoaded, DNS, TCP, TTFB

**API Interceptor Integration**:
- Automatic logging of all API calls
- Request ID generation for tracking
- Duration calculation
- Error logging with context

#### Backend Component

**Features**:
- Structured logging with levels
- Request/response logging middleware
- Audit trail for sensitive operations
- Log aggregation and storage
- Log querying and filtering API
- Performance metrics collection
- Integration-ready for ELK, Datadog, Grafana

**File Structure**:
```
layer-5-logging-backend/
├── app/
│   ├── models/
│   │   ├── log.py                # Application logs
│   │   ├── audit_log.py          # Audit trail
│   │   └── metric.py             # Performance metrics
│   ├── routes/
│   │   ├── logs.py               # Log ingestion API
│   │   └── admin_logs.py         # Admin query/view API
│   ├── services/
│   │   ├── logger.py             # AppLogger service
│   │   ├── audit_service.py      # Audit logging
│   │   └── metrics_service.py    # Metrics collection
│   ├── middleware/
│   │   └── logging_middleware.py # Request/response logging
│   └── dependencies/
│       └── logging.py            # Logging utilities
```

**Log Types**:

1. **Application Logs** (`logs` table):
   - General system events
   - User actions
   - API calls
   - Errors and warnings
   - Frontend logs

2. **Audit Logs** (`audit_logs` table):
   - Sensitive operations (user deletion, permission changes)
   - Who did what, when, why
   - Old values vs new values
   - Compliance and security

3. **Performance Metrics** (`performance_metrics` table):
   - API endpoint timing
   - Status codes
   - Database query counts
   - Response times

**Database Tables**:

**logs**:
- id, level, message, timestamp
- user_id, tenant_id, session_id, request_id
- ip_address, user_agent, url
- context (JSON), stack_trace
- duration_ms
- Indexes: (timestamp, level), (user_id, timestamp)

**audit_logs**:
- id, timestamp
- user_id, tenant_id, action
- resource_type, resource_id
- old_values (JSON), new_values (JSON)
- ip_address, request_id, reason
- Indexes: (user_id, action), (resource_type, resource_id)

**performance_metrics**:
- id, timestamp
- method, endpoint, status_code
- duration_ms, db_query_count, db_query_duration_ms
- user_id, tenant_id
- Indexes: (endpoint, timestamp)

**Logging Middleware**:
- Generates unique request ID for each request
- Logs all incoming requests (method, path, query params)
- Logs all responses (status code, duration)
- Tracks performance metrics
- Adds X-Request-ID header to responses
- Handles errors with context

**Logger Service**:
- Console logging (stdout)
- File logging (error.log for errors)
- Database storage for persistence
- Context injection (user, tenant, request ID)
- Stack trace capture for errors
- Performance metric tracking

**Audit Service**:
- `log_action()`: Log sensitive operations
- `get_resource_history()`: Get audit history for resource
- `get_user_activity()`: Get user's recent activity
- Automatic old/new value tracking
- Reason field for compliance

**Key Endpoints**:
- `POST /api/logs/batch`: Receive batch of frontend logs
- `POST /api/logs/error`: Receive single error from frontend
- `GET /admin/logs`: Query application logs with filters
- `GET /admin/audit-logs`: Query audit trail
- `GET /admin/performance-metrics`: Get performance analytics

**Query Filters** (Admin):
- Level (DEBUG, INFO, WARN, ERROR, FATAL)
- User ID
- Tenant ID
- Date range (start_date, end_date)
- Limit and offset for pagination

**Integration with Monitoring Tools**:
- Log format compatible with ELK Stack
- Structured JSON for Datadog
- Metrics exportable for Grafana
- Webhook support for alerts
- Support for log shipping

**Audit Logging Best Practices**:
- Log all sensitive operations
- Include who, what, when, why
- Store old and new values
- Never log passwords or tokens
- Mask PII in general logs
- Separate audit logs for compliance

---

## 4. Development vs Production Deployment

### Development Strategy

**Goal**: Fast iteration, hot reload, independent debugging

**Container Setup**:
- **gateway**: NGINX with development config
- **frontend**: Vite dev server on port 3000, source mounted as volumes
- **backend**: Uvicorn with `--reload`, source mounted as volumes
- **db**: PostgreSQL with exposed port 5432
- **redis**: Redis with exposed port 6379

**Key Configuration**:
- All layer source directories mounted as volumes
- Hot reload enabled for frontend and backend
- Database and Redis exposed for local clients
- Environment: `docker-compose.dev.yml`

**Volume Mounts**:
```
Frontend:
- ./layer-0-core-frontend/src → /app/layers/layer-0
- ./layer-1-auth-frontend/src → /app/layers/layer-1
- ./layer-2-multitenant-frontend/src → /app/layers/layer-2
- ./layer-3-authenticated-frontend/src → /app/layers/layer-3
- ./layer-4-languages-frontend/src → /app/layers/layer-4
- ./layer-5-logging-frontend/src → /app/layers/layer-5

Backend:
- ./layer-0-core-backend/app → /app/layers/layer-0
- ./layer-1-auth-backend/app → /app/layers/layer-1
- ./layer-2-multitenant-backend/app → /app/layers/layer-2
- ./layer-3-authenticated-backend/app → /app/layers/layer-3
- ./layer-4-languages-backend/app → /app/layers/layer-4
- ./layer-5-logging-backend/app → /app/layers/layer-5
```

---

### Production Strategy

**Goal**: Performance, security, resource optimization

**Container Setup**:
- **gateway**: NGINX serving static files + reverse proxy
- **frontend**: Build container (outputs static, then exits)
- **backend**: Gunicorn with Uvicorn workers
- **db**: PostgreSQL with persistent volume
- **redis**: Redis with persistent volume and AOF

**Key Configuration**:
- All layers merged/compiled
- Static files served by NGINX
- Multiple backend workers
- No exposed ports except gateway
- Environment: `docker-compose.prod.yml`

**Volume Strategy**:
- `frontend_static`: Shared between frontend build and gateway
- `postgres_prod_data`: Database persistence
- `redis_data`: Redis persistence

---

## 5. Frontend Layer Composition

### Build-Time Layer Merging Strategy

**Approach**: Monorepo with Vite + Vue 3, layers imported at build time

**Project Structure**:
```
modular-frontend/
├── layers/
│   ├── layer-0-core/
│   ├── layer-1-auth/
│   ├── layer-2-multitenant/
│   └── layer-3-authenticated/
├── main-app/
│   ├── src/
│   │   ├── main.ts          # App initialization
│   │   ├── App.vue
│   │   ├── router/          # Router configuration
│   │   └── config/
│   │       └── layers.config.ts  # Layer configuration
│   ├── package.json
│   └── vite.config.ts
├── package.json (root)
└── pnpm-workspace.yaml
```

### Layer Configuration

**Configuration File** (`layers.config.ts`):
```typescript
interface LayerConfig {
  name: string
  enabled: boolean
  priority: number
  dependencies?: string[]
}
```

**Example Configuration**:
- Layer 0 (core): priority 0, no dependencies
- Layer 1 (auth): priority 1, depends on core
- Layer 2 (multitenant): priority 2, depends on auth
- Layer 3 (authenticated): priority 3, depends on multitenant
- Layer 4 (languages): priority 4, depends on auth
- Layer 5 (logging): priority 5, no dependencies (cross-cutting)

### Dynamic Layer Loading

**Process**:
1. Read layer configuration
2. Filter enabled layers
3. Sort by priority
4. Load each layer module dynamically
5. Register routes from each layer
6. Register stores from each layer
7. Apply themes from each layer
8. Mount app

**Layer Module Interface**:
Each layer exports:
- `name`: Layer identifier
- `version`: Layer version
- `routes`: Vue Router routes
- `stores`: Pinia stores
- `theme`: CSS/SCSS theme
- `install()`: Optional custom installation logic

### Production Build

**Build Process**:
- All enabled layers imported
- Code splitting by layer for optimization
- Rollup bundles layers into chunks
- Static files output to `/dist`
- NGINX serves static files

**Optimization**:
- Manual chunks for each layer
- Lazy loading for non-critical routes
- Tree shaking unused code
- Asset optimization

---

## 6. Backend Layer Composition

### FastAPI Router Mounting Strategy

**Approach**: Each layer provides routers that are dynamically mounted

**Project Structure**:
```
modular-backend/
├── layers/
│   ├── layer_0_core/
│   ├── layer_1_auth/
│   ├── layer_2_multitenant/
│   └── layer_3_authenticated/
├── main.py              # App initialization
├── config.py            # Layer configuration
├── requirements.txt
└── alembic/             # Database migrations
```

### Layer Configuration

**Configuration File** (`config.py`):
```python
class LayerConfig:
    name: str
    enabled: bool = True
    priority: int
    prefix: str
    tags: List[str]
```

**Example Configuration**:
- Layer 0 (core): priority 0, prefix "", tags ["core"]
- Layer 1 (auth): priority 1, prefix "/api/auth", tags ["authentication"]
- Layer 2 (multitenant): priority 2, prefix "/api/tenants", tags ["multitenant"]
- Layer 3 (authenticated): priority 3, prefix "/api/app", tags ["authenticated"]
- Layer 4 (languages): priority 4, prefix "/api/i18n", tags ["internationalization"]
- Layer 5 (logging): priority 5, prefix "/api/logs", tags ["logging", "monitoring"]

### Dynamic Layer Loading

**Process**:
1. Read layer configuration
2. Sort enabled layers by priority
3. For each layer:
   - Import layer module
   - Get router from module
   - Mount router with prefix and tags
4. Start application

**Layer Module Interface**:
Each layer provides:
- `router`: FastAPI APIRouter instance
- Database models (imported in `main.py` for migrations)
- Services and utilities

### Production Deployment

**Dockerfile Pattern**:
- Base image: Python 3.11-slim
- Install dependencies from all layers
- Copy all layer source code
- Run database migrations
- Start Gunicorn with multiple Uvicorn workers

---

## 7. White-Label Theming System

### WordPress-Style Child Themes

**Concept**: Base theme provides defaults, child themes override specific variables/components

**Theme Structure**:
```
main-app/themes/
├── base/                    # Default theme
│   ├── variables.scss
│   ├── components.scss
│   └── layout.scss
├── client-a/                # Override theme
│   ├── theme.config.ts
│   ├── variables.scss       # Overrides
│   ├── logo.svg
│   └── custom-components/
│       └── CustomHeader.vue
└── client-b/
    ├── theme.config.ts
    └── variables.scss
```

### Base Theme

**CSS Variables** (defined in `:root`):
- Colors: `--color-primary`, `--color-secondary`, `--color-success`, etc.
- Typography: `--font-family`, `--font-size-base`, `--font-weight-normal`
- Spacing: `--spacing-xs`, `--spacing-sm`, `--spacing-md`, etc.
- Layout: `--header-height`, `--sidebar-width`, `--border-radius`
- Shadows: `--shadow-sm`, `--shadow-md`, `--shadow-lg`

### Child Theme

**Configuration** (`theme.config.ts`):
- `name`: Theme name
- `extends`: Parent theme (usually 'base')
- `logo`: Custom logo path
- `favicon`: Custom favicon path
- `customComponents`: Component overrides
- `variables`: CSS variable overrides

**Customization Levels**:
1. **CSS Variables**: Override colors, fonts, spacing
2. **Custom Components**: Replace entire components
3. **Logo/Favicon**: Brand assets
4. **Config-driven**: UI changes via configuration

### Theme Loader

**Loading Process**:
1. Detect theme (from subdomain, config, or default)
2. Load base theme
3. Load child theme overrides
4. Apply CSS variables to document
5. Update favicon
6. Register custom components globally

**Theme Detection Methods**:
- Subdomain: `client-a.yourapp.com` → theme 'client-a'
- Environment variable: `VITE_THEME_NAME=client-a`
- Default: 'base'

---

## 8. Multi-Tenant RBAC

### Permission System Architecture

**Permission Naming Convention**:
```
resource.action
resource.action.scope
```

Examples:
- `client.view` - View clients
- `client.create` - Create new clients
- `client.edit.own` - Edit own clients only
- `client.edit.all` - Edit all clients in tenant
- `report.export` - Export reports
- `settings.manage` - Manage settings

### Default Roles

**System Roles** (cannot be deleted):

1. **Superadmin**:
   - All permissions (`*`)
   - Cross-tenant access
   - System configuration

2. **Account Admin**:
   - `user.*` (manage users)
   - `client.*` (manage clients)
   - `settings.manage`
   - `report.*` (view and export)

3. **User**:
   - `client.view`
   - `client.create`
   - `client.edit.own` (only own resources)
   - `report.view`

4. **Viewer**:
   - `client.view`
   - `report.view`
   - Read-only access

### Polymorphic Resource Policies

**Purpose**: Fine-grained access control at resource level

**Structure**:
- User has role in tenant (tenant-wide permissions)
- User can also have specific access to individual resources
- Resource policies override or extend role permissions

**Use Cases**:
- Share specific client with user from another team
- Grant temporary access to specific project
- Delegate access without changing roles

**Policy Fields**:
- `can_view`: Boolean
- `can_edit`: Boolean
- `can_delete`: Boolean

---

## 9. Database Architecture

### Single Database with Schema Namespacing

**Approach**: One PostgreSQL database with table prefixes per layer

**Table Naming Convention**: `{layer_prefix}_{table_name}`

**Examples**:
- Layer 1: `auth_users`, `auth_otp_codes`
- Layer 2: `tenants`, `tenant_user_roles`, `roles`, `permissions`, `role_permissions`, `resource_policies`
- Layer 3: `app_clients`, `app_projects`
- Layer 4: `i18n_locales`, `i18n_translations`, `i18n_translation_history`, `i18n_missing_translations`
- Layer 5: `logs`, `audit_logs`, `performance_metrics`

### Benefits
- Easier maintenance than multiple databases
- Simple backup/restore
- Cross-layer queries when needed
- Better for multitenant with shared schema

### Multi-Tenant Data Isolation

**Strategy**: Tenant ID column in all tenant-specific tables

**Patterns**:
- Query helpers ensure automatic tenant filtering
- `get_tenant_query(Model, tenant_id)` helper function
- Row-level security via application logic

### Soft Deletes

**Implementation**: `deleted_at` column (nullable timestamp)

**Benefits**:
- Data recovery
- Audit trail
- Referential integrity

**Query Pattern**:
- Active records: `WHERE deleted_at IS NULL`
- Include deleted: No filter
- Only deleted: `WHERE deleted_at IS NOT NULL`

---

## 10. Container Orchestration

### Production Container Architecture

```
┌─────────────────────────────────────────────────────┐
│                   Load Balancer                     │
│                   (AWS ALB / GCP LB)                │
└──────────────────────┬──────────────────────────────┘
                       │
           ┌───────────┴───────────┐
           │                       │
    ┌──────▼──────┐         ┌──────▼──────┐
    │   NGINX     │         │   NGINX     │
    │  Gateway    │         │  Gateway    │
    │ (replica 1) │         │ (replica 2) │
    └──────┬──────┘         └──────┬──────┘
           │                       │
           └───────────┬───────────┘
                       │
         ┌─────────────┼─────────────┐
         │             │             │
    ┌────▼────┐   ┌────▼────┐   ┌────▼────┐
    │Frontend │   │ Backend │   │ Backend │
    │ (static)│   │(replica1)│  │(replica2)│
    └─────────┘   └────┬────┘   └────┬────┘
                       │             │
                       └──────┬──────┘
                              │
              ┌───────────────┼───────────────┐
              │               │               │
         ┌────▼────┐     ┌────▼────┐    ┌────▼────┐
         │Postgres │     │  Redis  │    │ Other   │
         │Primary  │     │ Cluster │    │Services │
         └────┬────┘     └─────────┘    └─────────┘
              │
         ┌────▼────┐
         │Postgres │
         │ Replica │
         └─────────┘
```

### Container Orchestration Options

**Option 1: Docker Compose (Simple Projects)**
- **Pros**: Simple setup, low cost, easy debugging
- **Cons**: Manual scaling, single server
- **Use Case**: MVP, small projects, internal tools

**Option 2: Azure Container Apps (Recommended for Brazil)**
- **Pros**: Auto-scaling, managed infrastructure, good pricing
- **Cons**: Azure lock-in, learning curve
- **Use Case**: Production apps, multi-tenant SaaS

**Option 3: Kubernetes (Enterprise)**
- **Pros**: Maximum flexibility, cloud-agnostic, advanced orchestration
- **Cons**: Complex setup, higher costs, operational overhead
- **Use Case**: Large-scale, multi-region deployments

---

## 11. Development Workflow

### Layer Development Process

**Steps**:
1. **Create Layer Structure**: Set up frontend and backend directories
2. **Implement Layer**: Build features, routes, components, services
3. **Test in Isolation**: Test layer independently
4. **Update Configs**: Add layer to frontend and backend configurations
5. **Test Integration**: Test with other layers
6. **Document**: Update documentation with layer details

### Version Control Strategy

**Monorepo Structure**:
```
modular-system/
├── .git/
├── layers/
│   ├── layer-0-core/
│   ├── layer-1-auth/
│   ├── layer-2-multitenant/
│   └── layer-3-authenticated/
├── main-app/
├── docker-compose.dev.yml
├── docker-compose.prod.yml
└── README.md
```

**Branching**:
- Feature branches for new layers: `feature/layer-X-name`
- Layer updates: `update/layer-X-feature`
- Bug fixes: `fix/layer-X-issue`

### CI/CD Pipeline

**Process**:
1. Push to feature branch
2. CI runs tests for affected layers
3. Build frontend and backend
4. Create PR
5. Code review
6. Merge to main
7. CI builds production containers
8. Deploy to staging
9. Run integration tests
10. Deploy to production
11. Monitor logs and metrics

---

## 12. Deployment Strategies

### Strategy 1: Docker Compose (Simple Projects)

**When to Use**:
- MVP development
- Internal tools
- Small user base (<100 users)
- Single-region deployment

**Setup**:
- Single server with Docker Compose
- All containers on one machine
- Simple backup/restore

---

### Strategy 2: Azure Container Apps (Recommended)

**When to Use**:
- Production SaaS applications
- Multi-tenant systems
- Brazilian market (good regional pricing)
- Auto-scaling requirements

**Setup**:
- Managed container orchestration
- Auto-scaling based on metrics
- Integration with Azure services (DB, Redis, Storage)
- Easy deployment via CLI or portal

---

### Strategy 3: Kubernetes (Enterprise)

**When to Use**:
- Large-scale deployments (1000+ users)
- Multi-region requirements
- Complex orchestration needs
- Team has K8s expertise

**Setup**:
- Kubernetes cluster (EKS, GKE, AKS)
- Deployments, Services, Ingress
- Helm charts for management
- Advanced monitoring and logging

---

## Configuration Management

### Environment Variables

**Development** (`.env.dev`):
- `DATABASE_URL`: Local PostgreSQL connection
- `REDIS_URL`: Local Redis connection
- `SECRET_KEY`: Development secret (non-production)
- `VITE_API_GATEWAY_URL`: Local gateway URL
- `VITE_THEME_NAME`: Default theme

**Production** (`.env.prod`):
- `DATABASE_URL`: Production database (from vault/secrets)
- `REDIS_URL`: Production Redis (from vault/secrets)
- `SECRET_KEY`: Strong secret from secrets manager
- `VITE_API_GATEWAY_URL`: Production API URL
- `VITE_THEME_NAME`: Client-specific theme

### Layer Configuration

**Frontend** (`layers.config.ts`):
- Enable/disable layers
- Set layer dependencies
- Configure priorities

**Backend** (`config.py`):
- Layer routing prefixes
- Database settings
- Feature flags

---

## Summary

This modular layered architecture provides:

✅ **Flexibility**: Add/remove/replace layers per project  
✅ **Development Speed**: Isolated containers with hot reload  
✅ **Production Efficiency**: Merged containers for optimal performance  
✅ **Multi-tenancy**: Built-in RBAC with three user levels  
✅ **White-Label**: WordPress-style theme system  
✅ **Internationalization**: Full i18n support with dynamic translations  
✅ **Comprehensive Logging**: Complete audit trail and monitoring system  
✅ **Scalability**: Container orchestration ready  
✅ **Maintainability**: Clear separation of concerns  

### Complete Layer Stack

**Layer 0**: Core Infrastructure (Gateway, Frontend API, Backend)  
**Layer 1**: Email Token Authentication  
**Layer 2**: Multitenant RBAC & Authorization  
**Layer 3**: Authenticated User Area  
**Layer 4**: Languages & Internationalization (i18n)  
**Layer 5**: Comprehensive Logging & Audit Trail  

### When to Use This Architecture

**Perfect For**:
- Multi-tenant SaaS applications
- White-label products
- Projects needing flexible authentication
- Applications requiring audit trails
- International/multi-language applications
- Rapid prototyping with production path

**Not Ideal For**:
- Simple single-page sites
- Monolithic legacy migrations
- Projects with fixed, unchanging requirements
- Very small teams without DevOps capacity

---

The system is production-ready for the Brazilian market with Azure Container Apps integration, making it perfect for DOT Marketing's AI and data intelligence services.
