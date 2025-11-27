import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import TokenInput from '@/components/auth/TokenInput.vue'
import { useAuthStore } from '@/stores/auth'

// Mock router
const mockPush = vi.fn()
vi.mock('vue-router', () => ({
  useRouter: () => ({
    push: mockPush
  }),
  useRoute: () => ({
    query: { email: 'test@example.com' }
  })
}))

describe('TokenInput.vue', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    mockPush.mockClear()
    vi.clearAllTimers()
  })

  it('renders 6 input fields', () => {
    const wrapper = mount(TokenInput, {
      props: {
        email: 'test@example.com'
      }
    })

    const inputs = wrapper.findAll('input.token-digit')
    expect(inputs).toHaveLength(6)
  })

  it('displays masked email', () => {
    const wrapper = mount(TokenInput, {
      props: {
        email: 'test@example.com'
      }
    })

    expect(wrapper.text()).toContain('t***@example.com')
  })

  it('only accepts numeric input', async () => {
    const wrapper = mount(TokenInput, {
      props: {
        email: 'test@example.com'
      }
    })

    const firstInput = wrapper.findAll('input.token-digit')[0]

    // Try to input a letter
    await firstInput.setValue('a')
    expect(firstInput.element.value).toBe('')

    // Input a number
    await firstInput.setValue('5')
    expect(firstInput.element.value).toBe('5')
  })

  it('auto-focuses next field after digit entry', async () => {
    const wrapper = mount(TokenInput, {
      props: {
        email: 'test@example.com'
      },
      attachTo: document.body
    })

    const inputs = wrapper.findAll('input.token-digit')
    const firstInput = inputs[0]
    const secondInput = inputs[1]

    // Focus first input
    await firstInput.trigger('focus')

    // Enter a digit
    await firstInput.setValue('1')
    await firstInput.trigger('input')

    // Wait for nextTick
    await wrapper.vm.$nextTick()

    // Second input should be focused (check if it's the active element)
    expect(document.activeElement).toBe(secondInput.element)

    wrapper.unmount()
  })

  it('handles backspace to move to previous field', async () => {
    const wrapper = mount(TokenInput, {
      props: {
        email: 'test@example.com'
      },
      attachTo: document.body
    })

    const inputs = wrapper.findAll('input.token-digit')
    const secondInput = inputs[1]

    // Set focus on second input
    await secondInput.trigger('focus')

    // Press backspace on empty field
    await secondInput.trigger('keydown', { key: 'Backspace' })
    await wrapper.vm.$nextTick()

    // First input should be focused
    expect(document.activeElement).toBe(inputs[0].element)

    wrapper.unmount()
  })

  it('handles paste of 6-digit code', async () => {
    const wrapper = mount(TokenInput, {
      props: {
        email: 'test@example.com'
      }
    })

    const firstInput = wrapper.findAll('input.token-digit')[0]

    // Create paste event
    const pasteEvent = new ClipboardEvent('paste', {
      clipboardData: new DataTransfer()
    })
    pasteEvent.clipboardData?.setData('text/plain', '123456')

    // Trigger paste
    await firstInput.element.dispatchEvent(pasteEvent)
    await wrapper.vm.$nextTick()

    // All fields should be filled
    const inputs = wrapper.findAll('input.token-digit')
    expect(inputs[0].element.value).toBe('1')
    expect(inputs[1].element.value).toBe('2')
    expect(inputs[2].element.value).toBe('3')
    expect(inputs[3].element.value).toBe('4')
    expect(inputs[4].element.value).toBe('5')
    expect(inputs[5].element.value).toBe('6')
  })

  it('shows loading state during validation', async () => {
    const authStore = useAuthStore()
    authStore.validateToken = vi.fn().mockImplementation(() => new Promise(resolve => setTimeout(resolve, 100)))

    const wrapper = mount(TokenInput, {
      props: {
        email: 'test@example.com'
      }
    })

    // Fill all digits
    const inputs = wrapper.findAll('input.token-digit')
    for (let i = 0; i < 6; i++) {
      await inputs[i].setValue(String(i + 1))
    }

    await wrapper.vm.$nextTick()

    // Should show loading
    expect(wrapper.find('.loading').exists()).toBe(true)
    expect(wrapper.text()).toContain('Validating')
  })

  it('displays error message on validation failure', async () => {
    const authStore = useAuthStore()
    authStore.validateToken = vi.fn().mockRejectedValue({
      response: {
        status: 401,
        data: { detail: 'Invalid or expired token' }
      }
    })

    const wrapper = mount(TokenInput, {
      props: {
        email: 'test@example.com'
      }
    })

    // Fill all digits
    const inputs = wrapper.findAll('input.token-digit')
    for (let i = 0; i < 6; i++) {
      await inputs[i].setValue(String(i + 1))
      await inputs[i].trigger('input')
    }

    await wrapper.vm.$nextTick()
    await new Promise(resolve => setTimeout(resolve, 50))

    // Should show error (error message changed to be more specific)
    expect(wrapper.find('.error-message').exists()).toBe(true)
    expect(wrapper.text()).toContain('This code has expired')
  })

  it('clears fields after error', async () => {
    const authStore = useAuthStore()
    authStore.validateToken = vi.fn().mockRejectedValue({
      response: {
        status: 401,
        data: { detail: 'Invalid token' }
      }
    })

    const wrapper = mount(TokenInput, {
      props: {
        email: 'test@example.com'
      }
    })

    // Fill all digits
    const inputs = wrapper.findAll('input.token-digit')
    for (let i = 0; i < 6; i++) {
      await inputs[i].setValue(String(i + 1))
      await inputs[i].trigger('input')
    }

    await wrapper.vm.$nextTick()
    await new Promise(resolve => setTimeout(resolve, 50))

    // All fields should be cleared
    for (let i = 0; i < 6; i++) {
      expect(inputs[i].element.value).toBe('')
    }
  })

  it('navigates to dashboard on successful validation', async () => {
    const authStore = useAuthStore()
    authStore.validateToken = vi.fn().mockResolvedValue({
      access_token: 'test-token',
      user: { id: '1', email: 'test@example.com' }
    })

    const wrapper = mount(TokenInput, {
      props: {
        email: 'test@example.com'
      }
    })

    // Fill all digits
    const inputs = wrapper.findAll('input.token-digit')
    for (let i = 0; i < 6; i++) {
      await inputs[i].setValue(String(i + 1))
      await inputs[i].trigger('input')
    }

    await wrapper.vm.$nextTick()
    await new Promise(resolve => setTimeout(resolve, 50))

    // Should navigate to dashboard
    expect(mockPush).toHaveBeenCalledWith({ name: 'dashboard' })
  })

  it('shows resend button with cooldown', async () => {
    const wrapper = mount(TokenInput, {
      props: {
        email: 'test@example.com'
      }
    })

    const resendButton = wrapper.find('.resend-button')
    expect(resendButton.exists()).toBe(true)
    expect(resendButton.text()).toBe("Resend code")
  })

  it('handles resend with cooldown timer', async () => {
    vi.useFakeTimers()

    const authStore = useAuthStore()
    authStore.requestToken = vi.fn().mockResolvedValue({
      email: 't***@example.com'
    })

    const wrapper = mount(TokenInput, {
      props: {
        email: 'test@example.com'
      }
    })

    const resendButton = wrapper.find('.resend-button')

    // Click resend
    await resendButton.trigger('click')
    await wrapper.vm.$nextTick()

    // Button should be disabled and show countdown (starts at 60)
    expect(resendButton.attributes('disabled')).toBeDefined()
    expect(resendButton.text()).toContain('Resend code (60s)')

    // Fast-forward 30 seconds
    vi.advanceTimersByTime(30000)
    await wrapper.vm.$nextTick()

    expect(resendButton.text()).toContain('Resend code (30s)')

    vi.useRealTimers()
  })

  it('handles expired token error specifically', async () => {
    const authStore = useAuthStore()
    authStore.validateToken = vi.fn().mockRejectedValue({
      response: {
        status: 401,
        data: { detail: 'Token has expired' }
      }
    })

    const wrapper = mount(TokenInput, {
      props: {
        email: 'test@example.com'
      }
    })

    // Fill all digits
    const inputs = wrapper.findAll('input.token-digit')
    for (let i = 0; i < 6; i++) {
      await inputs[i].setValue(String(i + 1))
      await inputs[i].trigger('input')
    }

    await wrapper.vm.$nextTick()
    await new Promise(resolve => setTimeout(resolve, 100))

    // Should show expired error
    expect(wrapper.text()).toContain('expired')
  }, 10000)

  it('handles used token error specifically', async () => {
    const authStore = useAuthStore()
    authStore.validateToken = vi.fn().mockRejectedValue({
      response: {
        status: 401,
        data: { detail: 'Token has already been used' }
      }
    })

    const wrapper = mount(TokenInput, {
      props: {
        email: 'test@example.com'
      }
    })

    // Fill all digits
    const inputs = wrapper.findAll('input.token-digit')
    for (let i = 0; i < 6; i++) {
      await inputs[i].setValue(String(i + 1))
      await inputs[i].trigger('input')
    }

    await wrapper.vm.$nextTick()
    await new Promise(resolve => setTimeout(resolve, 100))

    // Should show used error
    expect(wrapper.text()).toContain('used')
  }, 10000)
})
