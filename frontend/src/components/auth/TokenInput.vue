<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const props = defineProps<{
  email: string
}>()

const router = useRouter()
const authStore = useAuthStore()

const token = ref('')
const isSubmitting = ref(false)
const tokenInputs = ref<HTMLInputElement[]>([])

// Focus first input on mount
onMounted(() => {
  tokenInputs.value[0]?.focus()
})

// Handle input for individual digit boxes
function handleInput(index: number, event: Event) {
  const input = event.target as HTMLInputElement
  const value = input.value.replace(/\D/g, '')

  if (value.length > 1) {
    // Pasted value - distribute across inputs
    const digits = value.slice(0, 6).split('')
    digits.forEach((digit, i) => {
      if (tokenInputs.value[i]) {
        tokenInputs.value[i].value = digit
      }
    })
    updateToken()
    const nextIndex = Math.min(digits.length, 5)
    tokenInputs.value[nextIndex]?.focus()
  } else {
    input.value = value.slice(0, 1)
    updateToken()
    if (value && index < 5) {
      tokenInputs.value[index + 1]?.focus()
    }
  }
}

function handleKeydown(index: number, event: KeyboardEvent) {
  if (event.key === 'Backspace' && !tokenInputs.value[index]?.value && index > 0) {
    tokenInputs.value[index - 1]?.focus()
  }
}

function updateToken() {
  token.value = tokenInputs.value.map((input) => input.value).join('')
}

async function handleSubmit() {
  if (token.value.length !== 6 || isSubmitting.value) return

  isSubmitting.value = true
  authStore.clearError()

  try {
    await authStore.validateToken(props.email, token.value)
    // Navigate to dashboard
    const redirect = router.currentRoute.value.query.redirect as string
    router.push(redirect || '/dashboard')
  } catch {
    // Error handled in store
    // Clear token on error
    tokenInputs.value.forEach((input) => (input.value = ''))
    token.value = ''
    tokenInputs.value[0]?.focus()
  } finally {
    isSubmitting.value = false
  }
}

function handleResend() {
  router.push('/login')
}
</script>

<template>
  <div class="token-input-container">
    <div class="auth-header">
      <img src="/logo.svg" alt="Guardian" class="logo" />
      <h1>Enter your code</h1>
      <p>We sent a 6-digit code to {{ email }}</p>
    </div>

    <form @submit.prevent="handleSubmit" class="auth-form">
      <div class="token-inputs">
        <input
          v-for="i in 6"
          :key="i"
          :ref="(el) => { if (el) tokenInputs[i - 1] = el as HTMLInputElement }"
          type="text"
          inputmode="numeric"
          pattern="[0-9]*"
          maxlength="6"
          class="token-digit"
          :disabled="isSubmitting"
          @input="handleInput(i - 1, $event)"
          @keydown="handleKeydown(i - 1, $event)"
        />
      </div>

      <div v-if="authStore.error" class="error-message">
        {{ authStore.error }}
      </div>

      <button
        type="submit"
        class="submit-btn"
        :disabled="isSubmitting || token.length !== 6"
      >
        <span v-if="isSubmitting">Verifying...</span>
        <span v-else>Verify Code</span>
      </button>
    </form>

    <div class="auth-footer">
      <p>
        Didn't receive the code?
        <button type="button" class="link-btn" @click="handleResend">
          Send again
        </button>
      </p>
    </div>
  </div>
</template>

<style scoped>
.token-input-container {
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
  word-break: break-all;
}

.auth-form {
  background: var(--color-surface);
  border-radius: 8px;
  padding: 1.5rem;
  border: 1px solid var(--color-border);
}

.token-inputs {
  display: flex;
  gap: 0.5rem;
  justify-content: center;
  margin-bottom: 1.5rem;
}

.token-digit {
  width: 48px;
  height: 56px;
  text-align: center;
  font-size: 1.5rem;
  font-weight: 600;
  border: 2px solid var(--color-border);
  border-radius: 8px;
  background: var(--color-background);
  color: var(--color-text);
}

.token-digit:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px var(--color-primary-light);
}

.token-digit:disabled {
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
  text-align: center;
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

.link-btn {
  background: none;
  border: none;
  color: var(--color-primary);
  cursor: pointer;
  font-size: inherit;
  padding: 0;
}

.link-btn:hover {
  text-decoration: underline;
}
</style>
