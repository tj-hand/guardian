<script setup lang="ts">
import { onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()

onMounted(() => {
  // Initialize auth state from localStorage
  authStore.initAuth()
})
</script>

<template>
  <div id="guardian-app">
    <router-view />
  </div>
</template>

<style>
#guardian-app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}
</style>
