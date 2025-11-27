/**
 * Global TypeScript type definitions
 */

// User type
export interface User {
  id: string
  email: string
  name?: string
  createdAt?: string
  lastLogin?: string
}

// Authentication types
export interface LoginRequest {
  email: string
}

export interface TokenValidationRequest {
  email: string
  token: string
}

export interface AuthResponse {
  user: User
  token: string
  expiresAt: string
}

// API response types
export interface ApiResponse<T = any> {
  data: T
  message?: string
  success: boolean
}

export interface ApiError {
  message: string
  code?: string
  status?: number
  details?: Record<string, any>
}

// Router meta type
declare module 'vue-router' {
  interface RouteMeta {
    requiresAuth?: boolean
    title?: string
  }
}

// Environment variables type
declare global {
  interface ImportMetaEnv {
    readonly VITE_API_BASE_URL: string
    readonly VITE_APP_NAME: string
    readonly VITE_BRAND_PRIMARY_COLOR: string
    readonly VITE_BRAND_LOGO_URL: string
    readonly VITE_TOKEN_LENGTH: string
  }

  interface ImportMeta {
    readonly env: ImportMetaEnv
  }
}

export {}
