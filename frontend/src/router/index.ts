/**
 * Guardian Vue Router Configuration
 */

import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'Home',
    component: () => import('@/views/Home.vue'),
    meta: {
      requiresAuth: false,
      title: 'Home',
    },
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: {
      requiresAuth: false,
      title: 'Login',
    },
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: () => import('@/views/Dashboard.vue'),
    meta: {
      requiresAuth: true,
      title: 'Dashboard',
    },
  },
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
})

// Navigation guard
router.beforeEach(async (to, _from, next) => {
  const authStore = useAuthStore()
  const requiresAuth = to.matched.some((record) => record.meta.requiresAuth)

  // Update page title
  const appName = import.meta.env.VITE_APP_NAME || 'Guardian'
  document.title = to.meta.title ? `${to.meta.title} - ${appName}` : appName

  if (requiresAuth) {
    // Route requires authentication
    if (!authStore.isAuthenticated) {
      authStore.initAuth()

      if (!authStore.isAuthenticated) {
        next({ name: 'Login', query: { redirect: to.fullPath } })
        return
      }

      // Verify token is still valid
      const isValid = await authStore.checkAuth()
      if (!isValid) {
        next({ name: 'Login', query: { redirect: to.fullPath } })
        return
      }
    }
    next()
  } else {
    // Route doesn't require auth
    if (to.name === 'Login' && authStore.isAuthenticated) {
      next({ name: 'Dashboard' })
      return
    }
    next()
  }
})

export default router
