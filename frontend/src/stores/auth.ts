/**
 * Guardian Authentication Store
 *
 * Pinia store for managing authentication state.
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { apiClient } from '@/composables/useApi'
import type { User, TokenRequestResponse, TokenValidationResponse } from '@/types'

export const useAuthStore = defineStore('auth', () => {
  // State
  const user = ref<User | null>(null)
  const isAuthenticated = ref(false)
  const loading = ref(false)
  const error = ref<string | null>(null)
  const requestedEmail = ref<string | null>(null)
  const accessToken = ref<string | null>(null)

  // Getters
  const isLoggedIn = computed(() => isAuthenticated.value && user.value !== null)

  /**
   * Initialize auth from localStorage
   */
  function initAuth(): void {
    if (typeof window !== 'undefined') {
      const token = localStorage.getItem('access_token')
      const userJson = localStorage.getItem('user')

      if (token && userJson) {
        try {
          accessToken.value = token
          user.value = JSON.parse(userJson)
          isAuthenticated.value = true
        } catch {
          localStorage.removeItem('access_token')
          localStorage.removeItem('user')
        }
      }
    }
  }

  /**
   * Request 6-digit token via email
   */
  async function requestToken(email: string): Promise<TokenRequestResponse> {
    loading.value = true
    error.value = null

    try {
      const response = await apiClient.post<TokenRequestResponse>(
        '/auth/request-token',
        { email }
      )

      requestedEmail.value = response.data.email || email
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
   * Validate 6-digit token and create session
   */
  async function validateToken(email: string, token: string): Promise<TokenValidationResponse> {
    loading.value = true
    error.value = null

    try {
      const response = await apiClient.post<TokenValidationResponse>(
        '/auth/validate-token',
        { email, token }
      )

      // Store auth data
      user.value = response.data.user
      isAuthenticated.value = true
      accessToken.value = response.data.access_token

      // Persist to localStorage
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
   * Verify current session is valid
   */
  async function checkAuth(): Promise<boolean> {
    if (!accessToken.value) {
      return false
    }

    try {
      const response = await apiClient.get<User>('/auth/me')
      user.value = response.data
      isAuthenticated.value = true
      return true
    } catch {
      await logout()
      return false
    }
  }

  /**
   * Refresh JWT token
   */
  async function refreshToken(): Promise<void> {
    loading.value = true

    try {
      const response = await apiClient.post<TokenValidationResponse>('/auth/refresh')

      accessToken.value = response.data.access_token
      user.value = response.data.user

      if (typeof window !== 'undefined') {
        localStorage.setItem('access_token', response.data.access_token)
        localStorage.setItem('user', JSON.stringify(response.data.user))
      }
    } catch {
      await logout()
      error.value = 'Session expired. Please login again.'
      throw new Error('Session expired')
    } finally {
      loading.value = false
    }
  }

  /**
   * Logout user
   */
  async function logout(): Promise<void> {
    try {
      if (accessToken.value) {
        await apiClient.post('/auth/logout')
      }
    } catch {
      // Ignore errors, just clear state
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
   * Clear error state
   */
  function clearError(): void {
    error.value = null
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
    initAuth,
    requestToken,
    validateToken,
    checkAuth,
    refreshToken,
    logout,
    clearError,
  }
})
