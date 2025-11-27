/**
 * Guardian Routes - Layer 1 Authentication Routes
 *
 * These routes are exported to be registered in the Evoke router.
 * The navigation guards use the auth store for protection.
 */

import type { RouteRecordRaw, NavigationGuardNext, RouteLocationNormalized } from 'vue-router'

/**
 * Guardian authentication routes
 * To be merged into the main Evoke router
 */
export const guardianRoutes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'guardian-login',
    component: () => import('../views/Login.vue'),
    meta: {
      requiresAuth: false,
      title: 'Login',
      layer: 'guardian',
    },
  },
  {
    path: '/dashboard',
    name: 'guardian-dashboard',
    component: () => import('../views/Dashboard.vue'),
    meta: {
      requiresAuth: true,
      title: 'Dashboard',
      layer: 'guardian',
    },
  },
]

/**
 * Navigation guard for Guardian routes
 * Should be registered in Evoke's router.beforeEach
 */
export async function guardianNavigationGuard(
  to: RouteLocationNormalized,
  _from: RouteLocationNormalized,
  next: NavigationGuardNext
) {
  // Only handle guardian routes
  if (to.meta.layer !== 'guardian') {
    next()
    return
  }

  const { useAuthStore } = await import('../stores/auth')
  const authStore = useAuthStore()

  const requiresAuth = to.matched.some((record) => record.meta.requiresAuth)

  if (requiresAuth && !authStore.isAuthenticated) {
    // Try to restore session
    authStore.initAuth()

    if (!authStore.isAuthenticated) {
      next({ name: 'guardian-login', query: { redirect: to.fullPath } })
      return
    }

    // Verify token is still valid
    const isValid = await authStore.checkAuth()
    if (!isValid) {
      next({ name: 'guardian-login', query: { redirect: to.fullPath } })
      return
    }
  }

  // Redirect authenticated users away from login
  if (to.name === 'guardian-login' && authStore.isAuthenticated) {
    next({ name: 'guardian-dashboard' })
    return
  }

  next()
}

export default guardianRoutes
