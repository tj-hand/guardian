import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createRouter, createMemoryHistory } from 'vue-router'
import { createPinia, setActivePinia } from 'pinia'
import AppLayout from '@/components/layout/AppLayout.vue'
import AppHeader from '@/components/layout/AppHeader.vue'
import AppFooter from '@/components/layout/AppFooter.vue'

// Mock branding config
vi.mock('@/config/branding', () => ({
  getBrandingConfig: () => ({
    appName: 'Test App',
    logoUrl: '/test-logo.svg',
    primaryColor: '#007bff'
  })
}))

/**
 * AppLayout Component Tests
 * Tests the main layout wrapper that includes header, footer, and content slot
 */

describe('AppLayout Component', () => {
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
        { path: '/', name: 'Home', component: { template: '<div>Home</div>' } }
      ]
    })
  })

  describe('Component Rendering', () => {
    it('should render the component correctly', () => {
      const wrapper = mount(AppLayout, {
        global: {
          stubs: {
            AppHeader: true,
            AppFooter: true
          }
        }
      })

      expect(wrapper.find('.app-layout').exists()).toBe(true)
      expect(wrapper.find('.main-content').exists()).toBe(true)
    })

    it('should render AppHeader component', () => {
      const wrapper = mount(AppLayout, {
        global: {
          plugins: [router, pinia],
          stubs: {
            AppHeader: false,
            AppFooter: true
          }
        }
      })

      expect(wrapper.findComponent(AppHeader).exists()).toBe(true)
    })

    it('should render AppFooter component', () => {
      const wrapper = mount(AppLayout, {
        global: {
          stubs: {
            AppHeader: true,
            AppFooter: false
          }
        }
      })

      expect(wrapper.findComponent(AppFooter).exists()).toBe(true)
    })
  })

  describe('Slot Content', () => {
    it('should render slot content in main-content area', () => {
      const wrapper = mount(AppLayout, {
        slots: {
          default: '<div class="test-content">Test Content</div>'
        },
        global: {
          stubs: {
            AppHeader: true,
            AppFooter: true
          }
        }
      })

      const mainContent = wrapper.find('.main-content')
      expect(mainContent.exists()).toBe(true)
      expect(mainContent.find('.test-content').exists()).toBe(true)
      expect(mainContent.find('.test-content').text()).toBe('Test Content')
    })

    it('should render multiple elements in slot', () => {
      const wrapper = mount(AppLayout, {
        slots: {
          default: `
            <div class="element-1">Element 1</div>
            <div class="element-2">Element 2</div>
            <div class="element-3">Element 3</div>
          `
        },
        global: {
          stubs: {
            AppHeader: true,
            AppFooter: true
          }
        }
      })

      expect(wrapper.find('.element-1').exists()).toBe(true)
      expect(wrapper.find('.element-2').exists()).toBe(true)
      expect(wrapper.find('.element-3').exists()).toBe(true)
    })

    it('should handle empty slot gracefully', () => {
      const wrapper = mount(AppLayout, {
        global: {
          stubs: {
            AppHeader: true,
            AppFooter: true
          }
        }
      })

      const mainContent = wrapper.find('.main-content')
      expect(mainContent.exists()).toBe(true)
      expect(mainContent.text()).toBe('')
    })
  })

  describe('Layout Structure', () => {
    it('should have correct layout structure order', () => {
      const wrapper = mount(AppLayout, {
        slots: {
          default: '<div class="page-content">Page Content</div>'
        },
        global: {
          plugins: [router, pinia],
          stubs: {
            AppHeader: false,
            AppFooter: false
          }
        }
      })

      const layout = wrapper.find('.app-layout')
      const children = layout.element.children

      // Verify order: Header -> Main -> Footer
      expect(children[0].tagName).toBe('HEADER')
      expect(children[1].tagName).toBe('MAIN')
      expect(children[2].tagName).toBe('FOOTER')
    })

    it('should apply correct CSS classes', () => {
      const wrapper = mount(AppLayout, {
        global: {
          stubs: {
            AppHeader: true,
            AppFooter: true
          }
        }
      })

      const layout = wrapper.find('.app-layout')
      expect(layout.classes()).toContain('app-layout')

      const main = wrapper.find('.main-content')
      expect(main.classes()).toContain('main-content')
    })
  })

  describe('Layout Behavior', () => {
    it('should maintain layout structure with dynamic content', async () => {
      const wrapper = mount(AppLayout, {
        slots: {
          default: '<div class="content">Initial Content</div>'
        },
        global: {
          stubs: {
            AppHeader: true,
            AppFooter: true
          }
        }
      })

      expect(wrapper.find('.content').text()).toBe('Initial Content')

      // Simulate content change
      await wrapper.setProps({
        slots: {
          default: '<div class="content">Updated Content</div>'
        }
      })

      // Layout structure should remain intact
      expect(wrapper.find('.app-layout').exists()).toBe(true)
      expect(wrapper.find('.main-content').exists()).toBe(true)
    })
  })
})
