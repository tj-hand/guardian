<script setup lang="ts">
import { RouterView } from 'vue-router'
import { onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useTheme } from '@/composables/useTheme'

const authStore = useAuthStore()
const { initializeTheme } = useTheme()

// Initialize app on mount
onMounted(() => {
  // Initialize theme system (applies branding CSS variables)
  initializeTheme()

  // Check authentication status
  authStore.checkAuth()
})
</script>

<template>
  <div id="app">
    <RouterView />
  </div>
</template>

<style>
#app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}
</style>
