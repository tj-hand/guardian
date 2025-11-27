<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import EmailInput from '@/components/auth/EmailInput.vue'
import TokenInput from '@/components/auth/TokenInput.vue'

const route = useRoute()
const showTokenInput = computed(() => route.query.email !== undefined)
</script>

<template>
  <div class="login-page">
    <div class="login-container">
      <!-- Show email input by default -->
      <EmailInput v-if="!showTokenInput" />

      <!-- Show token input if email is in query params -->
      <TokenInput v-else :email="route.query.email as string" />
    </div>
  </div>
</template>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: var(--color-background);
}

.login-container {
  width: 100%;
  max-width: 500px;
  padding: 1rem;
}
</style>
