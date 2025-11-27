import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createRouter, createMemoryHistory } from 'vue-router'
import { createPinia, setActivePinia } from 'pinia'
import AppHeader from '@/components/layout/AppHeader.vue'
import { useAuthStore } from '@/stores/auth'

// Mock branding config
vi.mock('@/config/branding', () => ({
  getBrandingConfig: () => ({
    appName: 'Test App',
    logoUrl: '/test-logo.svg',
    primaryColor: '#007bff'
  })
}))

/**
 * AppHeader Component Tests
 * Tests the header navigation with branding, authentication state, and routing
 */

describe('AppHeader Component', () => {
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
        { path: '/login', name: 'login', component: { template: '<div>Login</div>' } },
        { path: '/dashboard', name: 'dashboard', component: { template: '<div>Dashboard</div>' } }
      ]
    })
  })

  describe('Component Rendering', () => {
    it('should render the header component correctly', () => {
      const wrapper = mount(AppHeader, {
        global: {
          plugins: [router, pinia]
        }
      })

      expect(wrapper.find('.app-header').exists()).toBe(true)
      expect(wrapper.find('.header-container').exists()).toBe(true)
      expect(wrapper.find('.header-left').exists()).toBe(true)
      expect(wrapper.find('.header-nav').exists()).toBe(true)
    })

    it('should display branding elements', () => {
      const wrapper = mount(AppHeader, {
        global: {
          plugins: [router, pinia]
        }
      })

      const logo = wrapper.find('.logo')
      expect(logo.exists()).toBe(true)
      expect(logo.attributes('src')).toBe('/test-logo.svg')
      expect(logo.attributes('alt')).toBe('Test App')

      const appName = wrapper.find('.app-name')
      expect(appName.exists()).toBe(true)
      expect(appName.text()).toBe('Test App')
    })

    it('should handle logo error gracefully', async () => {
      const wrapper = mount(AppHeader, {
        global: {
          plugins: [router, pinia]
        }
      })

      const logo = wrapper.find('.logo')
      await logo.trigger('error')

      // Logo should be hidden on error (display: none applied via inline style)
      expect(logo.element.style.display).toBe('none')
    })
  })

  describe('Navigation Links - Logged Out State', () => {
    it('should show Home and Login links when logged out', () => {
      const wrapper = mount(AppHeader, {
        global: {
          plugins: [router, pinia]
        }
      })

      const authStore = useAuthStore()
      authStore.isAuthenticated = false
      authStore.user = null

      const navLinks = wrapper.findAll('.nav-link')
      const linkTexts = navLinks.map(link => link.text())

      expect(linkTexts).toContain('Home')
      expect(linkTexts).toContain('Login')
      expect(linkTexts).not.toContain('Dashboard')
    })

    it('should not show user menu when logged out', () => {
      const wrapper = mount(AppHeader, {
        global: {
          plugins: [router, pinia]
        }
      })

      const authStore = useAuthStore()
      authStore.isAuthenticated = false

      expect(wrapper.find('.user-menu').exists()).toBe(false)
      expect(wrapper.find('.logout-button').exists()).toBe(false)
    })
  })

  describe('Navigation Links - Logged In State', () => {
    it('should show Home and Dashboard links when logged in', async () => {
      const wrapper = mount(AppHeader, {
        global: {
          plugins: [router, pinia]
        }
      })

      const authStore = useAuthStore()
      authStore.isAuthenticated = true
      authStore.user = { id: '1', email: 'test@example.com', is_active: true }

      await wrapper.vm.$nextTick()

      const navLinks = wrapper.findAll('.nav-link')
      const linkTexts = navLinks.map(link => link.text())

      expect(linkTexts).toContain('Home')
      expect(linkTexts).toContain('Dashboard')
      expect(linkTexts).not.toContain('Login')
    })

    it('should show user menu with email when logged in', async () => {
      const wrapper = mount(AppHeader, {
        global: {
          plugins: [router, pinia]
        }
      })

      const authStore = useAuthStore()
      authStore.isAuthenticated = true
      authStore.user = { id: '1', email: 'user@example.com', is_active: true }

      await wrapper.vm.$nextTick()

      const userMenu = wrapper.find('.user-menu')
      expect(userMenu.exists()).toBe(true)

      const userEmail = wrapper.find('.user-email')
      expect(userEmail.exists()).toBe(true)
      expect(userEmail.text()).toBe('user@example.com')

      const logoutButton = wrapper.find('.logout-button')
      expect(logoutButton.exists()).toBe(true)
      expect(logoutButton.text()).toBe('Logout')
    })
  })

  describe('Navigation Behavior', () => {
    it('should navigate to Home when logo is clicked', async () => {
      const wrapper = mount(AppHeader, {
        global: {
          plugins: [router, pinia]
        }
      })

      const pushSpy = vi.spyOn(router, 'push')
      const logoLink = wrapper.find('.logo-link')

      await logoLink.trigger('click')

      expect(pushSpy).toHaveBeenCalledWith({ name: 'Home' })
    })

    it('should navigate to Home when Home link is clicked', async () => {
      const wrapper = mount(AppHeader, {
        global: {
          plugins: [router, pinia]
        }
      })

      const pushSpy = vi.spyOn(router, 'push')
      const navLinks = wrapper.findAll('.nav-link')
      const homeLink = navLinks.find(link => link.text() === 'Home')

      await homeLink?.trigger('click')

      expect(pushSpy).toHaveBeenCalledWith({ name: 'Home' })
    })

    it('should navigate to Login when Login link is clicked', async () => {
      const wrapper = mount(AppHeader, {
        global: {
          plugins: [router, pinia]
        }
      })

      const authStore = useAuthStore()
      authStore.isAuthenticated = false

      await wrapper.vm.$nextTick()

      const pushSpy = vi.spyOn(router, 'push')
      const navLinks = wrapper.findAll('.nav-link')
      const loginLink = navLinks.find(link => link.text() === 'Login')

      await loginLink?.trigger('click')

      expect(pushSpy).toHaveBeenCalledWith({ name: 'login' })
    })

    it('should navigate to Dashboard when Dashboard link is clicked', async () => {
      const wrapper = mount(AppHeader, {
        global: {
          plugins: [router, pinia]
        }
      })

      const authStore = useAuthStore()
      authStore.isAuthenticated = true
      authStore.user = { id: '1', email: 'test@example.com', is_active: true }

      await wrapper.vm.$nextTick()

      const pushSpy = vi.spyOn(router, 'push')
      const navLinks = wrapper.findAll('.nav-link')
      const dashboardLink = navLinks.find(link => link.text() === 'Dashboard')

      await dashboardLink?.trigger('click')

      expect(pushSpy).toHaveBeenCalledWith({ name: 'dashboard' })
    })
  })

  describe('Active Route Highlighting', () => {
    it('should highlight active Home route', async () => {
      await router.push('/')
      await router.isReady()

      const wrapper = mount(AppHeader, {
        global: {
          plugins: [router, pinia]
        }
      })

      const navLinks = wrapper.findAll('.nav-link')
      const homeLink = navLinks.find(link => link.text() === 'Home')

      expect(homeLink?.classes()).toContain('active')
    })

    it('should highlight active Login route', async () => {
      await router.push('/login')
      await router.isReady()

      const wrapper = mount(AppHeader, {
        global: {
          plugins: [router, pinia]
        }
      })

      const authStore = useAuthStore()
      authStore.isAuthenticated = false

      await wrapper.vm.$nextTick()

      const navLinks = wrapper.findAll('.nav-link')
      const loginLink = navLinks.find(link => link.text() === 'Login')

      expect(loginLink?.classes()).toContain('active')
    })

    it('should highlight active Dashboard route', async () => {
      await router.push('/dashboard')
      await router.isReady()

      const wrapper = mount(AppHeader, {
        global: {
          plugins: [router, pinia]
        }
      })

      const authStore = useAuthStore()
      authStore.isAuthenticated = true
      authStore.user = { id: '1', email: 'test@example.com', is_active: true }

      await wrapper.vm.$nextTick()

      const navLinks = wrapper.findAll('.nav-link')
      const dashboardLink = navLinks.find(link => link.text() === 'Dashboard')

      expect(dashboardLink?.classes()).toContain('active')
    })
  })

  describe('Logout Functionality', () => {
    it('should call logout and redirect to login page', async () => {
      const wrapper = mount(AppHeader, {
        global: {
          plugins: [router, pinia]
        }
      })

      const authStore = useAuthStore()
      authStore.isAuthenticated = true
      authStore.user = { id: '1', email: 'test@example.com', is_active: true }

      await wrapper.vm.$nextTick()

      const logoutSpy = vi.spyOn(authStore, 'logout').mockResolvedValue()
      const pushSpy = vi.spyOn(router, 'push')

      const logoutButton = wrapper.find('.logout-button')
      await logoutButton.trigger('click')

      expect(logoutSpy).toHaveBeenCalled()
      expect(pushSpy).toHaveBeenCalledWith({ name: 'login' })
    })
  })

  describe('Computed Properties', () => {
    it('should compute isLoggedIn correctly', async () => {
      const wrapper = mount(AppHeader, {
        global: {
          plugins: [router, pinia]
        }
      })

      const authStore = useAuthStore()

      // Initially logged out
      authStore.isAuthenticated = false
      await wrapper.vm.$nextTick()
      expect(wrapper.find('.user-menu').exists()).toBe(false)

      // Change to logged in
      authStore.isAuthenticated = true
      authStore.user = { id: '1', email: 'test@example.com', is_active: true }
      await wrapper.vm.$nextTick()
      expect(wrapper.find('.user-menu').exists()).toBe(true)
    })

    it('should compute userEmail correctly', async () => {
      const wrapper = mount(AppHeader, {
        global: {
          plugins: [router, pinia]
        }
      })

      const authStore = useAuthStore()
      authStore.isAuthenticated = true
      authStore.user = { id: '1', email: 'custom@example.com', is_active: true }

      await wrapper.vm.$nextTick()

      const userEmail = wrapper.find('.user-email')
      expect(userEmail.text()).toBe('custom@example.com')
    })

    it('should handle missing user email gracefully', async () => {
      const wrapper = mount(AppHeader, {
        global: {
          plugins: [router, pinia]
        }
      })

      const authStore = useAuthStore()
      authStore.isAuthenticated = true
      authStore.user = null

      await wrapper.vm.$nextTick()

      const userEmail = wrapper.find('.user-email')
      if (userEmail.exists()) {
        expect(userEmail.text()).toBe('')
      }
    })
  })
})
