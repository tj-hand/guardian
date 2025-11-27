/**
 * Guardian API Composable
 *
 * This module provides API access for Guardian authentication.
 * It can use Evoke's client when available, or fall back to its own axios instance.
 */

import axios, { type AxiosInstance, type AxiosError } from 'axios'

// Evoke client reference (set by Evoke when mounting Guardian)
let evokeClient: AxiosInstance | null = null

/**
 * Set the Evoke client for Guardian to use
 * Called by Evoke when mounting Guardian layer
 */
export function setEvokeClient(client: AxiosInstance) {
  evokeClient = client
}

// Fallback axios instance (used when running standalone or Evoke client not set)
const fallbackClient: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor - add auth token
fallbackClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// Response interceptor - handle errors
fallbackClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token')
      localStorage.removeItem('user')

      if (typeof window !== 'undefined' && !window.location.pathname.includes('/login')) {
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)

/**
 * Get the API client (Evoke's or fallback)
 */
export function getApiClient(): AxiosInstance {
  return evokeClient || fallbackClient
}

// Export for direct use
export const apiClient = {
  get client() {
    return getApiClient()
  },
  async get<T>(url: string) {
    return getApiClient().get<T>(url)
  },
  async post<T>(url: string, data?: unknown) {
    return getApiClient().post<T>(url, data)
  },
  async put<T>(url: string, data?: unknown) {
    return getApiClient().put<T>(url, data)
  },
  async delete<T>(url: string) {
    return getApiClient().delete<T>(url)
  },
}

/**
 * Composable for API calls
 */
export function useApi() {
  const client = getApiClient()

  return {
    get: async <T>(url: string): Promise<T> => {
      const response = await client.get<T>(url)
      return response.data
    },
    post: async <T, D = unknown>(url: string, data?: D): Promise<T> => {
      const response = await client.post<T>(url, data)
      return response.data
    },
    put: async <T, D = unknown>(url: string, data?: D): Promise<T> => {
      const response = await client.put<T>(url, data)
      return response.data
    },
    delete: async <T>(url: string): Promise<T> => {
      const response = await client.delete<T>(url)
      return response.data
    },
    client,
  }
}
