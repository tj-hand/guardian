<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { getBrandingConfig } from '@/config/branding'
import AppLayout from '@/components/layout/AppLayout.vue'

const router = useRouter()
const authStore = useAuthStore()
const branding = getBrandingConfig()

const isLoggedIn = computed(() => authStore.isLoggedIn)

const goToLogin = () => {
  router.push({ name: 'login' })
}

const goToDashboard = () => {
  router.push({ name: 'dashboard' })
}
</script>

<template>
  <AppLayout>
    <div class="home">
      <div class="hero">
        <h1>Welcome to {{ branding.appName }}</h1>
        <p class="subtitle">
          Secure, passwordless authentication using email verification tokens
        </p>

        <div class="actions">
          <button v-if="!isLoggedIn" class="btn btn-primary" @click="goToLogin">
            Get Started
          </button>
          <button v-else class="btn btn-primary" @click="goToDashboard">
            Go to Dashboard
          </button>
        </div>
      </div>

      <div class="features">
        <div class="feature">
          <h3>Simple & Secure</h3>
          <p>No passwords to remember. Just enter your email and receive a verification code.</p>
        </div>

        <div class="feature">
          <h3>Fast Access</h3>
          <p>6-digit tokens delivered instantly to your email. Auto-submit for seamless experience.</p>
        </div>

        <div class="feature">
          <h3>Privacy First</h3>
          <p>Your data is protected. Tokens expire after 2 minutes and are single-use only.</p>
        </div>
      </div>
    </div>
  </AppLayout>
</template>

<style scoped>
.home {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
}

.hero {
  text-align: center;
  padding: 4rem 2rem;
}

.hero h1 {
  font-size: 2.5rem;
  font-weight: 700;
  margin-bottom: 1rem;
  color: var(--color-text-primary);
}

.subtitle {
  font-size: 1.25rem;
  color: var(--color-text-secondary);
  margin-bottom: 2rem;
}

.actions {
  display: flex;
  justify-content: center;
  gap: 1rem;
  margin-top: 2rem;
}

.features {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 2rem;
  margin-top: 4rem;
  padding: 2rem 0;
}

.feature {
  padding: 2rem;
  background: var(--color-background-card);
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.feature h3 {
  font-size: 1.5rem;
  font-weight: 600;
  margin-bottom: 1rem;
  color: var(--color-primary);
}

.feature p {
  color: var(--color-text-secondary);
  line-height: 1.6;
}

@media (max-width: 768px) {
  .hero h1 {
    font-size: 2rem;
  }

  .subtitle {
    font-size: 1rem;
  }

  .features {
    grid-template-columns: 1fr;
  }
}
</style>
