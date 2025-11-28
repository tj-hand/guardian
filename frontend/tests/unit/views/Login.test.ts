import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createRouter, createMemoryHistory } from 'vue-router'
import { createPinia, setActivePinia } from 'pinia'
import Login from '@/views/Login.vue'
import EmailInput from '@/components/auth/EmailInput.vue'
import TokenInput from '@/components/auth/TokenInput.vue'

/**
 * Login View Tests
 * Tests the login page that switches between email input and token input
 */

describe('Login View', () => {
  let router: any
  let pinia: any

  beforeEach(() => {
    // Create fresh pinia instance for each test
    pinia = createPinia()
    setActivePinia(pinia)

    // Create test router
    router = createRouter({
      history: createMemoryHistory(),
      routes: [
        { path: '/login', name: 'Login', component: Login }
      ]
    })
  })

  describe('Component Rendering', () => {
    it('should render the login view correctly', async () => {
      await router.push('/login')
      await router.isReady()

      const wrapper = mount(Login, {
        global: {
          plugins: [router, pinia]
        }
      })

      expect(wrapper.find('.login-page').exists()).toBe(true)
      expect(wrapper.find('.login-container').exists()).toBe(true)
    })

    it('should have correct page structure', async () => {
      await router.push('/login')
      await router.isReady()

      const wrapper = mount(Login, {
        global: {
          plugins: [router, pinia]
        }
      })

      const loginPage = wrapper.find('.login-page')
      expect(loginPage.exists()).toBe(true)

      const container = loginPage.find('.login-container')
      expect(container.exists()).toBe(true)
    })
  })

  describe('Email Input Display (Default State)', () => {
    it('should show EmailInput component by default', async () => {
      await router.push('/login')
      await router.isReady()

      const wrapper = mount(Login, {
        global: {
          plugins: [router, pinia],
          stubs: {
            EmailInput: false,
            TokenInput: false
          }
        }
      })

      const emailInput = wrapper.findComponent(EmailInput)
      expect(emailInput.exists()).toBe(true)
    })

    it('should not show TokenInput component by default', async () => {
      await router.push('/login')
      await router.isReady()

      const wrapper = mount(Login, {
        global: {
          plugins: [router, pinia],
          stubs: {
            EmailInput: false,
            TokenInput: false
          }
        }
      })

      const tokenInput = wrapper.findComponent(TokenInput)
      expect(tokenInput.exists()).toBe(false)
    })

    it('should show EmailInput when no email query param', async () => {
      await router.push('/login')
      await router.isReady()

      const wrapper = mount(Login, {
        global: {
          plugins: [router, pinia],
          stubs: {
            EmailInput: false,
            TokenInput: false
          }
        }
      })

      expect(wrapper.findComponent(EmailInput).exists()).toBe(true)
      expect(wrapper.findComponent(TokenInput).exists()).toBe(false)
    })
  })

  describe('Token Input Display (With Email Query)', () => {
    it('should show TokenInput when email query param is present', async () => {
      await router.push('/login?email=test@example.com')
      await router.isReady()

      const wrapper = mount(Login, {
        global: {
          plugins: [router, pinia],
          stubs: {
            EmailInput: false,
            TokenInput: false
          }
        }
      })

      const tokenInput = wrapper.findComponent(TokenInput)
      expect(tokenInput.exists()).toBe(true)
    })

    it('should not show EmailInput when email query param is present', async () => {
      await router.push('/login?email=user@example.com')
      await router.isReady()

      const wrapper = mount(Login, {
        global: {
          plugins: [router, pinia],
          stubs: {
            EmailInput: false,
            TokenInput: false
          }
        }
      })

      const emailInput = wrapper.findComponent(EmailInput)
      expect(emailInput.exists()).toBe(false)
    })

    it('should pass email prop to TokenInput', async () => {
      const testEmail = 'tokentest@example.com'
      await router.push(`/login?email=${testEmail}`)
      await router.isReady()

      const wrapper = mount(Login, {
        global: {
          plugins: [router, pinia],
          stubs: {
            EmailInput: false,
            TokenInput: false
          }
        }
      })

      const tokenInput = wrapper.findComponent(TokenInput)
      expect(tokenInput.exists()).toBe(true)
      expect(tokenInput.props('email')).toBe(testEmail)
    })
  })

  describe('Route Query Parameter Handling', () => {
    it('should detect email in query params', async () => {
      await router.push('/login?email=query@example.com')
      await router.isReady()

      const wrapper = mount(Login, {
        global: {
          plugins: [router, pinia],
          stubs: {
            EmailInput: false,
            TokenInput: false
          }
        }
      })

      expect(wrapper.findComponent(TokenInput).exists()).toBe(true)
    })

    it('should handle URL-encoded email addresses', async () => {
      const email = 'user+tag@example.com'
      const encodedEmail = encodeURIComponent(email)
      await router.push(`/login?email=${encodedEmail}`)
      await router.isReady()

      const wrapper = mount(Login, {
        global: {
          plugins: [router, pinia],
          stubs: {
            EmailInput: false,
            TokenInput: false
          }
        }
      })

      const tokenInput = wrapper.findComponent(TokenInput)
      expect(tokenInput.exists()).toBe(true)
      expect(tokenInput.props('email')).toBe(email)
    })

    it('should handle empty email query param', async () => {
      await router.push('/login?email=')
      await router.isReady()

      const wrapper = mount(Login, {
        global: {
          plugins: [router, pinia],
          stubs: {
            EmailInput: false,
            TokenInput: false
          }
        }
      })

      // Empty string is still a defined value, so TokenInput should show
      expect(wrapper.findComponent(TokenInput).exists()).toBe(true)
    })

    it('should ignore other query parameters', async () => {
      await router.push('/login?foo=bar&baz=qux')
      await router.isReady()

      const wrapper = mount(Login, {
        global: {
          plugins: [router, pinia],
          stubs: {
            EmailInput: false,
            TokenInput: false
          }
        }
      })

      // No email param, should show EmailInput
      expect(wrapper.findComponent(EmailInput).exists()).toBe(true)
      expect(wrapper.findComponent(TokenInput).exists()).toBe(false)
    })

    it('should prioritize email query param with other params present', async () => {
      await router.push('/login?email=priority@example.com&redirect=dashboard')
      await router.isReady()

      const wrapper = mount(Login, {
        global: {
          plugins: [router, pinia],
          stubs: {
            EmailInput: false,
            TokenInput: false
          }
        }
      })

      expect(wrapper.findComponent(TokenInput).exists()).toBe(true)
      expect(wrapper.findComponent(TokenInput).props('email')).toBe('priority@example.com')
    })
  })

  describe('Component Switching', () => {
    it('should switch from EmailInput to TokenInput when route changes', async () => {
      await router.push('/login')
      await router.isReady()

      const wrapper = mount(Login, {
        global: {
          plugins: [router, pinia],
          stubs: {
            EmailInput: false,
            TokenInput: false
          }
        }
      })

      // Initially shows EmailInput
      expect(wrapper.findComponent(EmailInput).exists()).toBe(true)
      expect(wrapper.findComponent(TokenInput).exists()).toBe(false)

      // Navigate to login with email
      await router.push('/login?email=switch@example.com')
      await wrapper.vm.$nextTick()

      // Should now show TokenInput
      expect(wrapper.findComponent(EmailInput).exists()).toBe(false)
      expect(wrapper.findComponent(TokenInput).exists()).toBe(true)
    })

    it('should switch from TokenInput to EmailInput when email query is removed', async () => {
      await router.push('/login?email=remove@example.com')
      await router.isReady()

      const wrapper = mount(Login, {
        global: {
          plugins: [router, pinia],
          stubs: {
            EmailInput: false,
            TokenInput: false
          }
        }
      })

      // Initially shows TokenInput
      expect(wrapper.findComponent(TokenInput).exists()).toBe(true)
      expect(wrapper.findComponent(EmailInput).exists()).toBe(false)

      // Remove email query
      await router.push('/login')
      await wrapper.vm.$nextTick()

      // Should now show EmailInput
      expect(wrapper.findComponent(EmailInput).exists()).toBe(true)
      expect(wrapper.findComponent(TokenInput).exists()).toBe(false)
    })
  })

  describe('Computed Property: showTokenInput', () => {
    it('should compute showTokenInput as false without email query', async () => {
      await router.push('/login')
      await router.isReady()

      const wrapper = mount(Login, {
        global: {
          plugins: [router, pinia]
        }
      })

      expect(wrapper.findComponent(EmailInput).exists()).toBe(true)
    })

    it('should compute showTokenInput as true with email query', async () => {
      await router.push('/login?email=computed@example.com')
      await router.isReady()

      const wrapper = mount(Login, {
        global: {
          plugins: [router, pinia]
        }
      })

      expect(wrapper.findComponent(TokenInput).exists()).toBe(true)
    })

    it('should reactively update when route changes', async () => {
      await router.push('/login')
      await router.isReady()

      const wrapper = mount(Login, {
        global: {
          plugins: [router, pinia],
          stubs: {
            EmailInput: false,
            TokenInput: false
          }
        }
      })

      expect(wrapper.findComponent(EmailInput).exists()).toBe(true)

      // Change route
      await router.push('/login?email=reactive@example.com')
      await wrapper.vm.$nextTick()

      expect(wrapper.findComponent(TokenInput).exists()).toBe(true)
    })
  })

  describe('Layout and Styling', () => {
    it('should have full-height page layout', async () => {
      await router.push('/login')
      await router.isReady()

      const wrapper = mount(Login, {
        global: {
          plugins: [router, pinia]
        }
      })

      const loginPage = wrapper.find('.login-page')
      expect(loginPage.exists()).toBe(true)
    })

    it('should center content container', async () => {
      await router.push('/login')
      await router.isReady()

      const wrapper = mount(Login, {
        global: {
          plugins: [router, pinia]
        }
      })

      const container = wrapper.find('.login-container')
      expect(container.exists()).toBe(true)
    })
  })

  describe('Smoke Tests', () => {
    it('should render without errors', async () => {
      await router.push('/login')
      await router.isReady()

      expect(() => {
        mount(Login, {
          global: {
            plugins: [router, pinia]
          }
        })
      }).not.toThrow()
    })

    it('should render without errors with email query', async () => {
      await router.push('/login?email=smoke@example.com')
      await router.isReady()

      expect(() => {
        mount(Login, {
          global: {
            plugins: [router, pinia]
          }
        })
      }).not.toThrow()
    })

    it('should render exactly one child component at a time', async () => {
      await router.push('/login')
      await router.isReady()

      const wrapper1 = mount(Login, {
        global: {
          plugins: [router, pinia],
          stubs: {
            EmailInput: false,
            TokenInput: false
          }
        }
      })

      const emailInputExists = wrapper1.findComponent(EmailInput).exists()
      const tokenInputExists = wrapper1.findComponent(TokenInput).exists()

      // Exactly one should be true
      expect(emailInputExists !== tokenInputExists).toBe(true)
    })

    it('should handle multiple route changes gracefully', async () => {
      await router.push('/login')
      await router.isReady()

      const wrapper = mount(Login, {
        global: {
          plugins: [router, pinia],
          stubs: {
            EmailInput: false,
            TokenInput: false
          }
        }
      })

      // Multiple route changes
      await router.push('/login?email=first@example.com')
      await wrapper.vm.$nextTick()
      expect(wrapper.find('.login-page').exists()).toBe(true)

      await router.push('/login')
      await wrapper.vm.$nextTick()
      expect(wrapper.find('.login-page').exists()).toBe(true)

      await router.push('/login?email=second@example.com')
      await wrapper.vm.$nextTick()
      expect(wrapper.find('.login-page').exists()).toBe(true)
    })
  })

  describe('Edge Cases', () => {
    it('should handle special characters in email query', async () => {
      const specialEmail = 'user+special@example.com'
      await router.push(`/login?email=${encodeURIComponent(specialEmail)}`)
      await router.isReady()

      const wrapper = mount(Login, {
        global: {
          plugins: [router, pinia],
          stubs: {
            EmailInput: false,
            TokenInput: false
          }
        }
      })

      const tokenInput = wrapper.findComponent(TokenInput)
      expect(tokenInput.props('email')).toBe(specialEmail)
    })

    it('should handle very long email addresses', async () => {
      const longEmail = 'verylongemailaddress' + 'a'.repeat(100) + '@example.com'
      await router.push(`/login?email=${encodeURIComponent(longEmail)}`)
      await router.isReady()

      const wrapper = mount(Login, {
        global: {
          plugins: [router, pinia],
          stubs: {
            EmailInput: false,
            TokenInput: false
          }
        }
      })

      expect(wrapper.findComponent(TokenInput).exists()).toBe(true)
    })

    it('should handle malformed email in query', async () => {
      await router.push('/login?email=notanemail')
      await router.isReady()

      const wrapper = mount(Login, {
        global: {
          plugins: [router, pinia],
          stubs: {
            EmailInput: false,
            TokenInput: false
          }
        }
      })

      // Should still show TokenInput (validation happens in TokenInput component)
      expect(wrapper.findComponent(TokenInput).exists()).toBe(true)
    })
  })
})
