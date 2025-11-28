/**
 * Guardian Layer 1 Frontend Exports
 *
 * This file provides the public API for the Guardian authentication service
 * to be consumed by the Evoke application (Layer 0).
 *
 * Evoke can import Guardian routes, stores, composables, and components
 * and integrate them into its own Vue application.
 */

import type { App } from 'vue'
import type { Router } from 'vue-router'
import { createPinia } from 'pinia'

// =============================================================================
// ROUTE EXPORTS
// =============================================================================

/**
 * Guardian route definitions
 * Evoke can register these routes in its own router
 */
export { default as guardianRoutes } from './router'

// =============================================================================
// STORE EXPORTS
// =============================================================================

/**
 * Authentication store for managing user sessions and tokens
 */
export { useAuthStore } from './stores/auth'

// =============================================================================
// COMPOSABLE EXPORTS
// =============================================================================

/**
 * White-label theming composable (CRITICAL)
 * Manages environment-based branding customization
 */
export { useTheme } from './composables/useTheme'

/**
 * API client composable with axios configuration
 */
export { useApi } from './composables/useApi'

/**
 * Export the raw API client for direct use
 */
export { apiClient } from './composables/useApi'

/**
 * Token countdown timer composable
 */
export { useTokenTimer } from './composables/useTokenTimer'

// =============================================================================
// VIEW/COMPONENT EXPORTS
// =============================================================================

/**
 * Login view with email input and token verification
 */
export { default as LoginView } from './views/Login.vue'

/**
 * Authenticated dashboard view
 */
export { default as DashboardView } from './views/Dashboard.vue'

/**
 * Home view
 */
export { default as HomeView } from './views/Home.vue'

/**
 * Authentication components
 */
export { default as EmailInput } from './components/auth/EmailInput.vue'
export { default as TokenInput } from './components/auth/TokenInput.vue'
export { default as CountdownTimer } from './components/auth/CountdownTimer.vue'

/**
 * Layout components
 */
export { default as AppLayout } from './components/layout/AppLayout.vue'
export { default as AppHeader } from './components/layout/AppHeader.vue'
export { default as AppFooter } from './components/layout/AppFooter.vue'

// =============================================================================
// CONFIGURATION EXPORTS
// =============================================================================

/**
 * White-label branding configuration (CRITICAL)
 * Exports BrandingConfig interface, getBrandingConfig, and applyBrandingTheme
 */
export {
  getBrandingConfig,
  applyBrandingTheme,
  type BrandingConfig
} from './config/branding'

// =============================================================================
// TYPE EXPORTS
// =============================================================================

/**
 * TypeScript type definitions matching backend schemas
 */
export type {
  User,
  LoginRequest,
  TokenValidationRequest,
  AuthResponse,
  ApiResponse,
  ApiError
} from './types'

// =============================================================================
// VUE PLUGIN - GUARDIAN INSTALLER
// =============================================================================

/**
 * Guardian plugin installer for Evoke
 *
 * Usage in Evoke's main.ts:
 * ```typescript
 * import { installGuardian } from '@guardian/frontend'
 *
 * const app = createApp(App)
 * const { pinia } = installGuardian(app)
 *
 * // Register Guardian routes in Evoke's router
 * import { guardianRoutes } from '@guardian/frontend'
 * router.addRoute(guardianRoutes)
 * ```
 *
 * @param app - Vue application instance
 * @param options - Optional configuration
 * @returns Object containing Pinia instance and other utilities
 */
export async function installGuardian(
  app: App,
  options?: {
    router?: Router
    initTheme?: boolean
  }
): Promise<{ pinia: ReturnType<typeof createPinia> }> {
  // Install Pinia if not already installed
  const pinia = createPinia()
  app.use(pinia)

  // Initialize theme if requested (default: true)
  if (options?.initTheme !== false) {
    const { useTheme } = await import('./composables/useTheme')
    const { initializeTheme } = useTheme()
    initializeTheme()
  }

  // Additional Guardian setup can be added here
  // For example: global error handlers, API interceptors, etc.

  return {
    pinia,
    // Additional utilities can be returned here
  }
}

// =============================================================================
// STANDALONE APP ENTRYPOINT (for development/testing)
// =============================================================================

/**
 * Create standalone Guardian app
 * This is useful for development and testing Guardian in isolation
 *
 * @returns Vue app instance
 */
export async function createGuardianApp() {
  const { createApp } = await import('vue')
  const App = (await import('./App.vue')).default
  const router = (await import('./router')).default

  const app = createApp(App)

  // Install Guardian
  const { pinia } = await installGuardian(app, {
    router,
    initTheme: true
  })

  // Use router
  app.use(router)

  return {
    app,
    router,
    pinia
  }
}
