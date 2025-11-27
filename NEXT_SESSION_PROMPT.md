# Guardian Implementation - Complete Session Prompt

## Project Overview

Guardian is a passwordless authentication service using 6-digit email tokens. It is a Layer 1 module that runs inside Evoke (frontend) and Manifast (backend) containers.

## Architecture: Layered System

The system uses a layered architecture where Guardian (Layer 1) is mounted into base containers (Layer 0):

- Frontend Container: Evoke (Layer 0) hosts Guardian Frontend (Layer 1)
- Gateway Container: Bolt handles routing between frontend and backend
- Backend Container: Manifast (Layer 0) hosts Guardian Backend (Layer 1)

Request Flow: User -> Guardian FE -> Evoke (L0) -> Bolt (Gateway) -> Manifast (L0) -> Guardian BE -> Database

Guardian produces TWO independent images:
1. guardian-frontend: Vue 3 module for Evoke to mount
2. guardian-backend: FastAPI module for Manifast to mount

Integration is done by the mainline_test repository, which orchestrates all layers together. Each repository (Guardian, Evoke, Bolt, Manifast) must remain independent.

## Orchestrator Instructions

You are the AI Orchestrator following servant leadership philosophy. Read your instructions from /home/user/guardian/Claude.md

Your agent team is defined in the agents folder:
- Database Agent (agents/database-agent.md): PostgreSQL, Alembic, SQLAlchemy models
- FastAPI Agent (agents/fastapi-agent.md): Backend APIs, services, Pydantic schemas
- Vue Agent (agents/vue-agent.md): Frontend logic, stores, API integration
- UX/UI Agent (agents/uxui-agent.md): Components, layouts, theming
- DevOps Agent (agents/devops-agent.md): Docker, deployment
- QA Agent (agents/qa-agent.md): Review, testing

## Reference Implementation

First, extract the source code to copy from:

unzip -o /home/user/guardian/repos/email_token_authentication-develop.zip -d /tmp/reference/

The reference implementation contains all the code that should be copied to Guardian. Do NOT implement from scratch - copy and adapt from the reference.

## Critical Features to Copy

1. White-Label Theming System (THIS WAS MISSING BEFORE - MUST INCLUDE)
   - Source: /tmp/reference/email_token_authentication-develop/frontend/src/config/branding.ts
   - Source: /tmp/reference/email_token_authentication-develop/frontend/src/composables/useTheme.ts
   - This provides environment-variable-based customization for colors, logos, fonts, company name, etc.

2. Backend Structure
   - Models: user.py, token.py with UUID primary keys and timestamps
   - Services: token_service.py, email_service.py, jwt_service.py, template_service.py, rate_limit_service.py, cleanup_service.py
   - Routes: auth.py, health.py
   - Schemas: auth.py, health.py
   - Core: config.py, database.py, security.py

3. Frontend Structure
   - Components: EmailInput.vue, TokenInput.vue, CountdownTimer.vue, AppHeader.vue, AppFooter.vue, AppLayout.vue
   - Views: Login.vue, Dashboard.vue, Home.vue
   - Stores: auth.ts
   - Composables: useApi.ts, useTheme.ts, useTokenTimer.ts
   - Config: branding.ts

4. GitHub Actions Workflows
   - .github/workflows/build-frontend.yml
   - .github/workflows/build-backend.yml
   - .github/workflows/release.yml

5. Docker Configuration
   - backend/Dockerfile
   - frontend/Dockerfile
   - docker-compose.yml
   - docker-compose.prod.yml

## Execution Plan

Execute in this order, using the Task tool to delegate to agents:

Phase 1 - Database Agent:
- Copy models from reference to /home/user/guardian/backend/app/models/
- Copy alembic configuration and migrations to /home/user/guardian/backend/alembic/
- Ensure UUID primary keys, created_at/updated_at timestamps, proper indexes

Phase 2 - FastAPI Agent:
- Copy core modules (config.py, database.py, security.py) to /home/user/guardian/backend/app/core/
- Copy services to /home/user/guardian/backend/app/services/
- Copy routes to /home/user/guardian/backend/app/api/routes/
- Copy schemas to /home/user/guardian/backend/app/schemas/
- Copy main.py to /home/user/guardian/backend/app/
- Create Layer 1 exports in app/__init__.py (setup_guardian function, router exports, model exports)

Phase 3 - Vue Agent and UX/UI Agent (can run in parallel):
- Copy all frontend structure from reference to /home/user/guardian/frontend/
- MUST include the white-label theming system (branding.ts, useTheme.ts)
- Create Layer 1 exports in src/index.ts (routes, stores, components, install function)

Phase 4 - DevOps Agent:
- Copy and adapt Dockerfiles for multi-stage builds with "layer" target
- Copy GitHub Actions workflows to .github/workflows/
- Ensure Layer 1 architecture as documented in MODULAR_LAYERED_ARCHITECTURE_CONCEPTUAL.md

Phase 5 - QA Agent:
- Review all code against agent checklists
- Validate Layer 1 exports work correctly
- Ensure white-label theming is functional
- Check that both images can be built

## Layer 1 Export Requirements

The key difference from a standalone app is that Guardian must EXPORT its functionality for the host containers to mount.

Frontend must export from src/index.ts:
- guardianRoutes (route definitions for Evoke to register)
- useAuthStore (Pinia store)
- useTheme (theme composable)
- installGuardian function (Vue plugin for Evoke to call)
- All components that Evoke might use directly

Backend must export from app/__init__.py:
- auth_router (FastAPI router for Manifast to mount)
- User and AuthToken models (for Manifast's Alembic)
- setup_guardian function (convenience function to mount all routes)
- Database utilities (get_db, init_database, etc.)

## Delegation Format

When using the Task tool to delegate to agents, provide this information:

Task Title: [Descriptive title]
Agent: [Agent name from the list]
Feature: GUARDIAN-XXX (sequential numbering)
Branch: Create new branch from main
Priority: High/Medium/Low

Objective: Clear description of what needs to be accomplished

Reference: Specify which files to copy from /tmp/reference/email_token_authentication-develop/
Destination: Specify where to copy to in /home/user/guardian/

Acceptance Criteria: List specific checkboxes the agent must complete

Notes: Remind agent to read their instructions from /home/user/guardian/agents/[name]-agent.md

## Important Reminders

1. COPY from reference implementation - do not implement from scratch
2. MUST include white-label theming system - this was missing in the previous attempt
3. Layer 1 architecture - Guardian exports modules, it does not create a standalone application
4. Use the Task tool to delegate to agents - do not do everything directly as the orchestrator
5. Two independent images - guardian-frontend and guardian-backend
6. mainline_test handles integration - Guardian repositories must be independent
7. Each agent should read their instructions from the agents folder before executing

## Getting Started

1. Read /home/user/guardian/Claude.md to understand your orchestrator role
2. Read each agent file in /home/user/guardian/agents/ to understand capabilities
3. Extract the reference implementation to /tmp/reference/
4. Create a new branch from main for this work
5. Create an action plan following the execution phases above
6. Delegate to agents using the Task tool in the specified order
7. Have QA Agent validate at the end
8. Commit with message format: feat: description GUARDIAN-XXX
9. Push to the branch
