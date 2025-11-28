import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createRouter, createMemoryHistory } from 'vue-router'
import { createPinia, setActivePinia } from 'pinia'
import EmailInput from '@/components/auth/EmailInput.vue'
import { useAuthStore } from '@/stores/auth'

/**
 * EmailInput Component Tests
 * Sprint 2 Story 8: Email Input Component with Token Request
 */

describe('EmailInput Component', () => {
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
        { path: '/', name: 'Home', component: { template: '<div>Home</div>' } },
        { path: '/login', name: 'Login', component: { template: '<div>Login</div>' } }
      ]
    })
  })

  describe('Component Rendering', () => {
    it('should render the component correctly', () => {
      const wrapper = mount(EmailInput, {
        global: {
          plugins: [router, pinia]
        }
      })

      expect(wrapper.find('h2').text()).toBe('Login')
      expect(wrapper.find('.subtitle').text()).toBe('Enter your email to receive a verification code')
      expect(wrapper.find('input[type="email"]').exists()).toBe(true)
      expect(wrapper.find('button[type="submit"]').exists()).toBe(true)
    })

    it('should have email input with correct attributes', () => {
      const wrapper = mount(EmailInput, {
        global: {
          plugins: [router, pinia]
        }
      })

      const input = wrapper.find('input[type="email"]')
      expect(input.attributes('placeholder')).toBe('you@example.com')
      expect(input.attributes('autocomplete')).toBe('email')
      expect(input.attributes('autofocus')).toBeDefined()
    })
  })

  describe('Email Validation', () => {
    it('should show error for invalid email format', async () => {
      const wrapper = mount(EmailInput, {
        global: {
          plugins: [router, pinia]
        }
      })

      const input = wrapper.find('input[type="email"]')
      await input.setValue('invalid-email')

      expect(wrapper.find('.field-error').exists()).toBe(true)
      expect(wrapper.find('.field-error').text()).toBe('Please enter a valid email address')
    })

    it('should not show error for valid email', async () => {
      const wrapper = mount(EmailInput, {
        global: {
          plugins: [router, pinia]
        }
      })

      const input = wrapper.find('input[type="email"]')
      await input.setValue('test@example.com')

      expect(wrapper.find('.field-error').exists()).toBe(false)
    })

    it('should validate email with multiple domains', async () => {
      const wrapper = mount(EmailInput, {
        global: {
          plugins: [router, pinia]
        }
      })

      const input = wrapper.find('input[type="email"]')

      // Valid emails
      await input.setValue('user@example.com')
      expect(wrapper.find('.field-error').exists()).toBe(false)

      await input.setValue('user.name@example.co.uk')
      expect(wrapper.find('.field-error').exists()).toBe(false)

      await input.setValue('user+tag@example.com')
      expect(wrapper.find('.field-error').exists()).toBe(false)
    })
  })

  describe('Submit Button State', () => {
    it('should disable submit button when email is empty', () => {
      const wrapper = mount(EmailInput, {
        global: {
          plugins: [router, pinia]
        }
      })

      const button = wrapper.find('button[type="submit"]')
      expect(button.attributes('disabled')).toBeDefined()
    })

    it('should disable submit button when email is invalid', async () => {
      const wrapper = mount(EmailInput, {
        global: {
          plugins: [router, pinia]
        }
      })

      const input = wrapper.find('input[type="email"]')
      await input.setValue('invalid-email')

      const button = wrapper.find('button[type="submit"]')
      expect(button.attributes('disabled')).toBeDefined()
    })

    it('should enable submit button when email is valid', async () => {
      const wrapper = mount(EmailInput, {
        global: {
          plugins: [router, pinia]
        }
      })

      const input = wrapper.find('input[type="email"]')
      await input.setValue('test@example.com')

      const button = wrapper.find('button[type="submit"]')
      expect(button.attributes('disabled')).toBeUndefined()
    })
  })

  describe('Form Submission', () => {
    it('should call requestToken on form submit with valid email', async () => {
      const wrapper = mount(EmailInput, {
        global: {
          plugins: [router, pinia]
        }
      })

      const authStore = useAuthStore()
      const requestTokenSpy = vi.spyOn(authStore, 'requestToken').mockResolvedValue()

      const input = wrapper.find('input[type="email"]')
      await input.setValue('test@example.com')

      const form = wrapper.find('form')
      await form.trigger('submit.prevent')

      expect(requestTokenSpy).toHaveBeenCalledWith('test@example.com')
    })

    it('should show loading state during submission', async () => {
      const wrapper = mount(EmailInput, {
        global: {
          plugins: [router, pinia]
        }
      })

      const authStore = useAuthStore()
      vi.spyOn(authStore, 'requestToken').mockImplementation(() =>
        new Promise(resolve => setTimeout(resolve, 100))
      )

      const input = wrapper.find('input[type="email"]')
      await input.setValue('test@example.com')

      const form = wrapper.find('form')
      await form.trigger('submit.prevent')

      // Check loading state
      expect(wrapper.find('.spinner').exists()).toBe(true)
      expect(wrapper.find('input').attributes('disabled')).toBeDefined()
      expect(wrapper.find('button').attributes('disabled')).toBeDefined()
    })

    it('should show success message after successful submission', async () => {
      const wrapper = mount(EmailInput, {
        global: {
          plugins: [router, pinia]
        }
      })

      const authStore = useAuthStore()
      vi.spyOn(authStore, 'requestToken').mockResolvedValue()

      const input = wrapper.find('input[type="email"]')
      await input.setValue('test@example.com')

      const form = wrapper.find('form')
      await form.trigger('submit.prevent')

      await flushPromises()

      expect(wrapper.find('.success-message').exists()).toBe(true)
      expect(wrapper.find('.success-message').text()).toContain('Check your email for a 6-digit verification code')
      expect(wrapper.find('.redirect-text').text()).toContain('Redirecting to code entry')
    })
  })

  describe('Error Handling', () => {
    it('should show error message on failed submission', async () => {
      const wrapper = mount(EmailInput, {
        global: {
          plugins: [router, pinia]
        }
      })

      const authStore = useAuthStore()
      vi.spyOn(authStore, 'requestToken').mockRejectedValue({
        response: {
          data: { detail: 'Server error occurred' }
        }
      })

      const input = wrapper.find('input[type="email"]')
      await input.setValue('test@example.com')

      const form = wrapper.find('form')
      await form.trigger('submit.prevent')

      await flushPromises()

      expect(wrapper.find('.error-message').exists()).toBe(true)
      expect(wrapper.find('.error-message').text()).toContain('Server error occurred')
    })

    it('should show default error message when detail is missing', async () => {
      const wrapper = mount(EmailInput, {
        global: {
          plugins: [router, pinia]
        }
      })

      const authStore = useAuthStore()
      vi.spyOn(authStore, 'requestToken').mockRejectedValue({
        response: { data: {} }
      })

      const input = wrapper.find('input[type="email"]')
      await input.setValue('test@example.com')

      const form = wrapper.find('form')
      await form.trigger('submit.prevent')

      await flushPromises()

      expect(wrapper.find('.error-message').exists()).toBe(true)
      expect(wrapper.find('.error-message').text()).toContain('Failed to send code')
    })
  })

  describe('Rate Limiting', () => {
    it('should show rate limit info with retry time', async () => {
      const wrapper = mount(EmailInput, {
        global: {
          plugins: [router, pinia]
        }
      })

      const authStore = useAuthStore()
      vi.spyOn(authStore, 'requestToken').mockRejectedValue({
        response: {
          status: 429,
          data: {
            detail: 'Rate limit exceeded',
            retry_after: 300
          }
        }
      })

      const input = wrapper.find('input[type="email"]')
      await input.setValue('test@example.com')

      const form = wrapper.find('form')
      await form.trigger('submit.prevent')

      await flushPromises()

      expect(wrapper.find('.error-message').exists()).toBe(true)
      expect(wrapper.find('.retry-info').exists()).toBe(true)
      expect(wrapper.find('.retry-info').text()).toContain('Please wait')
      expect(wrapper.find('.retry-info').text()).toContain('minutes')
    })

    it('should show attempts remaining info', async () => {
      const wrapper = mount(EmailInput, {
        global: {
          plugins: [router, pinia]
        }
      })

      const authStore = useAuthStore()
      vi.spyOn(authStore, 'requestToken').mockRejectedValue({
        response: {
          status: 429,
          data: {
            detail: 'Rate limit warning',
            attempts_remaining: 2
          }
        }
      })

      const input = wrapper.find('input[type="email"]')
      await input.setValue('test@example.com')

      const form = wrapper.find('form')
      await form.trigger('submit.prevent')

      await flushPromises()

      expect(wrapper.find('.retry-info').exists()).toBe(true)
      expect(wrapper.find('.retry-info').text()).toContain('2 attempts remaining')
    })

    it('should format retry time correctly', async () => {
      const wrapper = mount(EmailInput, {
        global: {
          plugins: [router, pinia]
        }
      })

      const authStore = useAuthStore()

      // Test 60 seconds = 1 minute
      vi.spyOn(authStore, 'requestToken').mockRejectedValue({
        response: {
          status: 429,
          data: { retry_after: 60 }
        }
      })

      const input = wrapper.find('input[type="email"]')
      await input.setValue('test@example.com')

      const form = wrapper.find('form')
      await form.trigger('submit.prevent')

      await flushPromises()

      expect(wrapper.find('.retry-info').text()).toContain('1 minute')
    })
  })

  describe('Auto-navigation', () => {
    it('should navigate to login with email query after success', async () => {
      vi.useFakeTimers()

      const wrapper = mount(EmailInput, {
        global: {
          plugins: [router, pinia]
        }
      })

      const authStore = useAuthStore()
      vi.spyOn(authStore, 'requestToken').mockResolvedValue()
      const pushSpy = vi.spyOn(router, 'push')

      const input = wrapper.find('input[type="email"]')
      await input.setValue('test@example.com')

      const form = wrapper.find('form')
      await form.trigger('submit.prevent')

      await flushPromises()

      // Fast-forward time by 1.5 seconds
      vi.advanceTimersByTime(1500)

      expect(pushSpy).toHaveBeenCalledWith({
        name: 'Login',
        query: { email: 'test@example.com' }
      })

      vi.useRealTimers()
    })
  })
})
