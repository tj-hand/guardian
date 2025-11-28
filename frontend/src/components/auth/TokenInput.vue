<template>
  <div class="token-input-container">
    <h2>Enter Verification Code</h2>
    <p class="subtitle">
      We sent a 6-digit code to <strong>{{ maskedEmail }}</strong>
    </p>

    <!-- Countdown Timer -->
    <CountdownTimer
      :time-remaining="timeRemaining"
      :is-low-time="isLowTime"
      :is-expired="isExpired"
    />

    <div class="token-inputs" role="group" aria-label="6-digit verification code input">
      <input
        v-for="(_digit, index) in digits"
        :key="index"
        :ref="(el) => (inputRefs[index] = el as HTMLInputElement)"
        v-model="digits[index]"
        type="text"
        inputmode="numeric"
        maxlength="1"
        class="token-digit"
        :disabled="loading"
        :aria-label="`Digit ${index + 1}`"
        @input="handleInput(index, $event)"
        @keydown="handleKeydown(index, $event)"
        @paste="handlePaste(index, $event)"
      />
    </div>

    <div v-if="loading" class="loading">
      <span class="spinner"></span>
      Validating...
    </div>

    <div v-if="errorMessage" class="error-message" role="alert">
      {{ errorMessage }}
    </div>

    <button
      v-if="!loading"
      :disabled="resendCooldown > 0"
      class="resend-button"
      :aria-label="resendCooldown > 0 ? `Resend code available in ${resendCooldown} seconds` : 'Resend code'"
      @click="handleResend"
    >
      {{ resendButtonText }}
    </button>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useTokenTimer } from '@/composables/useTokenTimer'
import CountdownTimer from '@/components/auth/CountdownTimer.vue'

// Props
const props = defineProps<{
  email?: string
}>()

// State
const digits = ref<string[]>(['', '', '', '', '', ''])
const inputRefs = ref<(HTMLInputElement | null)[]>([])
const loading = ref(false)
const errorMessage = ref('')
const resendCooldown = ref(0)

// Router and store
const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

// Token timer (2 minutes / 120 seconds)
const { timeRemaining, isLowTime, isExpired, startTimer, stopTimer } = useTokenTimer()

// Get email from props, route query, or sessionStorage
const email = computed(() => {
  return (
    props.email ||
    (route.query.email as string) ||
    sessionStorage.getItem('auth_email') ||
    ''
  )
})

const maskedEmail = computed(() => {
  if (!email.value) return ''
  const [local, domain] = email.value.split('@')
  if (!local || !domain) return email.value
  return `${local[0]}***@${domain}`
})

const resendButtonText = computed(() => {
  if (resendCooldown.value > 0) {
    return `Resend code (${resendCooldown.value}s)`
  }
  return 'Resend code'
})

// Token value
const token = computed(() => digits.value.join(''))

// Auto-submit when all 6 digits entered
watch(token, async (newToken) => {
  if (newToken.length === 6 && !loading.value) {
    await validateToken()
  }
})

// Focus first input on mount and start timer
onMounted(() => {
  inputRefs.value[0]?.focus()
  // Start 2-minute countdown when component mounts
  startTimer(120)
})

// Watch for timer expiration
watch(isExpired, (expired) => {
  if (expired) {
    // Show expired error when timer reaches 0
    errorMessage.value = 'Token expired. Please request a new code.'
    // Clear the input fields
    digits.value = ['', '', '', '', '', '']
    inputRefs.value[0]?.focus()
  }
})

// Input handling
function handleInput(index: number, event: Event) {
  const target = event.target as HTMLInputElement
  let value = target.value

  // Only allow digits
  value = value.replace(/[^0-9]/g, '')

  if (value.length > 1) {
    // Take only the last digit if multiple entered
    value = value.slice(-1)
  }

  digits.value[index] = value

  // Auto-focus next input
  if (value && index < 5) {
    inputRefs.value[index + 1]?.focus()
  }
}

function handleKeydown(index: number, event: KeyboardEvent) {
  // Backspace handling
  if (event.key === 'Backspace') {
    if (!digits.value[index] && index > 0) {
      // Move to previous input if current is empty
      inputRefs.value[index - 1]?.focus()
    }
  }

  // Arrow key navigation
  if (event.key === 'ArrowLeft' && index > 0) {
    inputRefs.value[index - 1]?.focus()
  }
  if (event.key === 'ArrowRight' && index < 5) {
    inputRefs.value[index + 1]?.focus()
  }
}

function handlePaste(_index: number, event: ClipboardEvent) {
  event.preventDefault()

  const pastedData = event.clipboardData?.getData('text') || ''
  const digitsOnly = pastedData.replace(/[^0-9]/g, '').slice(0, 6)

  // Fill all fields with pasted digits
  digitsOnly.split('').forEach((digit, i) => {
    if (i < 6) {
      digits.value[i] = digit
    }
  })

  // Focus last filled input
  const lastIndex = Math.min(digitsOnly.length - 1, 5)
  inputRefs.value[lastIndex]?.focus()
}

async function validateToken() {
  if (token.value.length !== 6 || isExpired.value) return

  loading.value = true
  errorMessage.value = ''

  try {
    // Call auth store to validate token
    await authStore.validateToken(email.value, token.value)

    // Success - stop timer and navigate to dashboard
    stopTimer()
    router.push({ name: 'dashboard' })
  } catch (error: any) {
    loading.value = false

    // Clear digits on error
    digits.value = ['', '', '', '', '', '']
    inputRefs.value[0]?.focus()

    // Handle specific errors
    if (error.response?.status === 401) {
      const detail = error.response.data?.detail || ''
      if (detail.includes('expired')) {
        errorMessage.value = 'This code has expired. Please request a new one.'
      } else if (detail.includes('used')) {
        errorMessage.value = 'This code has already been used. Please request a new one.'
      } else {
        errorMessage.value = 'Invalid code. Please try again.'
      }
    } else if (error.status === 401) {
      // Handle error from useApi
      const message = error.message || ''
      if (message.toLowerCase().includes('expired')) {
        errorMessage.value = 'This code has expired. Please request a new one.'
      } else if (message.toLowerCase().includes('used')) {
        errorMessage.value = 'This code has already been used. Please request a new one.'
      } else {
        errorMessage.value = 'Invalid code. Please try again.'
      }
    } else {
      errorMessage.value = 'An error occurred. Please try again.'
    }
  }
}

async function handleResend() {
  if (resendCooldown.value > 0) return

  try {
    // Request new token
    await authStore.requestToken(email.value)

    // Clear current input and error
    digits.value = ['', '', '', '', '', '']
    errorMessage.value = ''
    inputRefs.value[0]?.focus()

    // Restart the token expiration timer (2 minutes)
    startTimer(120)

    // Start cooldown (60 seconds)
    resendCooldown.value = 60
    const interval = setInterval(() => {
      resendCooldown.value--
      if (resendCooldown.value <= 0) {
        clearInterval(interval)
      }
    }, 1000)
  } catch (error: any) {
    errorMessage.value = 'Failed to resend code. Please try again.'
  }
}
</script>

<style scoped>
.token-input-container {
  max-width: 400px;
  margin: 0 auto;
  padding: 2rem;
  text-align: center;
}

h2 {
  font-size: 2rem;
  margin-bottom: 0.5rem;
  color: var(--color-heading, #2c3e50);
}

.subtitle {
  color: var(--color-text-secondary, #6c757d);
  margin-bottom: 2rem;
  font-size: 0.95rem;
}

.subtitle strong {
  color: var(--color-text, #2c3e50);
}

.token-inputs {
  display: flex;
  gap: 0.5rem;
  justify-content: center;
  margin-bottom: 1.5rem;
}

.token-digit {
  width: 3rem;
  height: 3.5rem;
  font-size: 1.5rem;
  font-weight: 600;
  text-align: center;
  border: 2px solid var(--color-border, #dee2e6);
  border-radius: 8px;
  transition: border-color 0.2s, box-shadow 0.2s;
  background-color: var(--color-background, #ffffff);
  color: var(--color-text, #2c3e50);
}

.token-digit:focus {
  outline: none;
  border-color: var(--color-primary, #007bff);
  box-shadow: 0 0 0 3px rgba(0, 123, 255, 0.1);
}

.token-digit:disabled {
  background-color: var(--color-background-mute, #f8f9fa);
  cursor: not-allowed;
  opacity: 0.6;
}

.loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  color: var(--color-text-secondary, #6c757d);
  margin-bottom: 1rem;
  font-size: 0.95rem;
}

.spinner {
  width: 20px;
  height: 20px;
  border: 2px solid rgba(0, 0, 0, 0.1);
  border-top-color: var(--color-primary, #007bff);
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.error-message {
  padding: 1rem;
  background-color: var(--color-error-bg, #f8d7da);
  color: var(--color-error-text, #721c24);
  border: 1px solid var(--color-error-border, #f5c6cb);
  border-radius: 4px;
  margin-bottom: 1rem;
  font-size: 0.9rem;
}

.resend-button {
  padding: 0.75rem 1.5rem;
  background-color: transparent;
  color: var(--color-primary, #007bff);
  border: 1px solid var(--color-primary, #007bff);
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.875rem;
  font-weight: 500;
  transition: background-color 0.2s, color 0.2s;
}

.resend-button:hover:not(:disabled) {
  background-color: var(--color-primary, #007bff);
  color: white;
}

.resend-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.resend-button:focus {
  outline: 2px solid var(--color-primary, #007bff);
  outline-offset: 2px;
}

/* Responsive design */
@media (max-width: 480px) {
  .token-input-container {
    padding: 1.5rem 1rem;
  }

  h2 {
    font-size: 1.5rem;
  }

  .token-digit {
    width: 2.5rem;
    height: 3rem;
    font-size: 1.25rem;
  }

  .token-inputs {
    gap: 0.35rem;
  }
}
</style>
