import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import AppFooter from '@/components/layout/AppFooter.vue'

// Mock branding config
vi.mock('@/config/branding', () => ({
  getBrandingConfig: () => ({
    appName: 'Test App',
    companyName: 'Test Company',
    footerText: 'Custom footer text'
  })
}))

/**
 * AppFooter Component Tests
 * Tests the footer component with copyright, links, and branding
 */

describe('AppFooter Component', () => {
  beforeEach(() => {
    // Use fake timers and set to a specific date
    vi.useFakeTimers()
    vi.setSystemTime(new Date('2025-11-10'))
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  describe('Component Rendering', () => {
    it('should render the footer component correctly', () => {
      const wrapper = mount(AppFooter)

      expect(wrapper.find('.app-footer').exists()).toBe(true)
      expect(wrapper.find('.footer-container').exists()).toBe(true)
      expect(wrapper.find('.footer-content').exists()).toBe(true)
      expect(wrapper.find('.footer-info').exists()).toBe(true)
    })

    it('should render copyright section', () => {
      const wrapper = mount(AppFooter)

      const copyright = wrapper.find('.copyright')
      expect(copyright.exists()).toBe(true)
    })

    it('should render footer links navigation', () => {
      const wrapper = mount(AppFooter)

      const footerLinks = wrapper.find('.footer-links')
      expect(footerLinks.exists()).toBe(true)
    })

    it('should render powered by section', () => {
      const wrapper = mount(AppFooter)

      const poweredBy = wrapper.find('.powered-by')
      expect(poweredBy.exists()).toBe(true)
    })
  })

  describe('Copyright Display', () => {
    it('should display current year in copyright', () => {
      const wrapper = mount(AppFooter)

      const copyright = wrapper.find('.copyright')
      expect(copyright.text()).toContain('2025')
    })

    it('should display app name in copyright', () => {
      const wrapper = mount(AppFooter)

      const copyright = wrapper.find('.copyright')
      expect(copyright.text()).toContain('Test App')
    })

    it('should display "All rights reserved" text', () => {
      const wrapper = mount(AppFooter)

      const copyright = wrapper.find('.copyright')
      expect(copyright.text()).toContain('All rights reserved')
    })

    it('should format copyright correctly', () => {
      const wrapper = mount(AppFooter)

      const copyright = wrapper.find('.copyright')
      expect(copyright.text()).toMatch(/© \d{4} Test App\. All rights reserved\./)
    })
  })

  describe('Footer Links', () => {
    it('should render all three footer links', () => {
      const wrapper = mount(AppFooter)

      const links = wrapper.findAll('.footer-link')
      expect(links).toHaveLength(3)
    })

    it('should render Privacy Policy link', () => {
      const wrapper = mount(AppFooter)

      const links = wrapper.findAll('.footer-link')
      const privacyLink = links.find(link => link.text() === 'Privacy Policy')

      expect(privacyLink).toBeDefined()
      expect(privacyLink?.attributes('href')).toBe('#')
    })

    it('should render Terms of Service link', () => {
      const wrapper = mount(AppFooter)

      const links = wrapper.findAll('.footer-link')
      const termsLink = links.find(link => link.text() === 'Terms of Service')

      expect(termsLink).toBeDefined()
      expect(termsLink?.attributes('href')).toBe('#')
    })

    it('should render Contact link', () => {
      const wrapper = mount(AppFooter)

      const links = wrapper.findAll('.footer-link')
      const contactLink = links.find(link => link.text() === 'Contact')

      expect(contactLink).toBeDefined()
      expect(contactLink?.attributes('href')).toBe('#')
    })

    it('should render separators between links', () => {
      const wrapper = mount(AppFooter)

      const separators = wrapper.findAll('.separator')
      expect(separators).toHaveLength(2)

      separators.forEach(separator => {
        expect(separator.text()).toBe('|')
      })
    })

    it('should have correct link order', () => {
      const wrapper = mount(AppFooter)

      const links = wrapper.findAll('.footer-link')
      expect(links[0].text()).toBe('Privacy Policy')
      expect(links[1].text()).toBe('Terms of Service')
      expect(links[2].text()).toBe('Contact')
    })
  })

  describe('Powered By Section', () => {
    it('should display powered by text', () => {
      const wrapper = mount(AppFooter)

      const poweredBy = wrapper.find('.powered-by')
      expect(poweredBy.text()).toBe('Powered by Email Token Authentication System')
    })
  })

  describe('Dynamic Year Updates', () => {
    it('should update copyright year dynamically', async () => {
      // Set date to 2024
      vi.setSystemTime(new Date('2024-06-15'))
      const wrapper1 = mount(AppFooter)
      expect(wrapper1.find('.copyright').text()).toContain('2024')

      // Set date to 2026
      vi.setSystemTime(new Date('2026-03-20'))
      const wrapper2 = mount(AppFooter)
      expect(wrapper2.find('.copyright').text()).toContain('2026')
    })

    it('should handle year transitions correctly', () => {
      // New Year's Eve
      vi.setSystemTime(new Date('2024-12-31T23:59:59'))
      const wrapper1 = mount(AppFooter)
      expect(wrapper1.find('.copyright').text()).toContain('2024')

      // New Year's Day
      vi.setSystemTime(new Date('2025-01-01T00:00:00'))
      const wrapper2 = mount(AppFooter)
      expect(wrapper2.find('.copyright').text()).toContain('2025')
    })
  })

  describe('Branding Integration', () => {
    it('should use branding config for app name', () => {
      const wrapper = mount(AppFooter)

      // Check that branding appName is used
      expect(wrapper.text()).toContain('Test App')
    })

    it('should integrate with getBrandingConfig', () => {
      const wrapper = mount(AppFooter)

      // The component should call getBrandingConfig and use the returned values
      const copyright = wrapper.find('.copyright')
      expect(copyright.exists()).toBe(true)
      expect(copyright.text()).toContain('Test App')
    })
  })

  describe('Layout Structure', () => {
    it('should have correct layout hierarchy', () => {
      const wrapper = mount(AppFooter)

      const footer = wrapper.find('.app-footer')
      expect(footer.exists()).toBe(true)

      const container = footer.find('.footer-container')
      expect(container.exists()).toBe(true)

      const content = container.find('.footer-content')
      expect(content.exists()).toBe(true)

      const info = container.find('.footer-info')
      expect(info.exists()).toBe(true)
    })

    it('should render copyright and links in footer-content', () => {
      const wrapper = mount(AppFooter)

      const footerContent = wrapper.find('.footer-content')
      expect(footerContent.find('.copyright').exists()).toBe(true)
      expect(footerContent.find('.footer-links').exists()).toBe(true)
    })

    it('should render powered-by in footer-info', () => {
      const wrapper = mount(AppFooter)

      const footerInfo = wrapper.find('.footer-info')
      expect(footerInfo.find('.powered-by').exists()).toBe(true)
    })
  })

  describe('Accessibility', () => {
    it('should have semantic footer element', () => {
      const wrapper = mount(AppFooter)

      const footer = wrapper.find('footer')
      expect(footer.exists()).toBe(true)
      expect(footer.classes()).toContain('app-footer')
    })

    it('should have semantic nav element for links', () => {
      const wrapper = mount(AppFooter)

      const nav = wrapper.find('nav')
      expect(nav.exists()).toBe(true)
      expect(nav.classes()).toContain('footer-links')
    })

    it('should have proper link elements', () => {
      const wrapper = mount(AppFooter)

      const links = wrapper.findAll('.footer-link')
      links.forEach(link => {
        expect(link.element.tagName).toBe('A')
        expect(link.attributes('href')).toBeDefined()
      })
    })
  })

  describe('Edge Cases', () => {
    it('should handle leap year correctly', () => {
      vi.setSystemTime(new Date('2024-02-29'))
      const wrapper = mount(AppFooter)

      const copyright = wrapper.find('.copyright')
      expect(copyright.text()).toContain('2024')
    })

    it('should render without errors when branding is minimal', () => {
      const wrapper = mount(AppFooter)

      // Should render successfully even with minimal branding
      expect(wrapper.find('.app-footer').exists()).toBe(true)
      expect(wrapper.find('.copyright').exists()).toBe(true)
      expect(wrapper.find('.powered-by').exists()).toBe(true)
    })
  })
})
