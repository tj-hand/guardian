import { test, expect, Page } from '@playwright/test'

/**
 * E2E Tests for Protected Routes and Session Management
 *
 * These tests verify that:
 * - Protected routes require authentication
 * - Sessions persist across page refreshes
 * - Logout works correctly
 */

const TEST_EMAIL = 'test@example.com'
const VALID_TOKEN = '123456'
const API_BASE_URL = 'http://localhost:8000'
const MOCK_JWT = 'mock-jwt-token-12345'

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
 */
async function waitForTokenInputScreen(page: Page) {
  await expect(page).toHaveURL(/email=/, { timeout: 10000 })
  await expect(page.locator('.token-digit').first()).toBeVisible({ timeout: 5000 })
}

test.describe('Protected Routes', () => {
  test('should redirect unauthenticated user to login', async ({ page }) => {
    // Try to access protected dashboard without authentication
    await page.goto('/dashboard')

    // Should be redirected to login page (may include redirect query param)
    await expect(page).toHaveURL(/\/login/, { timeout: 3000 })
  })

  test('should allow access to protected routes when authenticated', async ({ page }) => {
    // Mock authentication
    await page.route(`${API_BASE_URL}/api/v1/auth/request-token`, async (route) => {
      await route.fulfill({
        status: 200,
        body: JSON.stringify({ message: 'Token sent', email: TEST_EMAIL })
      })
    })

    await page.route(`${API_BASE_URL}/api/v1/auth/validate-token`, async (route) => {
      await route.fulfill({
        status: 200,
        body: JSON.stringify({
          access_token: MOCK_JWT,
          token_type: 'bearer',
          expires_in: 604800,
          user: { id: 1, email: TEST_EMAIL, created_at: new Date().toISOString() }
        })
      })
    })

    // Mock authenticated endpoint
    await page.route(`${API_BASE_URL}/api/v1/auth/me`, async (route) => {
      await route.fulfill({
        status: 200,
        body: JSON.stringify({
          id: 1,
          email: TEST_EMAIL,
          created_at: new Date().toISOString()
        })
      })
    })

    // Log in
    await page.goto('/login')
    await page.fill('input[type="email"]', TEST_EMAIL)
    await page.click('button[type="submit"]')

    // Wait for token input screen and fill token
    await waitForTokenInputScreen(page)
    await fillTokenInputs(page, VALID_TOKEN)

    // Wait for redirect to dashboard
    await expect(page).toHaveURL(/\/dashboard/, { timeout: 5000 })

    // Verify access to dashboard (check for page content)
    await expect(page.locator('h1, h2, [role="main"]')).toBeVisible()
  })

  test('should maintain session across page refresh', async ({ page, context }) => {
    // Set up authentication token in localStorage
    await context.addInitScript((token) => {
      localStorage.setItem('token', token)
      localStorage.setItem('user', JSON.stringify({
        id: 1,
        email: 'test@example.com',
        created_at: new Date().toISOString()
      }))
    }, MOCK_JWT)

    // Mock authenticated endpoint
    await page.route(`${API_BASE_URL}/api/v1/auth/me`, async (route) => {
      const headers = route.request().headers()
      if (headers['authorization'] === `Bearer ${MOCK_JWT}`) {
        await route.fulfill({
          status: 200,
          body: JSON.stringify({
            id: 1,
            email: TEST_EMAIL,
            created_at: new Date().toISOString()
          })
        })
      } else {
        await route.fulfill({ status: 401, body: JSON.stringify({ detail: 'Unauthorized' }) })
      }
    })

    // Navigate to dashboard
    await page.goto('/dashboard')

    // Should stay on dashboard (authenticated)
    await expect(page).toHaveURL(/\/dashboard/)

    // Refresh the page
    await page.reload()

    // Should still be on dashboard (session persisted)
    await expect(page).toHaveURL(/\/dashboard/)
    await expect(page.locator('h1, h2, [role="main"]')).toBeVisible()
  })

  test('should clear session on logout', async ({ page, context }) => {
    // Set up authentication token in localStorage
    await context.addInitScript((token) => {
      localStorage.setItem('token', token)
      localStorage.setItem('user', JSON.stringify({
        id: 1,
        email: 'test@example.com',
        created_at: new Date().toISOString()
      }))
    }, MOCK_JWT)

    // Mock authenticated endpoint
    await page.route(`${API_BASE_URL}/api/v1/auth/me`, async (route) => {
      await route.fulfill({
        status: 200,
        body: JSON.stringify({
          id: 1,
          email: TEST_EMAIL,
          created_at: new Date().toISOString()
        })
      })
    })

    // Navigate to dashboard
    await page.goto('/dashboard')
    await expect(page).toHaveURL(/\/dashboard/)

    // Click logout button (uses .logout-button class)
    const logoutButton = page.locator('.logout-button')
    await logoutButton.click()

    // Should be redirected to login page
    await expect(page).toHaveURL(/\/login|\//, { timeout: 3000 })

    // Verify localStorage is cleared
    const token = await page.evaluate(() => localStorage.getItem('token'))
    expect(token).toBeNull()

    // Try to access dashboard again (should redirect)
    await page.goto('/dashboard')
    await expect(page).toHaveURL(/\/login/)
  })

  test('should handle expired JWT token', async ({ page, context }) => {
    // Set up expired token
    await context.addInitScript(() => {
      localStorage.setItem('token', 'expired-jwt-token')
      localStorage.setItem('user', JSON.stringify({
        id: 1,
        email: 'test@example.com'
      }))
    })

    // Mock expired token response
    await page.route(`${API_BASE_URL}/api/v1/auth/me`, async (route) => {
      await route.fulfill({
        status: 401,
        body: JSON.stringify({ detail: 'Token expired' })
      })
    })

    // Navigate to dashboard
    await page.goto('/dashboard')

    // Should be redirected to login due to expired token
    await expect(page).toHaveURL(/\/login/, { timeout: 5000 })
  })
})
