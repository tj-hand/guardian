<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

function handleGetStarted() {
  if (authStore.isAuthenticated) {
    router.push('/dashboard')
  } else {
    router.push('/login')
  }
}
</script>

<template>
  <div class="home-page">
    <div class="hero">
      <img src="/logo.svg" alt="Guardian" class="hero-logo" />
      <h1>Guardian</h1>
      <p class="tagline">Passwordless Authentication</p>
      <p class="description">
        Secure, simple login with 6-digit email codes. No passwords to remember.
      </p>
      <button class="cta-btn" @click="handleGetStarted">
        {{ authStore.isAuthenticated ? 'Go to Dashboard' : 'Get Started' }}
      </button>
    </div>

    <div class="features">
      <div class="feature">
        <div class="feature-icon">&#128274;</div>
        <h3>Passwordless</h3>
        <p>No more password fatigue or credential attacks</p>
      </div>
      <div class="feature">
        <div class="feature-icon">&#9201;</div>
        <h3>Time-Limited</h3>
        <p>6-digit codes expire in minutes for security</p>
      </div>
      <div class="feature">
        <div class="feature-icon">&#128231;</div>
        <h3>Email-Based</h3>
        <p>Codes delivered directly to your inbox</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.home-page {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  background: linear-gradient(135deg, var(--color-background) 0%, var(--color-surface) 100%);
}

.hero {
  text-align: center;
  max-width: 600px;
  margin-bottom: 4rem;
}

.hero-logo {
  width: 96px;
  height: 96px;
  margin-bottom: 1.5rem;
}

.hero h1 {
  font-size: 3rem;
  font-weight: 700;
  color: var(--color-text);
  margin-bottom: 0.5rem;
}

.tagline {
  font-size: 1.25rem;
  color: var(--color-primary);
  font-weight: 500;
  margin-bottom: 1rem;
}

.description {
  font-size: 1.125rem;
  color: var(--color-text-muted);
  margin-bottom: 2rem;
  line-height: 1.6;
}

.cta-btn {
  padding: 1rem 2rem;
  font-size: 1.125rem;
  font-weight: 600;
  background: var(--color-primary);
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.cta-btn:hover {
  background: var(--color-primary-dark);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
}

.features {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 2rem;
  max-width: 800px;
  width: 100%;
}

.feature {
  text-align: center;
  padding: 2rem;
  background: var(--color-surface);
  border-radius: 12px;
  border: 1px solid var(--color-border);
}

.feature-icon {
  font-size: 2.5rem;
  margin-bottom: 1rem;
}

.feature h3 {
  font-size: 1.125rem;
  font-weight: 600;
  color: var(--color-text);
  margin-bottom: 0.5rem;
}

.feature p {
  color: var(--color-text-muted);
  font-size: 0.875rem;
}
</style>
