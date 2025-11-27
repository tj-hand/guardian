/**
 * Guardian Frontend - Layer 1 Authentication Module
 *
 * This module exports all Guardian authentication components, stores,
 * and routes to be mounted by the Evoke frontend container.
 *
 * Usage in Evoke:
 *   import { guardianRoutes, useAuthStore, installGuardian } from '@guardian/frontend'
 *   app.use(installGuardian)
 *   router.addRoute(guardianRoutes)
 */

// Layer metadata
export const layerInfo = {
  name: 'guardian',
  version: '1.0.0',
  layer: 1,
  description: 'Passwordless authentication with 6-digit email tokens',
}

// Routes
export { guardianRoutes } from './router'

// Stores
export { useAuthStore } from './stores/auth'

// Components
export { default as EmailInput } from './components/auth/EmailInput.vue'
export { default as TokenInput } from './components/auth/TokenInput.vue'

// Views
export { default as LoginView } from './views/Login.vue'
export { default as DashboardView } from './views/Dashboard.vue'

// Types
export type { User, AuthState, TokenRequestResponse, TokenValidationResponse } from './types'

// Plugin installation function for Vue app
export function installGuardian(app: any) {
  // Register global components if needed
  app.component('GuardianEmailInput', () => import('./components/auth/EmailInput.vue'))
  app.component('GuardianTokenInput', () => import('./components/auth/TokenInput.vue'))
}

// Default export for convenience
export default {
  layerInfo,
  install: installGuardian,
}
