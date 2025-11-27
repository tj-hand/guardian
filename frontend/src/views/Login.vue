<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import EmailInput from '@/components/auth/EmailInput.vue'
import TokenInput from '@/components/auth/TokenInput.vue'

const route = useRoute()

// Show token input if email is in query params
const showTokenInput = computed(() => route.query.email !== undefined)
const email = computed(() => route.query.email as string)
</script>

<template>
  <div class="login-page">
    <div class="login-container">
      <!-- Email input step -->
      <EmailInput v-if="!showTokenInput" />

      <!-- Token input step -->
      <TokenInput v-else :email="email" />
    </div>
  </div>
</template>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-background);
}

.login-container {
  width: 100%;
  max-width: 500px;
  padding: 1rem;
}
</style>
