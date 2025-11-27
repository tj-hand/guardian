<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const email = ref('')
const isSubmitting = ref(false)

async function handleSubmit() {
  if (!email.value || isSubmitting.value) return

  isSubmitting.value = true
  authStore.clearError()

  try {
    await authStore.requestToken(email.value)
    // Navigate to token input
    router.push({ path: '/login', query: { email: email.value } })
  } catch {
    // Error is handled in store
  } finally {
    isSubmitting.value = false
  }
}
</script>

<template>
  <div class="email-input-container">
    <div class="auth-header">
      <img src="/logo.svg" alt="Guardian" class="logo" />
      <h1>Welcome to Guardian</h1>
      <p>Enter your email to receive a login code</p>
    </div>

    <form @submit.prevent="handleSubmit" class="auth-form">
      <div class="form-group">
        <label for="email">Email Address</label>
        <input
          id="email"
          v-model="email"
          type="email"
          placeholder="you@example.com"
          required
          autocomplete="email"
          :disabled="isSubmitting"
        />
      </div>

      <div v-if="authStore.error" class="error-message">
        {{ authStore.error }}
      </div>

      <button type="submit" class="submit-btn" :disabled="isSubmitting || !email">
        <span v-if="isSubmitting">Sending...</span>
        <span v-else>Send Login Code</span>
      </button>
    </form>

    <div class="auth-footer">
      <p>No password needed. We'll send a 6-digit code to your email.</p>
    </div>
  </div>
</template>

<style scoped>
.email-input-container {
  max-width: 400px;
  margin: 0 auto;
  padding: 2rem;
}

.auth-header {
  text-align: center;
  margin-bottom: 2rem;
}

.logo {
  width: 64px;
  height: 64px;
  margin-bottom: 1rem;
}

.auth-header h1 {
  font-size: 1.5rem;
  color: var(--color-text);
  margin-bottom: 0.5rem;
}

.auth-header p {
  color: var(--color-text-muted);
}

.auth-form {
  background: var(--color-surface);
  border-radius: 8px;
  padding: 1.5rem;
  border: 1px solid var(--color-border);
}

.form-group {
  margin-bottom: 1rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 500;
  color: var(--color-text);
}

.form-group input {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid var(--color-border);
  border-radius: 4px;
  font-size: 1rem;
  background: var(--color-background);
  color: var(--color-text);
}

.form-group input:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px var(--color-primary-light);
}

.form-group input:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.error-message {
  background: var(--color-error-bg);
  color: var(--color-error);
  padding: 0.75rem;
  border-radius: 4px;
  margin-bottom: 1rem;
  font-size: 0.875rem;
}

.submit-btn {
  width: 100%;
  padding: 0.75rem;
  background: var(--color-primary);
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.2s;
}

.submit-btn:hover:not(:disabled) {
  background: var(--color-primary-dark);
}

.submit-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.auth-footer {
  text-align: center;
  margin-top: 1.5rem;
  color: var(--color-text-muted);
  font-size: 0.875rem;
}
</style>
