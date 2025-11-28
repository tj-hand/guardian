<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const email = ref('')
const loading = ref(false)
const error = ref('')
const success = ref(false)
const rateLimitInfo = ref<{ retryAfter?: number; attemptsRemaining?: number } | null>(null)

// Email validation
const emailError = computed(() => {
  if (!email.value) return ''
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  return emailRegex.test(email.value) ? '' : 'Please enter a valid email address'
})

const isValid = computed(() => email.value && !emailError.value)

// Submit handler
const handleSubmit = async () => {
  if (!isValid.value || loading.value) return

  loading.value = true
  error.value = ''
  success.value = false
  rateLimitInfo.value = null

  try {
    await authStore.requestToken(email.value)
    success.value = true

    // Navigate to token input after 1.5 seconds
    setTimeout(() => {
      router.push({ name: 'login', query: { email: email.value } })
    }, 1500)

  } catch (err: any) {
    if (err.response?.status === 429) {
      // Rate limit error
      const data = err.response.data
      error.value = data.detail || 'Too many requests. Please try again later.'
      rateLimitInfo.value = {
        retryAfter: data.retry_after,
        attemptsRemaining: data.attempts_remaining
      }
    } else {
      error.value = err.response?.data?.detail || 'Failed to send code. Please try again.'
    }
  } finally {
    loading.value = false
  }
}

// Format retry time
const formatRetryTime = (seconds: number) => {
  const minutes = Math.ceil(seconds / 60)
  return minutes === 1 ? '1 minute' : `${minutes} minutes`
}
</script>

<template>
  <div class="email-input-container">
    <h2>Login</h2>
    <p class="subtitle">Enter your email to receive a verification code</p>

    <form class="email-form" @submit.prevent="handleSubmit">
      <div class="form-group">
        <label for="email">Email Address</label>
        <input
          id="email"
          v-model="email"
          type="email"
          placeholder="you@example.com"
          :disabled="loading || success"
          :class="{ error: emailError && email }"
          autocomplete="email"
          autofocus
        />
        <span v-if="emailError && email" class="field-error">{{ emailError }}</span>
      </div>

      <button
        type="submit"
        :disabled="!isValid || loading || success"
        class="submit-button"
      >
        <span v-if="loading" class="spinner"></span>
        <span v-else>{{ success ? 'Code Sent' : 'Send Code' }}</span>
      </button>
    </form>

    <!-- Success Message -->
    <div v-if="success" class="success-message">
      <p>Check your email for a 6-digit verification code</p>
      <p class="redirect-text">Redirecting to code entry...</p>
    </div>

    <!-- Error Message -->
    <div v-if="error" class="error-message">
      <p>{{ error }}</p>
      <p v-if="rateLimitInfo?.retryAfter" class="retry-info">
        Please wait {{ formatRetryTime(rateLimitInfo.retryAfter) }} before trying again.
      </p>
      <p v-else-if="rateLimitInfo?.attemptsRemaining !== undefined" class="retry-info">
        {{ rateLimitInfo.attemptsRemaining }} attempts remaining
      </p>
    </div>
  </div>
</template>

<style scoped>
.email-input-container {
  max-width: 400px;
  margin: 0 auto;
  padding: 2rem;
}

h2 {
  margin-bottom: 0.5rem;
  color: var(--color-heading);
}

.subtitle {
  color: var(--color-text-muted);
  margin-bottom: 2rem;
}

.email-form {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

label {
  font-weight: 500;
  color: var(--color-text);
}

input {
  padding: 0.75rem;
  font-size: 1rem;
  border: 2px solid var(--color-border);
  border-radius: 8px;
  transition: border-color 0.2s;
}

input:focus {
  outline: none;
  border-color: var(--color-primary);
}

input.error {
  border-color: var(--color-error);
}

input:disabled {
  background-color: var(--color-background-muted);
  cursor: not-allowed;
}

.field-error {
  color: var(--color-error);
  font-size: 0.875rem;
}

.submit-button {
  padding: 0.875rem;
  font-size: 1rem;
  font-weight: 600;
  color: white;
  background-color: var(--color-primary);
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: background-color 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
}

.submit-button:hover:not(:disabled) {
  background-color: var(--color-primary-dark);
}

.submit-button:disabled {
  background-color: var(--color-border);
  cursor: not-allowed;
}

.spinner {
  width: 20px;
  height: 20px;
  border: 3px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.success-message {
  margin-top: 1.5rem;
  padding: 1rem;
  background-color: var(--color-success-bg);
  border: 1px solid var(--color-success);
  border-radius: 8px;
  color: var(--color-success);
}

.redirect-text {
  margin-top: 0.5rem;
  font-size: 0.875rem;
  opacity: 0.8;
}

.error-message {
  margin-top: 1.5rem;
  padding: 1rem;
  background-color: var(--color-error-bg);
  border: 1px solid var(--color-error);
  border-radius: 8px;
  color: var(--color-error);
}

.retry-info {
  margin-top: 0.5rem;
  font-size: 0.875rem;
}

@media (max-width: 480px) {
  .email-input-container {
    padding: 1rem;
  }
}
</style>
