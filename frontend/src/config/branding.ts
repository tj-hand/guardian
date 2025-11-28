/**
 * Branding configuration loader
 * Comprehensive white-label system for customizing app appearance
 * Loads branding from environment variables and applies theme to the application
 */

export interface BrandingConfig {
  // Application Identity
  appName: string
  companyName: string
  tagline: string

  // Visual Assets
  logoUrl: string
  faviconUrl: string

  // Color Scheme
  primaryColor: string
  secondaryColor: string
  accentColor: string
  successColor: string
  errorColor: string
  warningColor: string

  // Typography
  fontFamily: string
  headingFontFamily: string

  // Contact & Support
  supportEmail: string
  supportUrl: string

  // Social Media
  twitterUrl: string
  linkedinUrl: string
  githubUrl: string

  // Footer
  footerText: string
  showPoweredBy: boolean

  // Authentication
  tokenLength: number
}

/**
 * Load branding configuration from environment variables with sensible defaults
 */
export const getBrandingConfig = (): BrandingConfig => {
  return {
    // Application Identity
    appName: import.meta.env.VITE_APP_NAME || 'Email Token Auth',
    companyName: import.meta.env.VITE_COMPANY_NAME || 'My Company',
    tagline: import.meta.env.VITE_APP_TAGLINE || 'Secure passwordless authentication',

    // Visual Assets
    logoUrl: import.meta.env.VITE_BRAND_LOGO_URL || '/logo.svg',
    faviconUrl: import.meta.env.VITE_BRAND_FAVICON_URL || '/favicon.ico',

    // Color Scheme
    primaryColor: import.meta.env.VITE_BRAND_PRIMARY_COLOR || '#007bff',
    secondaryColor: import.meta.env.VITE_BRAND_SECONDARY_COLOR || '#6c757d',
    accentColor: import.meta.env.VITE_BRAND_ACCENT_COLOR || '#28a745',
    successColor: import.meta.env.VITE_BRAND_SUCCESS_COLOR || '#28a745',
    errorColor: import.meta.env.VITE_BRAND_ERROR_COLOR || '#dc3545',
    warningColor: import.meta.env.VITE_BRAND_WARNING_COLOR || '#ffc107',

    // Typography
    fontFamily: import.meta.env.VITE_BRAND_FONT_FAMILY || '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
    headingFontFamily: import.meta.env.VITE_BRAND_HEADING_FONT_FAMILY || 'inherit',

    // Contact & Support
    supportEmail: import.meta.env.VITE_SUPPORT_EMAIL || 'support@example.com',
    supportUrl: import.meta.env.VITE_SUPPORT_URL || '',

    // Social Media
    twitterUrl: import.meta.env.VITE_TWITTER_URL || '',
    linkedinUrl: import.meta.env.VITE_LINKEDIN_URL || '',
    githubUrl: import.meta.env.VITE_GITHUB_URL || '',

    // Footer
    footerText: import.meta.env.VITE_FOOTER_TEXT || '',
    showPoweredBy: import.meta.env.VITE_SHOW_POWERED_BY !== 'false',

    // Authentication
    tokenLength: parseInt(import.meta.env.VITE_TOKEN_LENGTH || '6', 10)
  }
}

/**
 * Apply branding theme to the application
 * Sets CSS custom properties for dynamic theming
 * This allows real-time theme switching without page reload
 */
export const applyBrandingTheme = (config?: BrandingConfig): void => {
  const branding = config || getBrandingConfig()
  const root = document.documentElement

  // Primary Colors with auto-generated variants
  root.style.setProperty('--color-primary', branding.primaryColor)
  root.style.setProperty('--color-primary-dark', darkenColor(branding.primaryColor, 10))
  root.style.setProperty('--color-primary-light', lightenColor(branding.primaryColor, 10))
  root.style.setProperty('--color-primary-alpha-10', hexToRgba(branding.primaryColor, 0.1))
  root.style.setProperty('--color-primary-alpha-20', hexToRgba(branding.primaryColor, 0.2))

  // Secondary Colors
  root.style.setProperty('--color-secondary', branding.secondaryColor)
  root.style.setProperty('--color-secondary-dark', darkenColor(branding.secondaryColor, 10))
  root.style.setProperty('--color-secondary-light', lightenColor(branding.secondaryColor, 10))

  // Accent Colors
  root.style.setProperty('--color-accent', branding.accentColor)
  root.style.setProperty('--color-accent-dark', darkenColor(branding.accentColor, 10))
  root.style.setProperty('--color-accent-light', lightenColor(branding.accentColor, 10))

  // Status Colors
  root.style.setProperty('--color-success', branding.successColor)
  root.style.setProperty('--color-success-bg', lightenColor(branding.successColor, 40))
  root.style.setProperty('--color-success-border', lightenColor(branding.successColor, 30))

  root.style.setProperty('--color-error', branding.errorColor)
  root.style.setProperty('--color-error-bg', lightenColor(branding.errorColor, 40))
  root.style.setProperty('--color-error-border', lightenColor(branding.errorColor, 30))

  root.style.setProperty('--color-warning', branding.warningColor)
  root.style.setProperty('--color-warning-bg', lightenColor(branding.warningColor, 40))
  root.style.setProperty('--color-warning-border', lightenColor(branding.warningColor, 30))

  // Typography
  root.style.setProperty('--font-family', branding.fontFamily)
  root.style.setProperty('--font-family-heading', branding.headingFontFamily)

  // Update document metadata
  document.title = branding.appName
  updateFavicon(branding.faviconUrl)
}

/**
 * Update the favicon dynamically
 */
const updateFavicon = (faviconUrl: string): void => {
  const link = document.querySelector("link[rel~='icon']") as HTMLLinkElement
  if (link) {
    link.href = faviconUrl
  } else {
    const newLink = document.createElement('link')
    newLink.rel = 'icon'
    newLink.href = faviconUrl
    document.head.appendChild(newLink)
  }
}

/**
 * Darken a hex color by a percentage
 */
const darkenColor = (hex: string, percent: number): string => {
  const num = parseInt(hex.replace('#', ''), 16)
  const amt = Math.round(2.55 * percent)
  const R = Math.max(0, (num >> 16) - amt)
  const G = Math.max(0, ((num >> 8) & 0x00ff) - amt)
  const B = Math.max(0, (num & 0x0000ff) - amt)
  return '#' + ((1 << 24) | (R << 16) | (G << 8) | B).toString(16).slice(1)
}

/**
 * Lighten a hex color by a percentage
 */
const lightenColor = (hex: string, percent: number): string => {
  const num = parseInt(hex.replace('#', ''), 16)
  const amt = Math.round(2.55 * percent)
  const R = Math.min(255, (num >> 16) + amt)
  const G = Math.min(255, ((num >> 8) & 0x00ff) + amt)
  const B = Math.min(255, (num & 0x0000ff) + amt)
  return '#' + ((1 << 24) | (R << 16) | (G << 8) | B).toString(16).slice(1)
}

/**
 * Convert hex color to rgba with alpha channel
 */
const hexToRgba = (hex: string, alpha: number): string => {
  const num = parseInt(hex.replace('#', ''), 16)
  const r = (num >> 16) & 255
  const g = (num >> 8) & 255
  const b = num & 255
  return `rgba(${r}, ${g}, ${b}, ${alpha})`
}
