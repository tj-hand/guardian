/**
 * Guardian API Composable
 * Uses Evoke JS Client (Layer 0) for API communication
 *
 * Architecture flow:
 * Guardian Frontend → Evoke → Bolt → Manifast → Guardian Backend
 */

import { ref } from 'vue'

// =============================================================================
// EVOKE CLIENT TYPE DECLARATIONS
// =============================================================================

/**
 * Evoke API Response type
 */
interface EvokeApiResponse<T> {
  data: T
  status: number
  headers: Record<string, string>
  duration?: number
}

/**
 * Evoke API Error type
 */
interface EvokeApiError {
  message: string
  code: string
  status?: number
  response?: unknown
  isNetworkError(): boolean
  isTimeout(): boolean
  toJSON(): Record<string, unknown>
}

/**
 * Evoke Client Configuration
 */
interface EvokeConfig {
  baseURL: string
  timeout?: number
  withCredentials?: boolean
  headers?: Record<string, string>
  tokenStorage?: {
    type: 'localStorage' | 'sessionStorage' | 'memory'
    accessTokenKey?: string
    refreshTokenKey?: string
  }
  retry?: {
    maxRetries?: number
    baseDelay?: number
    maxDelay?: number
  } | false
  onAuthError?: (error: EvokeApiError) => void
  onNetworkError?: (error: EvokeApiError) => void
  debug?: boolean
}

/**
 * Evoke Client Interface
 */
interface EvokeClient {
  get<T>(url: string, options?: { params?: Record<string, unknown> }): Promise<EvokeApiResponse<T>>
  post<T, D = unknown>(url: string, data?: D, options?: { params?: Record<string, unknown> }): Promise<EvokeApiResponse<T>>
  put<T, D = unknown>(url: string, data?: D, options?: { params?: Record<string, unknown> }): Promise<EvokeApiResponse<T>>
  patch<T, D = unknown>(url: string, data?: D, options?: { params?: Record<string, unknown> }): Promise<EvokeApiResponse<T>>
  delete<T>(url: string, options?: { params?: Record<string, unknown> }): Promise<EvokeApiResponse<T>>
  publicGet<T>(url: string, options?: { params?: Record<string, unknown> }): Promise<EvokeApiResponse<T>>
  publicPost<T, D = unknown>(url: string, data?: D, options?: { params?: Record<string, unknown> }): Promise<EvokeApiResponse<T>>
  setToken(token: string): void
  clearToken(): void
  getToken(): string | null
  hasToken(): boolean
}

/**
 * Global Evoke object (loaded via script tag)
 */
interface EvokeGlobal {
  createClient(config: EvokeConfig): EvokeClient
  EvokeClient: new (config: EvokeConfig) => EvokeClient
}

// Declare global Evoke
declare global {
  interface Window {
    Evoke?: EvokeGlobal
  }
}

// =============================================================================
// API TYPES (Exported)
// =============================================================================

/**
 * API response type (for backward compatibility)
 */
export interface ApiResponse<T = unknown> {
  data: T
  message?: string
  success: boolean
}

/**
 * API error type
 */
export interface ApiError {
  message: string
  code?: string
  status?: number
}

// =============================================================================
// EVOKE CLIENT INITIALIZATION
// =============================================================================

/**
 * Create Evoke client instance
 * Uses Evoke JS client loaded via script tag for the layered architecture
 */
const createApiClient = (): EvokeClient => {
  // Check if Evoke is available (loaded via script tag)
  if (typeof window !== 'undefined' && window.Evoke) {
    const client = window.Evoke.createClient({
      // Evoke handles routing through the layered architecture
      // Requests go: Guardian → Evoke → Bolt → Manifast → Guardian Backend
      baseURL: import.meta.env.VITE_EVOKE_URL || '/evoke',
      timeout: 30000,
      withCredentials: true,
      tokenStorage: {
        type: 'localStorage',
        accessTokenKey: 'access_token',
        refreshTokenKey: 'refresh_token',
      },
      retry: {
        maxRetries: 3,
        baseDelay: 1000,
        maxDelay: 10000,
      },
      onAuthError: () => {
        // Clear local storage and redirect to login on 401
        localStorage.removeItem('access_token')
        localStorage.removeItem('user')
        if (window.location.pathname !== '/login') {
          window.location.href = '/login'
        }
      },
      debug: import.meta.env.DEV,
    })

    // Load existing token if available
    const existingToken = localStorage.getItem('access_token')
    if (existingToken) {
      client.setToken(existingToken)
    }

    return client
  }

  // Fallback: Create a minimal client that logs errors
  // This handles the case where Evoke script hasn't loaded yet
  console.warn('[Guardian] Evoke client not available. Ensure evoke.js is loaded.')

  const fallbackClient: EvokeClient = {
    async get<T>(): Promise<EvokeApiResponse<T>> {
      throw new Error('Evoke client not initialized')
    },
    async post<T>(): Promise<EvokeApiResponse<T>> {
      throw new Error('Evoke client not initialized')
    },
    async put<T>(): Promise<EvokeApiResponse<T>> {
      throw new Error('Evoke client not initialized')
    },
    async patch<T>(): Promise<EvokeApiResponse<T>> {
      throw new Error('Evoke client not initialized')
    },
    async delete<T>(): Promise<EvokeApiResponse<T>> {
      throw new Error('Evoke client not initialized')
    },
    async publicGet<T>(): Promise<EvokeApiResponse<T>> {
      throw new Error('Evoke client not initialized')
    },
    async publicPost<T>(): Promise<EvokeApiResponse<T>> {
      throw new Error('Evoke client not initialized')
    },
    setToken() {},
    clearToken() {},
    getToken() { return null },
    hasToken() { return false },
  }

  return fallbackClient
}

// Create singleton API client instance
let _apiClient: EvokeClient | null = null

/**
 * Get or create the API client instance
 * Lazy initialization to ensure Evoke script has loaded
 */
const getApiClient = (): EvokeClient => {
  if (!_apiClient) {
    _apiClient = createApiClient()
  }
  return _apiClient
}

// =============================================================================
// API CLIENT WRAPPER (for backward compatibility)
// =============================================================================

/**
 * API client wrapper that maintains backward compatibility
 * with the previous axios-based implementation
 */
export const apiClient = {
  /**
   * GET request
   */
  async get<T = unknown>(url: string, config?: { params?: Record<string, unknown> }): Promise<EvokeApiResponse<T>> {
    return getApiClient().get<T>(url, config)
  },

  /**
   * POST request
   */
  async post<T = unknown>(url: string, data?: unknown, config?: { params?: Record<string, unknown> }): Promise<EvokeApiResponse<T>> {
    return getApiClient().post<T>(url, data, config)
  },

  /**
   * PUT request
   */
  async put<T = unknown>(url: string, data?: unknown, config?: { params?: Record<string, unknown> }): Promise<EvokeApiResponse<T>> {
    return getApiClient().put<T>(url, data, config)
  },

  /**
   * DELETE request
   */
  async delete<T = unknown>(url: string, config?: { params?: Record<string, unknown> }): Promise<EvokeApiResponse<T>> {
    return getApiClient().delete<T>(url, config)
  },

  /**
   * Set authentication token
   */
  setToken(token: string): void {
    getApiClient().setToken(token)
  },

  /**
   * Clear authentication token
   */
  clearToken(): void {
    getApiClient().clearToken()
  },

  /**
   * Check if client has a token
   */
  hasToken(): boolean {
    return getApiClient().hasToken()
  },
}

// =============================================================================
// USE API COMPOSABLE
// =============================================================================

/**
 * API composable for making HTTP requests
 * Provides reactive loading and error state management
 *
 * @example
 * ```typescript
 * const { loading, error, get, post } = useApi()
 *
 * const users = await get<User[]>('/api/users')
 * const newUser = await post<User>('/api/users', { name: 'John' })
 * ```
 */
export const useApi = () => {
  const loading = ref(false)
  const error = ref<ApiError | null>(null)

  /**
   * Handle API errors
   */
  const handleError = (err: unknown): ApiError => {
    // Handle Evoke API errors
    if (err && typeof err === 'object' && 'code' in err) {
      const evokeError = err as EvokeApiError
      return {
        message: evokeError.message || 'An unexpected error occurred',
        code: evokeError.code,
        status: evokeError.status,
      }
    }

    // Handle standard errors
    if (err instanceof Error) {
      return {
        message: err.message,
      }
    }

    return {
      message: 'An unexpected error occurred',
    }
  }

  /**
   * Make GET request
   */
  const get = async <T = unknown>(
    url: string,
    config?: { params?: Record<string, unknown> }
  ): Promise<T> => {
    loading.value = true
    error.value = null

    try {
      const response = await apiClient.get<T>(url, config)
      return response.data
    } catch (err) {
      error.value = handleError(err)
      throw error.value
    } finally {
      loading.value = false
    }
  }

  /**
   * Make POST request
   */
  const post = async <T = unknown>(
    url: string,
    data?: unknown,
    config?: { params?: Record<string, unknown> }
  ): Promise<T> => {
    loading.value = true
    error.value = null

    try {
      const response = await apiClient.post<T>(url, data, config)
      return response.data
    } catch (err) {
      error.value = handleError(err)
      throw error.value
    } finally {
      loading.value = false
    }
  }

  /**
   * Make PUT request
   */
  const put = async <T = unknown>(
    url: string,
    data?: unknown,
    config?: { params?: Record<string, unknown> }
  ): Promise<T> => {
    loading.value = true
    error.value = null

    try {
      const response = await apiClient.put<T>(url, data, config)
      return response.data
    } catch (err) {
      error.value = handleError(err)
      throw error.value
    } finally {
      loading.value = false
    }
  }

  /**
   * Make DELETE request
   */
  const del = async <T = unknown>(
    url: string,
    config?: { params?: Record<string, unknown> }
  ): Promise<T> => {
    loading.value = true
    error.value = null

    try {
      const response = await apiClient.delete<T>(url, config)
      return response.data
    } catch (err) {
      error.value = handleError(err)
      throw error.value
    } finally {
      loading.value = false
    }
  }

  return {
    loading,
    error,
    get,
    post,
    put,
    del,
  }
}
