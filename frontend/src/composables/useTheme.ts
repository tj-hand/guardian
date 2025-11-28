/**
 * useTheme Composable
 * Provides reactive theme management for white-label customization
 * Allows runtime theme switching and branding configuration access
 */

import { ref, computed, onMounted } from 'vue'
import { getBrandingConfig, applyBrandingTheme, type BrandingConfig } from '@/config/branding'

// Reactive branding configuration
const brandingConfig = ref<BrandingConfig>(getBrandingConfig())

// Track if theme has been initialized
const themeInitialized = ref(false)

export function useTheme() {
  /**
   * Get the current branding configuration
   */
  const branding = computed(() => brandingConfig.value)

  /**
   * Check if theme is initialized
   */
  const isInitialized = computed(() => themeInitialized.value)

  /**
   * Initialize the theme system
   * Call this once on app mount
   */
  const initializeTheme = () => {
    if (themeInitialized.value) return

    brandingConfig.value = getBrandingConfig()
    applyBrandingTheme(brandingConfig.value)
    themeInitialized.value = true
  }

  /**
   * Update theme with new branding configuration
   * Useful for runtime theme switching or A/B testing
   */
  const updateTheme = (newConfig: Partial<BrandingConfig>) => {
    brandingConfig.value = {
      ...brandingConfig.value,
      ...newConfig
    }
    applyBrandingTheme(brandingConfig.value)
  }

  /**
   * Reset theme to environment defaults
   */
  const resetTheme = () => {
    brandingConfig.value = getBrandingConfig()
    applyBrandingTheme(brandingConfig.value)
  }

  /**
   * Get a specific theme color with fallback
   */
  const getColor = (colorName: keyof BrandingConfig, fallback = '#000000'): string => {
    const value = brandingConfig.value[colorName]
    return typeof value === 'string' ? value : fallback
  }

  /**
   * Check if a feature is enabled based on branding config
   */
  const isFeatureEnabled = (feature: keyof BrandingConfig): boolean => {
    const value = brandingConfig.value[feature]
    return Boolean(value)
  }

  /**
   * Get social media links that are configured
   */
  const socialLinks = computed(() => {
    const links = []
    if (brandingConfig.value.twitterUrl) {
      links.push({ name: 'Twitter', url: brandingConfig.value.twitterUrl })
    }
    if (brandingConfig.value.linkedinUrl) {
      links.push({ name: 'LinkedIn', url: brandingConfig.value.linkedinUrl })
    }
    if (brandingConfig.value.githubUrl) {
      links.push({ name: 'GitHub', url: brandingConfig.value.githubUrl })
    }
    return links
  })

  /**
   * Auto-initialize on mount (optional)
   * Components can call this in their onMounted hook
   */
  onMounted(() => {
    if (!themeInitialized.value) {
      initializeTheme()
    }
  })

  return {
    // State
    branding,
    isInitialized,
    socialLinks,

    // Methods
    initializeTheme,
    updateTheme,
    resetTheme,
    getColor,
    isFeatureEnabled
  }
}
