import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { apiClient } from '@/composables/useApi'

// User type definition
interface User {
  id: string
  email: string
  name?: string
  is_active?: boolean
  created_at?: string
}

/**
 * Authentication store
 * Manages user authentication state and actions
 *
 * Note: This is a stub implementation for Sprint 1.
 * Full authentication logic will be implemented in Sprint 2.
 */
export const useAuthStore = defineStore('auth', () => {
  // State
  const user = ref<User | null>(null)
  const isAuthenticated = ref<boolean>(false)
  const loading = ref<boolean>(false)
  const error = ref<string | null>(null)
  const requestedEmail = ref<string | null>(null)
  const accessToken = ref<string | null>(null)

  // Getters
  const isLoggedIn = computed(() => isAuthenticated.value && user.value !== null)

  /**
   * Logout user
   * Clear session and redirect to login
   */
  const logout = async (): Promise<void> => {
    try {
      // Call backend logout endpoint (best practice, even though JWT is stateless)
      if (accessToken.value) {
        await apiClient.post('/api/auth/logout')
      }
    } catch {
      // Ignore errors, just clear local state
    } finally {
      // Clear all auth state
      user.value = null
      isAuthenticated.value = false
      accessToken.value = null
      error.value = null
      requestedEmail.value = null

      // Clear localStorage
      if (typeof window !== 'undefined') {
        localStorage.removeItem('access_token')
        localStorage.removeItem('user')
      }
    }
  }

  /**
   * Refresh JWT token
   * Extend session before expiry
   */
  const refreshToken = async (): Promise<void> => {
    loading.value = true

    try {
      const response = await apiClient.post('/api/auth/refresh')

      // Update token and user
      accessToken.value = response.data.access_token
      user.value = response.data.user

      // Update localStorage
      if (typeof window !== 'undefined') {
        localStorage.setItem('access_token', response.data.access_token)
        localStorage.setItem('user', JSON.stringify(response.data.user))
      }
    } catch (err: unknown) {
      // Token refresh failed, logout user
      await logout()
      error.value = 'Session expired. Please login again.'
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Check authentication status
   * Verify JWT is still valid
   */
  const checkAuth = async (): Promise<boolean> => {
    if (!accessToken.value) {
      return false
    }

    try {
      // Call /me endpoint to verify token
      const response = await apiClient.get('/api/auth/me')
      user.value = response.data
      isAuthenticated.value = true
      return true
    } catch (err) {
      // Token invalid, clear session
      await logout()
      return false
    }
  }

  /**
   * Request token
   * Send email with 6-digit verification code
   * Sprint 2 Story 8 implementation
   */
  const requestToken = async (email: string): Promise<void> => {
    loading.value = true
    error.value = null

    try {
      const response = await apiClient.post('/api/auth/request-token', { email })

      // Store masked email for display
      requestedEmail.value = response.data.email || email

      // Success - token sent to email
      // Note: Response doesn't contain the actual token for security
      return response.data
    } catch (err: unknown) {
      const axiosError = err as { response?: { data?: { detail?: string } } }
      error.value = axiosError.response?.data?.detail || 'Failed to request token'
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Validate token
   * Verify 6-digit token and establish JWT session
   * Sprint 2 Story 9 implementation
   */
  const validateToken = async (email: string, token: string): Promise<void> => {
    loading.value = true
    error.value = null

    try {
      const response = await apiClient.post('/api/auth/validate-token', {
        email,
        token
      })

      // Store user and JWT token
      user.value = response.data.user
      isAuthenticated.value = true
      accessToken.value = response.data.access_token

      // Store token in localStorage for persistence
      if (typeof window !== 'undefined') {
        localStorage.setItem('access_token', response.data.access_token)
        localStorage.setItem('user', JSON.stringify(response.data.user))
      }

      return response.data
    } catch (err: unknown) {
      const axiosError = err as { response?: { data?: { detail?: string } } }
      error.value = axiosError.response?.data?.detail || 'Token validation failed'
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Initialize authentication from localStorage
   * Check for existing JWT token on app start
   */
  const initAuth = (): void => {
    if (typeof window !== 'undefined') {
      const token = localStorage.getItem('access_token')
      const userJson = localStorage.getItem('user')

      if (token && userJson) {
        try {
          accessToken.value = token
          user.value = JSON.parse(userJson)
          isAuthenticated.value = true
        } catch (err) {
          // Invalid stored data, clear it
          localStorage.removeItem('access_token')
          localStorage.removeItem('user')
        }
      }
    }
  }

  return {
    // State
    user,
    isAuthenticated,
    loading,
    error,
    requestedEmail,
    accessToken,

    // Getters
    isLoggedIn,

    // Actions
    logout,
    refreshToken,
    checkAuth,
    requestToken,
    validateToken,
    initAuth
  }
})
