import { Page, BrowserContext } from '@playwright/test'

/**
 * E2E Test Helpers for Authentication
 *
 * Common utilities for setting up test scenarios
 */

export const API_BASE_URL = 'http://localhost:8000'

export interface MockUser {
  id: number
  email: string
  created_at: string
}

export interface MockAuthResponse {
  access_token: string
  token_type: string
  expires_in: number
  user: MockUser
}

/**
 * Set up authenticated session in browser context
 */
export async function setAuthenticatedSession(
  context: BrowserContext,
  token: string = 'mock-jwt-token',
  user?: Partial<MockUser>
) {
  const defaultUser: MockUser = {
    id: 1,
    email: 'test@example.com',
    created_at: new Date().toISOString(),
    ...user
  }

  await context.addInitScript(
    ({ token, user }) => {
      localStorage.setItem('token', token)
      localStorage.setItem('user', JSON.stringify(user))
    },
    { token, user: defaultUser }
  )
}

/**
 * Mock successful token request
 */
export async function mockTokenRequest(page: Page, email: string) {
  await page.route(`${API_BASE_URL}/api/v1/auth/request-token`, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        message: 'Token sent to email',
        email
      })
    })
  })
}

/**
 * Mock successful token validation
 */
export async function mockTokenValidation(
  page: Page,
  email: string,
  token: string = 'mock-jwt-token'
) {
  await page.route(`${API_BASE_URL}/api/v1/auth/validate-token`, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        access_token: token,
        token_type: 'bearer',
        expires_in: 604800,
        user: {
          id: 1,
          email,
          created_at: new Date().toISOString()
        }
      })
    })
  })
}

/**
 * Mock failed token validation
 */
export async function mockTokenValidationError(
  page: Page,
  errorMessage: string = 'Invalid or expired token',
  statusCode: number = 401
) {
  await page.route(`${API_BASE_URL}/api/v1/auth/validate-token`, async (route) => {
    await route.fulfill({
      status: statusCode,
      contentType: 'application/json',
      body: JSON.stringify({
        detail: errorMessage
      })
    })
  })
}

/**
 * Mock authenticated user endpoint
 */
export async function mockAuthenticatedUser(
  page: Page,
  user?: Partial<MockUser>,
  token: string = 'mock-jwt-token'
) {
  const defaultUser: MockUser = {
    id: 1,
    email: 'test@example.com',
    created_at: new Date().toISOString(),
    ...user
  }

  await page.route(`${API_BASE_URL}/api/v1/auth/me`, async (route) => {
    const headers = route.request().headers()
    if (headers['authorization'] === `Bearer ${token}`) {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(defaultUser)
      })
    } else {
      await route.fulfill({
        status: 401,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'Unauthorized' })
      })
    }
  })
}

/**
 * Mock rate limit error
 */
export async function mockRateLimitError(page: Page) {
  await page.route(`${API_BASE_URL}/api/v1/auth/request-token`, async (route) => {
    await route.fulfill({
      status: 429,
      contentType: 'application/json',
      body: JSON.stringify({
        detail: 'Too many requests. Please try again later.'
      })
    })
  })
}

/**
 * Complete login flow with mocked API
 */
export async function loginWithMockedAPI(
  page: Page,
  email: string,
  token: string = '123456',
  jwtToken: string = 'mock-jwt-token'
) {
  // Mock API calls
  await mockTokenRequest(page, email)
  await mockTokenValidation(page, email, jwtToken)
  await mockAuthenticatedUser(page, { email }, jwtToken)

  // Navigate to login
  await page.goto('/')

  // Enter email
  await page.fill('input[type="email"]', email)
  await page.click('button[type="submit"]')

  // Enter token
  await page.fill('input[type="text"][maxlength="6"]', token)

  // Wait for redirect to dashboard
  await page.waitForURL(/\/dashboard/, { timeout: 5000 })
}

/**
 * Clear authentication from browser
 */
export async function clearAuth(page: Page) {
  await page.evaluate(() => {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
  })
}

/**
 * Get authentication token from browser
 */
export async function getAuthToken(page: Page): Promise<string | null> {
  return await page.evaluate(() => localStorage.getItem('token'))
}

/**
 * Get user data from browser
 */
export async function getAuthUser(page: Page): Promise<MockUser | null> {
  const userStr = await page.evaluate(() => localStorage.getItem('user'))
  return userStr ? JSON.parse(userStr) : null
}
