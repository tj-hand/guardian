<script setup lang="ts">
import { getBrandingConfig } from '@/config/branding'

const branding = getBrandingConfig()
const currentYear = new Date().getFullYear()
</script>

<template>
  <footer class="app-footer">
    <div class="footer-container">
      <div class="footer-content">
        <p class="copyright">
          &copy; {{ currentYear }} {{ branding.appName }}. All rights reserved.
        </p>

        <nav class="footer-links">
          <a href="#" class="footer-link">Privacy Policy</a>
          <span class="separator">|</span>
          <a href="#" class="footer-link">Terms of Service</a>
          <span class="separator">|</span>
          <a href="#" class="footer-link">Contact</a>
        </nav>
      </div>

      <div class="footer-info">
        <p class="powered-by">
          Powered by Email Token Authentication System
        </p>
      </div>
    </div>
  </footer>
</template>

<style scoped>
.app-footer {
  background: var(--color-background-card);
  border-top: 1px solid var(--color-border);
  margin-top: auto;
}

.footer-container {
  max-width: 1400px;
  margin: 0 auto;
  padding: 2rem;
}

.footer-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 1rem;
  margin-bottom: 1rem;
}

.copyright {
  color: var(--color-text-secondary);
  font-size: 0.9rem;
  margin: 0;
}

.footer-links {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.footer-link {
  color: var(--color-text-secondary);
  text-decoration: none;
  font-size: 0.9rem;
  transition: color 0.2s;
}

.footer-link:hover {
  color: var(--color-primary);
}

.separator {
  color: var(--color-border);
  font-size: 0.9rem;
}

.footer-info {
  text-align: center;
  padding-top: 1rem;
  border-top: 1px solid var(--color-border);
}

.powered-by {
  color: var(--color-text-secondary);
  font-size: 0.85rem;
  margin: 0;
}

@media (max-width: 768px) {
  .footer-container {
    padding: 1.5rem 1rem;
  }

  .footer-content {
    flex-direction: column;
    align-items: center;
    text-align: center;
  }

  .footer-links {
    justify-content: center;
  }
}
</style>
