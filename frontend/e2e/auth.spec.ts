import { test, expect, Page } from '@playwright/test'

/**
 * E2E Tests for Email Token Authentication Flow
 *
 * These tests cover the complete authentication user journey:
 * - Token request
 * - Token validation
 * - Session management
 * - Logout
 */

// Test configuration
const TEST_EMAIL = 'test@example.com'
const VALID_TOKEN = '123456'
const INVALID_TOKEN = '999999'
const API_BASE_URL = 'http://localhost:8000'

/**
 * Helper function to fill in the 6-digit token
 * The UI uses 6 separate inputs with class 'token-digit'
 */
async function fillTokenInputs(page: Page, token: string) {
  const digits = token.split('')
  const tokenInputs = page.locator('.token-digit')

  for (let i = 0; i < digits.length; i++) {
    await tokenInputs.nth(i).fill(digits[i])
  }
}

/**
 * Helper function to wait for token input screen to appear
 * This happens after email submission when URL changes to include email query param
 */
async function waitForTokenInputScreen(page: Page) {
  // Wait for URL to contain email query param (redirect after email submission)
  await expect(page).toHaveURL(/email=/, { timeout: 10000 })

  // Wait for the first token digit input to be visible
  await expect(page.locator('.token-digit').first()).toBeVisible({ timeout: 5000 })
}

test.describe('Authentication Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to login page before each test
    await page.goto('/login')
  })

  test('should allow user to request token and login successfully', async ({ page }) => {
    // Intercept API call to request token
    await page.route(`${API_BASE_URL}/api/v1/auth/request-token`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          message: 'Token sent to email',
          email: TEST_EMAIL
        })
      })
    })

    // Intercept API call to validate token
    await page.route(`${API_BASE_URL}/api/v1/auth/validate-token`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          access_token: 'mock-jwt-token',
          token_type: 'bearer',
          expires_in: 604800,
          user: {
            id: 1,
            email: TEST_EMAIL,
            created_at: new Date().toISOString()
          }
        })
      })
    })

    // Step 1: Enter email
    const emailInput = page.locator('input[type="email"]')
    await expect(emailInput).toBeVisible()
    await emailInput.fill(TEST_EMAIL)

    // Click submit button
    await page.click('button[type="submit"]')

    // Step 2: Wait for token input screen to appear (after redirect)
    await waitForTokenInputScreen(page)

    // Step 3: Enter 6-digit token (should auto-submit)
    await fillTokenInputs(page, VALID_TOKEN)

    // Step 4: Verify redirect to dashboard
    await expect(page).toHaveURL(/\/dashboard/, { timeout: 5000 })

    // Step 5: Verify user is authenticated (check for page heading or content)
    await expect(page.locator('h1, h2, [role="main"]')).toBeVisible()
  })

  test('should show error for invalid token', async ({ page }) => {
    // Intercept API call to request token
    await page.route(`${API_BASE_URL}/api/v1/auth/request-token`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          message: 'Token sent to email',
          email: TEST_EMAIL
        })
      })
    })

    // Intercept API call to validate token with error
    await page.route(`${API_BASE_URL}/api/v1/auth/validate-token`, async (route) => {
      await route.fulfill({
        status: 401,
        contentType: 'application/json',
        body: JSON.stringify({
          detail: 'Invalid or expired token'
        })
      })
    })

    // Enter email
    await page.fill('input[type="email"]', TEST_EMAIL)
    await page.click('button[type="submit"]')

    // Wait for token input screen
    await waitForTokenInputScreen(page)

    // Enter invalid token
    await fillTokenInputs(page, INVALID_TOKEN)

    // Verify error message appears (look for error in .error-message container)
    await expect(page.locator('.error-message')).toContainText(/invalid/i, { timeout: 5000 })
  })

  test('should show error for expired token', async ({ page }) => {
    // Intercept API call to request token
    await page.route(`${API_BASE_URL}/api/v1/auth/request-token`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          message: 'Token sent to email',
          email: TEST_EMAIL
        })
      })
    })

    // Intercept API call to validate token with expiry error
    await page.route(`${API_BASE_URL}/api/v1/auth/validate-token`, async (route) => {
      await route.fulfill({
        status: 401,
        contentType: 'application/json',
        body: JSON.stringify({
          detail: 'Token has expired'
        })
      })
    })

    // Enter email
    await page.fill('input[type="email"]', TEST_EMAIL)
    await page.click('button[type="submit"]')

    // Wait for token input screen
    await waitForTokenInputScreen(page)

    // Enter token
    await fillTokenInputs(page, VALID_TOKEN)

    // Verify error message appears (look for error in .error-message container)
    await expect(page.locator('.error-message')).toContainText(/expired/i, { timeout: 5000 })
  })

  test('should auto-submit token when 6 digits are entered', async ({ page }) => {
    let validateTokenCalled = false

    // Intercept API call to request token
    await page.route(`${API_BASE_URL}/api/v1/auth/request-token`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          message: 'Token sent to email',
          email: TEST_EMAIL
        })
      })
    })

    // Intercept API call to validate token
    await page.route(`${API_BASE_URL}/api/v1/auth/validate-token`, async (route) => {
      validateTokenCalled = true
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          access_token: 'mock-jwt-token',
          token_type: 'bearer',
          expires_in: 604800,
          user: {
            id: 1,
            email: TEST_EMAIL,
            created_at: new Date().toISOString()
          }
        })
      })
    })

    // Enter email
    await page.fill('input[type="email"]', TEST_EMAIL)
    await page.click('button[type="submit"]')

    // Wait for token input screen
    await waitForTokenInputScreen(page)

    // Enter 6 digits one by one - this should trigger auto-submit
    await fillTokenInputs(page, VALID_TOKEN)

    // Wait for auto-submit (validate endpoint should be called)
    await page.waitForTimeout(1000)

    // Verify auto-submit occurred
    expect(validateTokenCalled).toBe(true)
  })
})
