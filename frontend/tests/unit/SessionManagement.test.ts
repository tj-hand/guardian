import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useAuthStore } from '@/stores/auth'
import { apiClient } from '@/composables/useApi'

// Mock apiClient
vi.mock('@/composables/useApi', () => ({
  apiClient: {
    post: vi.fn(),
    get: vi.fn()
  }
}))

describe('Session Management', () => {
  beforeEach(() => {
    // Create a fresh pinia instance for each test
    setActivePinia(createPinia())

    // Clear localStorage
    localStorage.clear()

    // Clear all mocks
    vi.clearAllMocks()
  })

  afterEach(() => {
    localStorage.clear()
  })

  describe('Auth Store - logout', () => {
    it('should clear all auth state on logout', async () => {
      const authStore = useAuthStore()

      // Set up initial authenticated state
      authStore.user = { id: '1', email: 'test@example.com' }
      authStore.isAuthenticated = true
      authStore.accessToken = 'test-token'
      localStorage.setItem('access_token', 'test-token')
      localStorage.setItem('user', JSON.stringify({ id: '1', email: 'test@example.com' }))

      // Mock successful logout API call
      vi.mocked(apiClient.post).mockResolvedValueOnce({ data: {} })

      // Call logout
      await authStore.logout()

      // Verify all state is cleared
      expect(authStore.user).toBeNull()
      expect(authStore.isAuthenticated).toBe(false)
      expect(authStore.accessToken).toBeNull()
      expect(authStore.error).toBeNull()
      expect(authStore.requestedEmail).toBeNull()

      // Verify localStorage is cleared
      expect(localStorage.getItem('access_token')).toBeNull()
      expect(localStorage.getItem('user')).toBeNull()
    })

    it('should clear state even if logout API call fails', async () => {
      const authStore = useAuthStore()

      // Set up initial authenticated state
      authStore.user = { id: '1', email: 'test@example.com' }
      authStore.isAuthenticated = true
      authStore.accessToken = 'test-token'

      // Mock failed logout API call
      vi.mocked(apiClient.post).mockRejectedValueOnce(new Error('API Error'))

      // Call logout
      await authStore.logout()

      // Verify all state is cleared despite API error
      expect(authStore.user).toBeNull()
      expect(authStore.isAuthenticated).toBe(false)
      expect(authStore.accessToken).toBeNull()
    })

    it('should not call logout API if no token exists', async () => {
      const authStore = useAuthStore()

      // No token set
      authStore.accessToken = null

      // Call logout
      await authStore.logout()

      // Verify logout API was not called
      expect(apiClient.post).not.toHaveBeenCalled()
    })
  })

  describe('Auth Store - refreshToken', () => {
    it('should update token and user on successful refresh', async () => {
      const authStore = useAuthStore()

      // Set up initial state
      authStore.accessToken = 'old-token'

      const mockResponse = {
        data: {
          access_token: 'new-token',
          user: { id: '1', email: 'test@example.com', is_active: true }
        }
      }

      // Mock successful refresh
      vi.mocked(apiClient.post).mockResolvedValueOnce(mockResponse)

      // Call refreshToken
      await authStore.refreshToken()

      // Verify state is updated
      expect(authStore.accessToken).toBe('new-token')
      expect(authStore.user).toEqual(mockResponse.data.user)

      // Verify localStorage is updated
      expect(localStorage.getItem('access_token')).toBe('new-token')
      expect(localStorage.getItem('user')).toBe(JSON.stringify(mockResponse.data.user))
    })

    it('should logout user if refresh fails', async () => {
      const authStore = useAuthStore()

      // Set up initial state
      authStore.accessToken = 'old-token'
      authStore.user = { id: '1', email: 'test@example.com' }
      authStore.isAuthenticated = true

      // Mock failed refresh
      vi.mocked(apiClient.post).mockRejectedValueOnce(new Error('Refresh failed'))

      // Call refreshToken and expect it to throw
      await expect(authStore.refreshToken()).rejects.toThrow()

      // Verify user is logged out
      expect(authStore.user).toBeNull()
      expect(authStore.isAuthenticated).toBe(false)
      expect(authStore.accessToken).toBeNull()
      expect(authStore.error).toBe('Session expired. Please login again.')
    })

    it('should set loading state during refresh', async () => {
      const authStore = useAuthStore()

      authStore.accessToken = 'old-token'

      const mockResponse = {
        data: {
          access_token: 'new-token',
          user: { id: '1', email: 'test@example.com' }
        }
      }

      let loadingDuringCall = false

      vi.mocked(apiClient.post).mockImplementationOnce(async () => {
        loadingDuringCall = authStore.loading
        return mockResponse
      })

      await authStore.refreshToken()

      expect(loadingDuringCall).toBe(true)
      expect(authStore.loading).toBe(false)
    })
  })

  describe('Auth Store - checkAuth', () => {
    it('should return false if no token exists', async () => {
      const authStore = useAuthStore()

      // No token
      authStore.accessToken = null

      // Call checkAuth
      const result = await authStore.checkAuth()

      // Verify result
      expect(result).toBe(false)
      expect(apiClient.get).not.toHaveBeenCalled()
    })

    it('should validate token and return true if valid', async () => {
      const authStore = useAuthStore()

      // Set token
      authStore.accessToken = 'valid-token'

      const mockUser = {
        id: '1',
        email: 'test@example.com',
        is_active: true,
        created_at: '2024-01-01T00:00:00Z'
      }

      // Mock successful validation
      vi.mocked(apiClient.get).mockResolvedValueOnce({ data: mockUser })

      // Call checkAuth
      const result = await authStore.checkAuth()

      // Verify result
      expect(result).toBe(true)
      expect(authStore.user).toEqual(mockUser)
      expect(authStore.isAuthenticated).toBe(true)
      expect(apiClient.get).toHaveBeenCalledWith('/api/auth/me')
    })

    it('should logout and return false if token is invalid', async () => {
      const authStore = useAuthStore()

      // Set up initial authenticated state
      authStore.accessToken = 'invalid-token'
      authStore.user = { id: '1', email: 'test@example.com' }
      authStore.isAuthenticated = true

      // Mock failed validation
      vi.mocked(apiClient.get).mockRejectedValueOnce(new Error('Unauthorized'))

      // Call checkAuth
      const result = await authStore.checkAuth()

      // Verify result
      expect(result).toBe(false)
      expect(authStore.user).toBeNull()
      expect(authStore.isAuthenticated).toBe(false)
      expect(authStore.accessToken).toBeNull()
    })
  })

  describe('Auth Store - initAuth', () => {
    it('should restore user and token from localStorage', () => {
      const authStore = useAuthStore()

      const mockUser = { id: '1', email: 'test@example.com' }
      const mockToken = 'stored-token'

      // Set localStorage
      localStorage.setItem('access_token', mockToken)
      localStorage.setItem('user', JSON.stringify(mockUser))

      // Call initAuth
      authStore.initAuth()

      // Verify state is restored
      expect(authStore.accessToken).toBe(mockToken)
      expect(authStore.user).toEqual(mockUser)
      expect(authStore.isAuthenticated).toBe(true)
    })

    it('should handle missing localStorage data gracefully', () => {
      const authStore = useAuthStore()

      // No localStorage data
      localStorage.clear()

      // Call initAuth
      authStore.initAuth()

      // Verify state remains unauthenticated
      expect(authStore.accessToken).toBeNull()
      expect(authStore.user).toBeNull()
      expect(authStore.isAuthenticated).toBe(false)
    })

    it('should clear invalid JSON from localStorage', () => {
      const authStore = useAuthStore()

      // Set invalid JSON
      localStorage.setItem('access_token', 'valid-token')
      localStorage.setItem('user', 'invalid-json{')

      // Call initAuth
      authStore.initAuth()

      // Verify localStorage is cleared
      expect(localStorage.getItem('access_token')).toBeNull()
      expect(localStorage.getItem('user')).toBeNull()
      expect(authStore.isAuthenticated).toBe(false)
    })
  })

  describe('Session Persistence', () => {
    it('should persist session across page reloads', async () => {
      const authStore = useAuthStore()

      const mockUser = { id: '1', email: 'test@example.com' }
      const mockToken = 'session-token'

      // Simulate successful login
      authStore.user = mockUser
      authStore.isAuthenticated = true
      authStore.accessToken = mockToken
      localStorage.setItem('access_token', mockToken)
      localStorage.setItem('user', JSON.stringify(mockUser))

      // Create new store instance (simulating page reload)
      const newStore = useAuthStore()
      newStore.initAuth()

      // Verify session is restored
      expect(newStore.accessToken).toBe(mockToken)
      expect(newStore.user).toEqual(mockUser)
      expect(newStore.isAuthenticated).toBe(true)
    })

    it('should clear session on logout and not restore', async () => {
      const authStore = useAuthStore()

      // Set up authenticated state
      authStore.user = { id: '1', email: 'test@example.com' }
      authStore.isAuthenticated = true
      authStore.accessToken = 'test-token'
      localStorage.setItem('access_token', 'test-token')
      localStorage.setItem('user', JSON.stringify({ id: '1', email: 'test@example.com' }))

      // Mock logout
      vi.mocked(apiClient.post).mockResolvedValueOnce({ data: {} })

      // Logout
      await authStore.logout()

      // Create new store instance (simulating page reload)
      const newStore = useAuthStore()
      newStore.initAuth()

      // Verify session is not restored
      expect(newStore.accessToken).toBeNull()
      expect(newStore.user).toBeNull()
      expect(newStore.isAuthenticated).toBe(false)
    })
  })

  describe('Integration - Full Auth Flow', () => {
    it('should handle complete authentication lifecycle', async () => {
      const authStore = useAuthStore()

      // 1. Initial state - unauthenticated
      expect(authStore.isAuthenticated).toBe(false)

      // 2. Simulate token validation (login)
      const mockUser = { id: '1', email: 'test@example.com', is_active: true }
      vi.mocked(apiClient.post).mockResolvedValueOnce({
        data: {
          access_token: 'new-token',
          user: mockUser
        }
      })

      await authStore.validateToken('test@example.com', '123456')

      // 3. Verify authenticated state
      expect(authStore.isAuthenticated).toBe(true)
      expect(authStore.user).toEqual(mockUser)
      expect(authStore.accessToken).toBe('new-token')

      // 4. Verify checkAuth with valid token
      vi.mocked(apiClient.get).mockResolvedValueOnce({ data: mockUser })
      const checkResult = await authStore.checkAuth()
      expect(checkResult).toBe(true)

      // 5. Logout
      vi.mocked(apiClient.post).mockResolvedValueOnce({ data: {} })
      await authStore.logout()

      // 6. Verify logged out state
      expect(authStore.isAuthenticated).toBe(false)
      expect(authStore.user).toBeNull()
      expect(authStore.accessToken).toBeNull()
    })
  })
})
