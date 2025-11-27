/**
 * Guardian TypeScript Types
 */

// User type
export interface User {
  id: string
  email: string
  is_active: boolean
  created_at: string
}

// API Response types
export interface TokenRequestResponse {
  message: string
  email: string
  expires_in_minutes: number
}

export interface TokenValidationResponse {
  access_token: string
  token_type: string
  expires_in: number
  user: User
}

export interface LogoutResponse {
  message: string
}

// API Error type
export interface ApiError {
  detail: string | Record<string, unknown>
  message?: string
}

// Auth state
export interface AuthState {
  user: User | null
  isAuthenticated: boolean
  loading: boolean
  error: string | null
  requestedEmail: string | null
  accessToken: string | null
}
