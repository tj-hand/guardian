import axios, { AxiosError, type AxiosInstance, type AxiosRequestConfig, type AxiosResponse } from 'axios'
import { ref } from 'vue'

// API response type
export interface ApiResponse<T = any> {
  data: T
  message?: string
  success: boolean
}

// API error type
export interface ApiError {
  message: string
  code?: string
  status?: number
}

/**
 * Create axios instance with base configuration
 */
const createApiClient = (): AxiosInstance => {
  const client = axios.create({
    baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
    timeout: 30000,
    headers: {
      'Content-Type': 'application/json'
    }
  })

  // Request interceptor - Add authentication token if available
  client.interceptors.request.use(
    (config) => {
      // Get token from localStorage
      const token = localStorage.getItem('access_token')

      if (token) {
        config.headers.Authorization = `Bearer ${token}`
      }

      return config
    },
    (error) => {
      return Promise.reject(error)
    }
  )

  // Response interceptor - Handle common errors
  client.interceptors.response.use(
    (response) => {
      return response
    },
    async (error: AxiosError) => {
      // Handle authentication errors
      if (error.response?.status === 401) {
        // Token expired or invalid
        // Clear auth and redirect to login
        localStorage.removeItem('access_token')
        localStorage.removeItem('user')

        // Redirect to login (only if not already there)
        if (window.location.pathname !== '/login') {
          window.location.href = '/login'
        }
      }

      // Handle server errors
      if (error.response?.status && error.response.status >= 500) {
        console.error('Server error:', error)
      }

      return Promise.reject(error)
    }
  )

  return client
}

// Create singleton API client instance
const apiClient = createApiClient()

/**
 * API composable for making HTTP requests
 * Provides reactive loading and error state management
 */
export const useApi = () => {
  const loading = ref(false)
  const error = ref<ApiError | null>(null)

  /**
   * Make GET request
   */
  const get = async <T = any>(
    url: string,
    config?: AxiosRequestConfig
  ): Promise<T> => {
    loading.value = true
    error.value = null

    try {
      const response: AxiosResponse<T> = await apiClient.get(url, config)
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
  const post = async <T = any>(
    url: string,
    data?: any,
    config?: AxiosRequestConfig
  ): Promise<T> => {
    loading.value = true
    error.value = null

    try {
      const response: AxiosResponse<T> = await apiClient.post(url, data, config)
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
  const put = async <T = any>(
    url: string,
    data?: any,
    config?: AxiosRequestConfig
  ): Promise<T> => {
    loading.value = true
    error.value = null

    try {
      const response: AxiosResponse<T> = await apiClient.put(url, data, config)
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
  const del = async <T = any>(
    url: string,
    config?: AxiosRequestConfig
  ): Promise<T> => {
    loading.value = true
    error.value = null

    try {
      const response: AxiosResponse<T> = await apiClient.delete(url, config)
      return response.data
    } catch (err) {
      error.value = handleError(err)
      throw error.value
    } finally {
      loading.value = false
    }
  }

  /**
   * Handle API errors
   */
  const handleError = (err: unknown): ApiError => {
    if (axios.isAxiosError(err)) {
      const axiosError = err as AxiosError<{ message?: string; detail?: string }>

      return {
        message: axiosError.response?.data?.message ||
                 axiosError.response?.data?.detail ||
                 axiosError.message ||
                 'An unexpected error occurred',
        code: axiosError.code,
        status: axiosError.response?.status
      }
    }

    return {
      message: err instanceof Error ? err.message : 'An unexpected error occurred'
    }
  }

  return {
    loading,
    error,
    get,
    post,
    put,
    del
  }
}

// Export the API client for direct use if needed
export { apiClient }
