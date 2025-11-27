import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import CountdownTimer from '@/components/auth/CountdownTimer.vue'

describe('CountdownTimer.vue', () => {
  it('renders with normal state for time > 30 seconds', () => {
    const wrapper = mount(CountdownTimer, {
      props: {
        timeRemaining: 90,
        isLowTime: false,
        isExpired: false
      }
    })

    expect(wrapper.find('.countdown-timer').exists()).toBe(true)
    expect(wrapper.find('.timer-normal').exists()).toBe(true)
    expect(wrapper.text()).toContain('Time remaining:')
    expect(wrapper.text()).toContain('1:30')
  })

  it('renders with warning state for time <= 30 seconds', () => {
    const wrapper = mount(CountdownTimer, {
      props: {
        timeRemaining: 25,
        isLowTime: true,
        isExpired: false
      }
    })

    expect(wrapper.find('.timer-warning').exists()).toBe(true)
    expect(wrapper.text()).toContain('Time remaining:')
    expect(wrapper.text()).toContain('0:25')
  })

  it('renders with expired state when time is 0', () => {
    const wrapper = mount(CountdownTimer, {
      props: {
        timeRemaining: 0,
        isLowTime: false,
        isExpired: true
      }
    })

    expect(wrapper.find('.timer-expired').exists()).toBe(true)
    expect(wrapper.text()).toContain('Token expired')
    // When expired, we only show "Token expired" text, not the time
    expect(wrapper.find('.expired-text').exists()).toBe(true)
  })

  it('formats time correctly as MM:SS', () => {
    const wrapper = mount(CountdownTimer, {
      props: {
        timeRemaining: 125,
        isLowTime: false,
        isExpired: false
      }
    })

    expect(wrapper.text()).toContain('2:05')
  })

  it('formats single digit seconds with leading zero', () => {
    const wrapper = mount(CountdownTimer, {
      props: {
        timeRemaining: 9,
        isLowTime: true,
        isExpired: false
      }
    })

    expect(wrapper.text()).toContain('0:09')
  })

  it('displays timer icon', () => {
    const wrapper = mount(CountdownTimer, {
      props: {
        timeRemaining: 60,
        isLowTime: false,
        isExpired: false
      }
    })

    expect(wrapper.find('.timer-icon').exists()).toBe(true)
    expect(wrapper.find('.timer-icon').text()).toBeTruthy()
  })

  it('has proper ARIA attributes for accessibility', () => {
    const wrapper = mount(CountdownTimer, {
      props: {
        timeRemaining: 90,
        isLowTime: false,
        isExpired: false
      }
    })

    const timer = wrapper.find('.countdown-timer')
    expect(timer.attributes('role')).toBe('timer')
    expect(timer.attributes('aria-label')).toBeTruthy()
    expect(timer.attributes('aria-live')).toBe('polite')
  })

  it('has descriptive ARIA label for normal state', () => {
    const wrapper = mount(CountdownTimer, {
      props: {
        timeRemaining: 90,
        isLowTime: false,
        isExpired: false
      }
    })

    const ariaLabel = wrapper.find('.countdown-timer').attributes('aria-label')
    expect(ariaLabel).toContain('Time remaining')
    expect(ariaLabel).toContain('minute')
  })

  it('has descriptive ARIA label for expired state', () => {
    const wrapper = mount(CountdownTimer, {
      props: {
        timeRemaining: 0,
        isLowTime: false,
        isExpired: true
      }
    })

    const ariaLabel = wrapper.find('.countdown-timer').attributes('aria-label')
    expect(ariaLabel).toBe('Token expired')
  })

  it('handles 2 minutes (120 seconds) correctly', () => {
    const wrapper = mount(CountdownTimer, {
      props: {
        timeRemaining: 120,
        isLowTime: false,
        isExpired: false
      }
    })

    expect(wrapper.text()).toContain('2:00')
  })

  it('handles 1 minute exactly', () => {
    const wrapper = mount(CountdownTimer, {
      props: {
        timeRemaining: 60,
        isLowTime: false,
        isExpired: false
      }
    })

    expect(wrapper.text()).toContain('1:00')
  })

  it('handles the 30-second threshold', () => {
    const wrapper = mount(CountdownTimer, {
      props: {
        timeRemaining: 30,
        isLowTime: true,
        isExpired: false
      }
    })

    expect(wrapper.find('.timer-warning').exists()).toBe(true)
    expect(wrapper.text()).toContain('0:30')
  })

  it('displays warning icon in low time state', () => {
    const wrapper = mount(CountdownTimer, {
      props: {
        timeRemaining: 15,
        isLowTime: true,
        isExpired: false
      }
    })

    const icon = wrapper.find('.timer-icon').text()
    expect(icon).toBeTruthy()
  })

  it('displays warning icon in expired state', () => {
    const wrapper = mount(CountdownTimer, {
      props: {
        timeRemaining: 0,
        isLowTime: false,
        isExpired: true
      }
    })

    const icon = wrapper.find('.timer-icon').text()
    expect(icon).toBeTruthy()
  })

  it('applies correct CSS classes for each state', () => {
    // Normal state
    const normalWrapper = mount(CountdownTimer, {
      props: {
        timeRemaining: 90,
        isLowTime: false,
        isExpired: false
      }
    })
    expect(normalWrapper.find('.timer-normal').exists()).toBe(true)
    expect(normalWrapper.find('.timer-warning').exists()).toBe(false)
    expect(normalWrapper.find('.timer-expired').exists()).toBe(false)

    // Warning state
    const warningWrapper = mount(CountdownTimer, {
      props: {
        timeRemaining: 20,
        isLowTime: true,
        isExpired: false
      }
    })
    expect(warningWrapper.find('.timer-warning').exists()).toBe(true)
    expect(warningWrapper.find('.timer-normal').exists()).toBe(false)
    expect(warningWrapper.find('.timer-expired').exists()).toBe(false)

    // Expired state
    const expiredWrapper = mount(CountdownTimer, {
      props: {
        timeRemaining: 0,
        isLowTime: false,
        isExpired: true
      }
    })
    expect(expiredWrapper.find('.timer-expired').exists()).toBe(true)
    expect(expiredWrapper.find('.timer-normal').exists()).toBe(false)
    expect(expiredWrapper.find('.timer-warning').exists()).toBe(false)
  })

  it('updates displayed time when prop changes', async () => {
    const wrapper = mount(CountdownTimer, {
      props: {
        timeRemaining: 60,
        isLowTime: false,
        isExpired: false
      }
    })

    expect(wrapper.text()).toContain('1:00')

    // Update time
    await wrapper.setProps({ timeRemaining: 45 })
    expect(wrapper.text()).toContain('0:45')
  })

  it('updates state classes when props change', async () => {
    const wrapper = mount(CountdownTimer, {
      props: {
        timeRemaining: 60,
        isLowTime: false,
        isExpired: false
      }
    })

    expect(wrapper.find('.timer-normal').exists()).toBe(true)

    // Update to low time
    await wrapper.setProps({ timeRemaining: 20, isLowTime: true })
    expect(wrapper.find('.timer-warning').exists()).toBe(true)

    // Update to expired
    await wrapper.setProps({ timeRemaining: 0, isLowTime: false, isExpired: true })
    expect(wrapper.find('.timer-expired').exists()).toBe(true)
  })

  it('handles seconds only correctly', () => {
    const wrapper = mount(CountdownTimer, {
      props: {
        timeRemaining: 45,
        isLowTime: false,
        isExpired: false
      }
    })

    const ariaLabel = wrapper.find('.countdown-timer').attributes('aria-label')
    expect(ariaLabel).toContain('45 seconds')
  })

  it('handles minutes only correctly', () => {
    const wrapper = mount(CountdownTimer, {
      props: {
        timeRemaining: 120,
        isLowTime: false,
        isExpired: false
      }
    })

    const ariaLabel = wrapper.find('.countdown-timer').attributes('aria-label')
    expect(ariaLabel).toContain('2 minutes')
  })

  it('handles minutes and seconds correctly in ARIA label', () => {
    const wrapper = mount(CountdownTimer, {
      props: {
        timeRemaining: 95,
        isLowTime: false,
        isExpired: false
      }
    })

    const ariaLabel = wrapper.find('.countdown-timer').attributes('aria-label')
    expect(ariaLabel).toContain('1 minute')
    expect(ariaLabel).toContain('35 seconds')
  })

  it('uses singular forms in ARIA label correctly', () => {
    const wrapper = mount(CountdownTimer, {
      props: {
        timeRemaining: 61,
        isLowTime: false,
        isExpired: false
      }
    })

    const ariaLabel = wrapper.find('.countdown-timer').attributes('aria-label')
    expect(ariaLabel).toContain('1 minute')
    expect(ariaLabel).toContain('1 second')
  })
})
