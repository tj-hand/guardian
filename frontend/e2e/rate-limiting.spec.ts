import { test, expect } from '@playwright/test'

/**
 * E2E Tests for Rate Limiting
 *
 * These tests verify that rate limiting is enforced:
 * - Maximum 3 token requests per 15 minutes per email (default)
 * - Error message displayed when rate limit exceeded
 * - Users can try again after window expires
 */

const TEST_EMAIL = 'test@example.com'
const API_BASE_URL = 'http://localhost:8000'

test.describe('Rate Limiting', () => {
  test('should enforce rate limiting after 3 token requests', async ({ page }) => {
    let requestCount = 0

    // Intercept API calls to track requests
    await page.route(`${API_BASE_URL}/api/auth/request-token`, async (route) => {
      requestCount++

      if (requestCount <= 3) {
        // First 3 requests succeed
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            message: 'Token sent to email',
            email: TEST_EMAIL
          })
        })
      } else {
        // 4th request fails with rate limit error
        await route.fulfill({
          status: 429,
          contentType: 'application/json',
          body: JSON.stringify({
            detail: 'Too many requests. Please try again later.'
          })
        })
      }
    })

    await page.goto('/login')

    // Make 3 successful requests
    for (let i = 0; i < 3; i++) {
      await page.fill('input[type="email"]', TEST_EMAIL)
      await page.click('button[type="submit"]')

      // Wait for success message or token input
      await page.waitForTimeout(500)

      // Go back to email input (simulate user requesting new token)
      await page.goto('/login')
    }

    // 4th request should be rate limited
    await page.fill('input[type="email"]', TEST_EMAIL)
    await page.click('button[type="submit"]')

    // Verify rate limit error message appears in error container
    await expect(page.locator('.error-message')).toContainText(/too many|rate limit|try again/i, { timeout: 3000 })

    // Verify request count
    expect(requestCount).toBe(4)
  })

  test('should show appropriate error message for rate limit', async ({ page }) => {
    // Intercept API call to return rate limit error immediately
    await page.route(`${API_BASE_URL}/api/auth/request-token`, async (route) => {
      await route.fulfill({
        status: 429,
        contentType: 'application/json',
        body: JSON.stringify({
          detail: 'Rate limit exceeded. Please wait 15 minutes before trying again.'
        })
      })
    })

    await page.goto('/login')

    // Try to request token
    await page.fill('input[type="email"]', TEST_EMAIL)
    await page.click('button[type="submit"]')

    // Verify error message in error container
    await expect(page.locator('.error-message')).toContainText(/rate limit/i)
    await expect(page.locator('.error-message')).toContainText(/15 minutes/i)
  })

  test('should allow requests after rate limit window expires', async ({ page }) => {
    let requestCount = 0
    let rateLimitExpired = false

    // Intercept API calls
    await page.route(`${API_BASE_URL}/api/auth/request-token`, async (route) => {
      requestCount++

      if (!rateLimitExpired && requestCount > 3) {
        // Rate limited
        await route.fulfill({
          status: 429,
          body: JSON.stringify({
            detail: 'Rate limit exceeded. Please wait.'
          })
        })
      } else {
        // Success
        await route.fulfill({
          status: 200,
          body: JSON.stringify({
            message: 'Token sent to email',
            email: TEST_EMAIL
          })
        })
      }
    })

    await page.goto('/login')

    // Make 3 successful requests first
    for (let i = 0; i < 3; i++) {
      await page.fill('input[type="email"]', TEST_EMAIL)
      await page.click('button[type="submit"]')
      await page.waitForTimeout(500)
      await page.goto('/login')
    }

    // 4th request should be rate limited - don't navigate away
    await page.fill('input[type="email"]', TEST_EMAIL)
    await page.click('button[type="submit"]')

    // Verify rate limit message in error container
    await expect(page.locator('.error-message')).toContainText(/rate limit/i)

    // Simulate rate limit window expiring
    rateLimitExpired = true

    // Try again (should succeed now)
    await page.goto('/login')
    await page.fill('input[type="email"]', TEST_EMAIL)
    await page.click('button[type="submit"]')

    // Should NOT show rate limit error
    await expect(page.locator('.error-message')).not.toBeVisible({ timeout: 2000 })
  })

  test('should rate limit per email address', async ({ page }) => {
    const email1 = 'user1@example.com'
    const email2 = 'user2@example.com'
    const requestCounts = new Map<string, number>()

    // Intercept API calls and track per email
    await page.route(`${API_BASE_URL}/api/auth/request-token`, async (route) => {
      const requestBody = route.request().postDataJSON()
      const email = requestBody.email

      const count = (requestCounts.get(email) || 0) + 1
      requestCounts.set(email, count)

      if (count <= 3) {
        await route.fulfill({
          status: 200,
          body: JSON.stringify({ message: 'Token sent', email })
        })
      } else {
        await route.fulfill({
          status: 429,
          body: JSON.stringify({ detail: 'Rate limit exceeded' })
        })
      }
    })

    await page.goto('/login')

    // Make 3 requests for email1
    for (let i = 0; i < 3; i++) {
      await page.fill('input[type="email"]', email1)
      await page.click('button[type="submit"]')
      await page.waitForTimeout(300)
      await page.goto('/login')
    }

    // 4th request for email1 should fail
    await page.fill('input[type="email"]', email1)
    await page.click('button[type="submit"]')
    await expect(page.locator('.error-message')).toContainText(/rate limit/i)

    // But email2 should still work (different email)
    await page.goto('/login')
    await page.fill('input[type="email"]', email2)
    await page.click('button[type="submit"]')

    // Should NOT show rate limit error for email2 (should see success message instead)
    await page.waitForTimeout(1000)
    await expect(page.locator('.error-message')).not.toBeVisible()
  })
})
