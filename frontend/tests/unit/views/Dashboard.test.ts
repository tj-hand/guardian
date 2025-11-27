import { describe, it, expect, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createRouter, createMemoryHistory } from 'vue-router'
import { createPinia, setActivePinia } from 'pinia'
import Dashboard from '@/views/Dashboard.vue'
import { useAuthStore } from '@/stores/auth'
import AppLayout from '@/components/layout/AppLayout.vue'

/**
 * Dashboard View Tests
 * Tests the protected dashboard view with user information display
 */

describe('Dashboard View', () => {
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
        { path: '/dashboard', name: 'Dashboard', component: Dashboard }
      ]
    })
  })

  describe('Component Rendering', () => {
    it('should render the dashboard view correctly', () => {
      const wrapper = mount(Dashboard, {
        global: {
          plugins: [router, pinia],
          stubs: {
            AppLayout: false
          }
        }
      })

      expect(wrapper.find('.dashboard').exists()).toBe(true)
      expect(wrapper.findComponent(AppLayout).exists()).toBe(true)
    })

    it('should render dashboard title', () => {
      const wrapper = mount(Dashboard, {
        global: {
          plugins: [router, pinia],
          stubs: {
            AppLayout: false
          }
        }
      })

      const title = wrapper.find('h1')
      expect(title.exists()).toBe(true)
      expect(title.text()).toBe('Dashboard')
    })

    it('should render welcome section', () => {
      const wrapper = mount(Dashboard, {
        global: {
          plugins: [router, pinia],
          stubs: {
            AppLayout: false
          }
        }
      })

      const welcome = wrapper.find('.welcome')
      expect(welcome.exists()).toBe(true)
    })

    it('should render session information box', () => {
      const wrapper = mount(Dashboard, {
        global: {
          plugins: [router, pinia],
          stubs: {
            AppLayout: false
          }
        }
      })

      const infoBox = wrapper.find('.info-box')
      expect(infoBox.exists()).toBe(true)
      expect(infoBox.find('h2').text()).toBe('Session Information')
    })
  })

  describe('Welcome Message', () => {
    it('should display welcome message with user email', async () => {
      const authStore = useAuthStore()
      authStore.user = {
        id: '123',
        email: 'user@example.com',
        is_active: true,
        created_at: '2024-01-15T10:30:00Z'
      }

      const wrapper = mount(Dashboard, {
        global: {
          plugins: [router, pinia],
          stubs: {
            AppLayout: false
          }
        }
      })

      await wrapper.vm.$nextTick()

      const welcome = wrapper.find('.welcome')
      expect(welcome.text()).toContain('Welcome,')
      expect(welcome.text()).toContain('user@example.com')
    })

    it('should display authentication success message', () => {
      const wrapper = mount(Dashboard, {
        global: {
          plugins: [router, pinia],
          stubs: {
            AppLayout: false
          }
        }
      })

      const subtitle = wrapper.find('.welcome .subtitle')
      expect(subtitle.exists()).toBe(true)
      expect(subtitle.text()).toBe('You are successfully authenticated.')
    })

    it('should render email in bold', async () => {
      const authStore = useAuthStore()
      authStore.user = {
        id: '123',
        email: 'bold@example.com',
        is_active: true
      }

      const wrapper = mount(Dashboard, {
        global: {
          plugins: [router, pinia],
          stubs: {
            AppLayout: false
          }
        }
      })

      await wrapper.vm.$nextTick()

      const strong = wrapper.find('.welcome strong')
      expect(strong.exists()).toBe(true)
      expect(strong.text()).toBe('bold@example.com')
    })
  })

  describe('Session Information Display', () => {
    it('should display user email', async () => {
      const authStore = useAuthStore()
      authStore.user = {
        id: '123',
        email: 'test@example.com',
        is_active: true
      }

      const wrapper = mount(Dashboard, {
        global: {
          plugins: [router, pinia],
          stubs: {
            AppLayout: false
          }
        }
      })

      await wrapper.vm.$nextTick()

      const dl = wrapper.find('dl')
      expect(dl.text()).toContain('Email:')
      expect(dl.text()).toContain('test@example.com')
    })

    it('should display user ID', async () => {
      const authStore = useAuthStore()
      authStore.user = {
        id: '456',
        email: 'test@example.com',
        is_active: true
      }

      const wrapper = mount(Dashboard, {
        global: {
          plugins: [router, pinia],
          stubs: {
            AppLayout: false
          }
        }
      })

      await wrapper.vm.$nextTick()

      const dl = wrapper.find('dl')
      expect(dl.text()).toContain('User ID:')
      expect(dl.text()).toContain('456')
    })

    it('should display active account status', async () => {
      const authStore = useAuthStore()
      authStore.user = {
        id: '123',
        email: 'test@example.com',
        is_active: true
      }

      const wrapper = mount(Dashboard, {
        global: {
          plugins: [router, pinia],
          stubs: {
            AppLayout: false
          }
        }
      })

      await wrapper.vm.$nextTick()

      const dl = wrapper.find('dl')
      expect(dl.text()).toContain('Account Status:')
      expect(dl.text()).toContain('Active')
    })

    it('should display inactive account status', () => {
      const authStore = useAuthStore()
      authStore.user = {
        id: '123',
        email: 'test@example.com',
        is_active: false
      }

      const wrapper = mount(Dashboard, {
        global: {
          plugins: [router, pinia],
          stubs: {
            AppLayout: false
          }
        }
      })

      const dl = wrapper.find('dl')
      expect(dl.text()).toContain('Account Status:')
      expect(dl.text()).toContain('Inactive')
    })

    it('should display registration date when available', async () => {
      const authStore = useAuthStore()
      authStore.user = {
        id: '123',
        email: 'test@example.com',
        is_active: true,
        created_at: '2024-01-15T10:30:00Z'
      }

      const wrapper = mount(Dashboard, {
        global: {
          plugins: [router, pinia],
          stubs: {
            AppLayout: false
          }
        }
      })

      await wrapper.vm.$nextTick()

      const dl = wrapper.find('dl')
      expect(dl.text()).toContain('Registered:')
      // Check that a date is displayed (format may vary by locale)
      expect(dl.text()).toMatch(/Registered:\s*\d/)
    })

    it('should display N/A when registration date is missing', () => {
      const authStore = useAuthStore()
      authStore.user = {
        id: '123',
        email: 'test@example.com',
        is_active: true
      }

      const wrapper = mount(Dashboard, {
        global: {
          plugins: [router, pinia],
          stubs: {
            AppLayout: false
          }
        }
      })

      const dl = wrapper.find('dl')
      expect(dl.text()).toContain('Registered:')
      expect(dl.text()).toContain('N/A')
    })
  })

  describe('Session Information Structure', () => {
    it('should use definition list for session info', () => {
      const wrapper = mount(Dashboard, {
        global: {
          plugins: [router, pinia],
          stubs: {
            AppLayout: false
          }
        }
      })

      const dl = wrapper.find('.info-box dl')
      expect(dl.exists()).toBe(true)
    })

    it('should have definition terms (dt) for labels', () => {
      const wrapper = mount(Dashboard, {
        global: {
          plugins: [router, pinia],
          stubs: {
            AppLayout: false
          }
        }
      })

      const dts = wrapper.findAll('dt')
      const labels = dts.map(dt => dt.text())

      expect(labels).toContain('Email:')
      expect(labels).toContain('User ID:')
      expect(labels).toContain('Account Status:')
      expect(labels).toContain('Registered:')
    })

    it('should have definition descriptions (dd) for values', async () => {
      const authStore = useAuthStore()
      authStore.user = {
        id: '999',
        email: 'data@example.com',
        is_active: true
      }

      const wrapper = mount(Dashboard, {
        global: {
          plugins: [router, pinia],
          stubs: {
            AppLayout: false
          }
        }
      })

      await wrapper.vm.$nextTick()

      const dds = wrapper.findAll('dd')
      expect(dds.length).toBeGreaterThan(0)

      const values = dds.map(dd => dd.text())
      expect(values).toContain('data@example.com')
      expect(values).toContain('999')
      expect(values).toContain('Active')
    })
  })

  describe('Null User Handling', () => {
    it('should handle null user gracefully', () => {
      const authStore = useAuthStore()
      authStore.user = null

      const wrapper = mount(Dashboard, {
        global: {
          plugins: [router, pinia],
          stubs: {
            AppLayout: false
          }
        }
      })

      // Should render without errors
      expect(wrapper.find('.dashboard').exists()).toBe(true)
    })

    it('should display empty values when user is null', () => {
      const authStore = useAuthStore()
      authStore.user = null

      const wrapper = mount(Dashboard, {
        global: {
          plugins: [router, pinia],
          stubs: {
            AppLayout: false
          }
        }
      })

      const welcome = wrapper.find('.welcome')
      // Should show welcome text but with empty/undefined values
      expect(welcome.exists()).toBe(true)
    })
  })

  describe('Date Formatting', () => {
    it('should format date correctly', async () => {
      const authStore = useAuthStore()
      authStore.user = {
        id: '123',
        email: 'test@example.com',
        is_active: true,
        created_at: '2024-06-15T12:00:00Z'
      }

      const wrapper = mount(Dashboard, {
        global: {
          plugins: [router, pinia],
          stubs: {
            AppLayout: false
          }
        }
      })

      await wrapper.vm.$nextTick()

      const dl = wrapper.find('dl')
      const text = dl.text()

      // Check that date formatting works (exact format depends on locale)
      expect(text).toContain('Registered:')
      expect(text).toMatch(/Registered:\s*\d/)
    })

    it('should handle invalid date format', () => {
      const authStore = useAuthStore()
      authStore.user = {
        id: '123',
        email: 'test@example.com',
        is_active: true,
        created_at: 'invalid-date'
      }

      const wrapper = mount(Dashboard, {
        global: {
          plugins: [router, pinia],
          stubs: {
            AppLayout: false
          }
        }
      })

      // Should not throw error
      expect(() => {
        wrapper.find('dl').text()
      }).not.toThrow()
    })
  })

  describe('Layout Integration', () => {
    it('should wrap content in AppLayout component', () => {
      const wrapper = mount(Dashboard, {
        global: {
          plugins: [router, pinia],
          stubs: {
            AppLayout: false
          }
        }
      })

      const layout = wrapper.findComponent(AppLayout)
      expect(layout.exists()).toBe(true)

      // Dashboard content should be inside AppLayout
      const dashboardContent = layout.find('.dashboard')
      expect(dashboardContent.exists()).toBe(true)
    })
  })

  describe('Smoke Tests', () => {
    it('should render without errors', () => {
      expect(() => {
        mount(Dashboard, {
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
      const wrapper = mount(Dashboard, {
        global: {
          plugins: [router, pinia],
          stubs: {
            AppLayout: false
          }
        }
      })

      expect(wrapper.find('.dashboard').exists()).toBe(true)
      expect(wrapper.find('h1').exists()).toBe(true)
      expect(wrapper.find('.welcome').exists()).toBe(true)
      expect(wrapper.find('.info-box').exists()).toBe(true)
    })

    it('should handle various user data formats', () => {
      const authStore = useAuthStore()

      // Test with minimal user data
      authStore.user = {
        id: '1',
        email: 'min@example.com',
        is_active: true
      }

      const wrapper = mount(Dashboard, {
        global: {
          plugins: [router, pinia],
          stubs: {
            AppLayout: false
          }
        }
      })

      expect(wrapper.find('.dashboard').exists()).toBe(true)

      // Test with full user data
      authStore.user = {
        id: '2',
        email: 'full@example.com',
        is_active: false,
        created_at: '2024-01-01T00:00:00Z'
      }

      expect(wrapper.find('.dashboard').exists()).toBe(true)
    })

    it('should render consistently with different user states', async () => {
      const authStore = useAuthStore()

      // Active user
      authStore.user = {
        id: '1',
        email: 'active@example.com',
        is_active: true
      }

      const wrapper = mount(Dashboard, {
        global: {
          plugins: [router, pinia],
          stubs: {
            AppLayout: false
          }
        }
      })

      await wrapper.vm.$nextTick()
      expect(wrapper.find('.dashboard').exists()).toBe(true)

      // Inactive user
      authStore.user = {
        id: '2',
        email: 'inactive@example.com',
        is_active: false
      }
      await wrapper.vm.$nextTick()
      expect(wrapper.find('.dashboard').exists()).toBe(true)
    })
  })
})
