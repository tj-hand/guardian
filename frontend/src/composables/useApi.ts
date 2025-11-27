/**
 * Guardian API Client Composable
 *
 * Centralized axios instance for API calls following Evoke patterns.
 */

import axios, { type AxiosInstance, type AxiosError } from 'axios'

// Create axios instance
const apiClient: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor - add auth token
apiClient.interceptors.request.use(
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
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    // Handle 401 - redirect to login
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token')
      localStorage.removeItem('user')

      // Only redirect if not already on login page
      if (!window.location.pathname.includes('/login')) {
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)

export { apiClient }

/**
 * Composable for API calls with loading and error state
 */
export function useApi() {
  const get = async <T>(url: string): Promise<T> => {
    const response = await apiClient.get<T>(url)
    return response.data
  }

  const post = async <T, D = unknown>(url: string, data?: D): Promise<T> => {
    const response = await apiClient.post<T>(url, data)
    return response.data
  }

  const put = async <T, D = unknown>(url: string, data?: D): Promise<T> => {
    const response = await apiClient.put<T>(url, data)
    return response.data
  }

  const del = async <T>(url: string): Promise<T> => {
    const response = await apiClient.delete<T>(url)
    return response.data
  }

  return {
    get,
    post,
    put,
    delete: del,
    client: apiClient,
  }
}
