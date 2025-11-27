import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

// Route definitions with meta information
const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'Home',
    component: () => import('@/views/Home.vue'),
    meta: {
      requiresAuth: false,
      title: 'Home'
    }
  },
  {
    path: '/login',
    name: 'login',
    component: () => import('@/views/Login.vue'),
    meta: {
      requiresAuth: false,
      title: 'Login'
    }
  },
  {
    path: '/dashboard',
    name: 'dashboard',
    component: () => import('@/views/Dashboard.vue'),
    meta: {
      requiresAuth: true,
      title: 'Dashboard'
    }
  }
]

// Create router instance
const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes
})

// Navigation guard for authentication
router.beforeEach(async (to, _from, next) => {
  const authStore = useAuthStore()
  const requiresAuth = to.matched.some(record => record.meta.requiresAuth)

  // Update page title
  document.title = to.meta.title
    ? `${to.meta.title} - ${import.meta.env.VITE_APP_NAME || 'Email Token Auth'}`
    : import.meta.env.VITE_APP_NAME || 'Email Token Auth'

  if (requiresAuth) {
    // Route requires authentication
    if (!authStore.isAuthenticated) {
      // Try to restore session from localStorage
      authStore.initAuth()

      if (!authStore.isAuthenticated) {
        // No valid session, redirect to login
        next({ name: 'login', query: { redirect: to.fullPath } })
        return
      }

      // Verify token is still valid
      const isValid = await authStore.checkAuth()
      if (!isValid) {
        next({ name: 'login', query: { redirect: to.fullPath } })
        return
      }
    }

    // User is authenticated
    next()
  } else {
    // Route doesn't require auth
    if (to.name === 'login' && authStore.isAuthenticated) {
      // Already logged in, redirect to dashboard
      next({ name: 'dashboard' })
      return
    }

    next()
  }
})

export default router
