import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createRouter, createMemoryHistory } from 'vue-router'
import { createPinia, setActivePinia } from 'pinia'
import Home from '@/views/Home.vue'
import { useAuthStore } from '@/stores/auth'
import AppLayout from '@/components/layout/AppLayout.vue'

// Mock branding config
vi.mock('@/config/branding', () => ({
  getBrandingConfig: () => ({
    appName: 'Test Authentication App',
    primaryColor: '#007bff',
    logoUrl: '/test-logo.svg'
  })
}))

/**
 * Home View Tests
 * Tests the landing page view with authentication-aware content
 */

describe('Home View', () => {
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
        { path: '/', name: 'Home', component: Home },
        { path: '/login', name: 'login', component: { template: '<div>Login</div>' } },
        { path: '/dashboard', name: 'dashboard', component: { template: '<div>Dashboard</div>' } }
      ]
    })
  })

  describe('Component Rendering', () => {
    it('should render the home view correctly', () => {
      const wrapper = mount(Home, {
        global: {
          plugins: [router, pinia],
          stubs: {
            AppLayout: false
          }
        }
      })

      expect(wrapper.find('.home').exists()).toBe(true)
      expect(wrapper.findComponent(AppLayout).exists()).toBe(true)
    })

    it('should render hero section', () => {
      const wrapper = mount(Home, {
        global: {
          plugins: [router, pinia],
          stubs: {
            AppLayout: false
          }
        }
      })

      const hero = wrapper.find('.hero')
      expect(hero.exists()).toBe(true)
      expect(hero.find('h1').exists()).toBe(true)
      expect(hero.find('.subtitle').exists()).toBe(true)
      expect(hero.find('.actions').exists()).toBe(true)
    })

    it('should render features section', () => {
      const wrapper = mount(Home, {
        global: {
          plugins: [router, pinia],
          stubs: {
            AppLayout: false
          }
        }
      })

      const features = wrapper.find('.features')
      expect(features.exists()).toBe(true)

      const featureCards = wrapper.findAll('.feature')
      expect(featureCards).toHaveLength(3)
    })
  })

  describe('Hero Section Content', () => {
    it('should display welcome message with app name', () => {
      const wrapper = mount(Home, {
        global: {
          plugins: [router, pinia],
          stubs: {
            AppLayout: false
          }
        }
      })

      const heading = wrapper.find('.hero h1')
      expect(heading.text()).toContain('Welcome to Test Authentication App')
    })

    it('should display subtitle', () => {
      const wrapper = mount(Home, {
        global: {
          plugins: [router, pinia],
          stubs: {
            AppLayout: false
          }
        }
      })

      const subtitle = wrapper.find('.subtitle')
      expect(subtitle.text()).toBe('Secure, passwordless authentication using email verification tokens')
    })
  })

  describe('Call-to-Action Button - Logged Out', () => {
    it('should show "Get Started" button when logged out', async () => {
      const wrapper = mount(Home, {
        global: {
          plugins: [router, pinia],
          stubs: {
            AppLayout: false
          }
        }
      })

      const authStore = useAuthStore()
      authStore.isAuthenticated = false

      await wrapper.vm.$nextTick()

      const button = wrapper.find('.actions button')
      expect(button.exists()).toBe(true)
      expect(button.text()).toBe('Get Started')
      expect(button.classes()).toContain('btn-primary')
    })

    it('should navigate to login when "Get Started" is clicked', async () => {
      const wrapper = mount(Home, {
        global: {
          plugins: [router, pinia],
          stubs: {
            AppLayout: false
          }
        }
      })

      const authStore = useAuthStore()
      authStore.isAuthenticated = false

      await wrapper.vm.$nextTick()

      const pushSpy = vi.spyOn(router, 'push')
      const button = wrapper.find('.actions button')

      await button.trigger('click')

      expect(pushSpy).toHaveBeenCalledWith({ name: 'login' })
    })
  })

  describe('Call-to-Action Button - Logged In', () => {
    it('should show "Go to Dashboard" button when logged in', async () => {
      const wrapper = mount(Home, {
        global: {
          plugins: [router, pinia],
          stubs: {
            AppLayout: false
          }
        }
      })

      const authStore = useAuthStore()
      authStore.isAuthenticated = true
      authStore.user = { id: '1', email: 'test@example.com', is_active: true }

      await wrapper.vm.$nextTick()

      const button = wrapper.find('.actions button')
      expect(button.exists()).toBe(true)
      expect(button.text()).toBe('Go to Dashboard')
      expect(button.classes()).toContain('btn-primary')
    })

    it('should navigate to dashboard when "Go to Dashboard" is clicked', async () => {
      const wrapper = mount(Home, {
        global: {
          plugins: [router, pinia],
          stubs: {
            AppLayout: false
          }
        }
      })

      const authStore = useAuthStore()
      authStore.isAuthenticated = true
      authStore.user = { id: '1', email: 'test@example.com', is_active: true }

      await wrapper.vm.$nextTick()

      const pushSpy = vi.spyOn(router, 'push')
      const button = wrapper.find('.actions button')

      await button.trigger('click')

      expect(pushSpy).toHaveBeenCalledWith({ name: 'dashboard' })
    })

    it('should not show "Get Started" button when logged in', async () => {
      const wrapper = mount(Home, {
        global: {
          plugins: [router, pinia],
          stubs: {
            AppLayout: false
          }
        }
      })

      const authStore = useAuthStore()
      authStore.isAuthenticated = true
      authStore.user = { id: '1', email: 'test@example.com', is_active: true }

      await wrapper.vm.$nextTick()

      const buttons = wrapper.findAll('.actions button')
      const getStartedButton = buttons.find(btn => btn.text() === 'Get Started')

      expect(getStartedButton).toBeUndefined()
    })
  })

  describe('Features Section', () => {
    it('should display "Simple & Secure" feature', () => {
      const wrapper = mount(Home, {
        global: {
          plugins: [router, pinia],
          stubs: {
            AppLayout: false
          }
        }
      })

      const features = wrapper.findAll('.feature')
      const simpleSecure = features.find(f => f.find('h3').text() === 'Simple & Secure')

      expect(simpleSecure).toBeDefined()
      expect(simpleSecure?.find('p').text()).toBe('No passwords to remember. Just enter your email and receive a verification code.')
    })

    it('should display "Fast Access" feature', () => {
      const wrapper = mount(Home, {
        global: {
          plugins: [router, pinia],
          stubs: {
            AppLayout: false
          }
        }
      })

      const features = wrapper.findAll('.feature')
      const fastAccess = features.find(f => f.find('h3').text() === 'Fast Access')

      expect(fastAccess).toBeDefined()
      expect(fastAccess?.find('p').text()).toBe('6-digit tokens delivered instantly to your email. Auto-submit for seamless experience.')
    })

    it('should display "Privacy First" feature', () => {
      const wrapper = mount(Home, {
        global: {
          plugins: [router, pinia],
          stubs: {
            AppLayout: false
          }
        }
      })

      const features = wrapper.findAll('.feature')
      const privacyFirst = features.find(f => f.find('h3').text() === 'Privacy First')

      expect(privacyFirst).toBeDefined()
      expect(privacyFirst?.find('p').text()).toBe('Your data is protected. Tokens expire after 2 minutes and are single-use only.')
    })

    it('should render feature cards with correct structure', () => {
      const wrapper = mount(Home, {
        global: {
          plugins: [router, pinia],
          stubs: {
            AppLayout: false
          }
        }
      })

      const features = wrapper.findAll('.feature')

      features.forEach(feature => {
        expect(feature.find('h3').exists()).toBe(true)
        expect(feature.find('p').exists()).toBe(true)
      })
    })
  })

  describe('Computed Properties', () => {
    it('should reactively update isLoggedIn based on auth store', async () => {
      const wrapper = mount(Home, {
        global: {
          plugins: [router, pinia],
          stubs: {
            AppLayout: false
          }
        }
      })

      const authStore = useAuthStore()

      // Initially logged out
      authStore.isAuthenticated = false
      await wrapper.vm.$nextTick()
      expect(wrapper.find('.actions button').text()).toBe('Get Started')

      // Change to logged in
      authStore.isAuthenticated = true
      authStore.user = { id: '1', email: 'test@example.com', is_active: true }
      await wrapper.vm.$nextTick()
      expect(wrapper.find('.actions button').text()).toBe('Go to Dashboard')
    })
  })

  describe('Branding Integration', () => {
    it('should use branding config for app name', () => {
      const wrapper = mount(Home, {
        global: {
          plugins: [router, pinia],
          stubs: {
            AppLayout: false
          }
        }
      })

      const heading = wrapper.find('.hero h1')
      expect(heading.text()).toContain('Test Authentication App')
    })

    it('should integrate getBrandingConfig', () => {
      const wrapper = mount(Home, {
        global: {
          plugins: [router, pinia],
          stubs: {
            AppLayout: false
          }
        }
      })

      // Component should successfully call getBrandingConfig
      expect(wrapper.find('.home').exists()).toBe(true)
      expect(wrapper.text()).toContain('Test Authentication App')
    })
  })

  describe('Layout Integration', () => {
    it('should wrap content in AppLayout component', () => {
      const wrapper = mount(Home, {
        global: {
          plugins: [router, pinia],
          stubs: {
            AppLayout: false
          }
        }
      })

      const layout = wrapper.findComponent(AppLayout)
      expect(layout.exists()).toBe(true)

      // Home content should be inside AppLayout
      const homeContent = layout.find('.home')
      expect(homeContent.exists()).toBe(true)
    })
  })

  describe('Smoke Tests', () => {
    it('should render without errors', () => {
      expect(() => {
        mount(Home, {
          global: {
            plugins: [router, pinia],
            stubs: {
              AppLayout: false
            }
          }
        })
      }).not.toThrow()
    })

    it('should render all main sections', () => {
      const wrapper = mount(Home, {
        global: {
          plugins: [router, pinia],
          stubs: {
            AppLayout: false
          }
        }
      })

      expect(wrapper.find('.home').exists()).toBe(true)
      expect(wrapper.find('.hero').exists()).toBe(true)
      expect(wrapper.find('.features').exists()).toBe(true)
      expect(wrapper.find('.actions').exists()).toBe(true)
    })

    it('should handle auth store state changes', async () => {
      const wrapper = mount(Home, {
        global: {
          plugins: [router, pinia],
          stubs: {
            AppLayout: false
          }
        }
      })

      const authStore = useAuthStore()

      // Multiple state changes should not cause errors
      authStore.isAuthenticated = false
      await wrapper.vm.$nextTick()

      authStore.isAuthenticated = true
      authStore.user = { id: '1', email: 'test@example.com', is_active: true }
      await wrapper.vm.$nextTick()

      authStore.isAuthenticated = false
      authStore.user = null
      await wrapper.vm.$nextTick()

      expect(wrapper.find('.home').exists()).toBe(true)
    })
  })
})
