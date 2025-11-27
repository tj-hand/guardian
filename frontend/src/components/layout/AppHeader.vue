<script setup lang="ts">
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { getBrandingConfig } from '@/config/branding'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const branding = getBrandingConfig()

const isLoggedIn = computed(() => authStore.isLoggedIn)
const userEmail = computed(() => authStore.user?.email || '')

const navigateTo = (routeName: string) => {
  router.push({ name: routeName })
}

const handleLogout = async () => {
  await authStore.logout()
  router.push({ name: 'login' })
}

const isActive = (routeName: string) => {
  return route.name === routeName
}
</script>

<template>
  <header class="app-header">
    <div class="header-container">
      <div class="header-left">
        <button class="logo-link" @click="navigateTo('Home')">
          <img
            :src="branding.logoUrl"
            :alt="branding.appName"
            class="logo"
            @error="(e) => (e.target as HTMLImageElement).style.display = 'none'"
          />
          <span class="app-name">{{ branding.appName }}</span>
        </button>
      </div>

      <nav class="header-nav">
        <button
          class="nav-link"
          :class="{ active: isActive('Home') }"
          @click="navigateTo('Home')"
        >
          Home
        </button>

        <button
          v-if="!isLoggedIn"
          class="nav-link"
          :class="{ active: isActive('login') }"
          @click="navigateTo('login')"
        >
          Login
        </button>

        <template v-if="isLoggedIn">
          <button
            class="nav-link"
            :class="{ active: isActive('dashboard') }"
            @click="navigateTo('dashboard')"
          >
            Dashboard
          </button>

          <div class="user-menu">
            <span class="user-email">{{ userEmail }}</span>
            <button class="logout-button" @click="handleLogout">
              Logout
            </button>
          </div>
        </template>
      </nav>
    </div>
  </header>
</template>

<style scoped>
.app-header {
  background: var(--color-background-card);
  border-bottom: 1px solid var(--color-border);
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.05);
  position: sticky;
  top: 0;
  z-index: 1000;
}

.header-container {
  max-width: 1400px;
  margin: 0 auto;
  padding: 1rem 2rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.header-left {
  display: flex;
  align-items: center;
}

.logo-link {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  background: none;
  border: none;
  cursor: pointer;
  padding: 0.5rem;
  border-radius: 6px;
  transition: background 0.2s;
}

.logo-link:hover {
  background: rgba(0, 0, 0, 0.05);
}

.logo {
  height: 32px;
  width: auto;
}

.app-name {
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--color-text-primary);
}

.header-nav {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.nav-link {
  padding: 0.5rem 1rem;
  background: none;
  border: none;
  font-size: 1rem;
  font-weight: 500;
  color: var(--color-text-secondary);
  cursor: pointer;
  border-radius: 6px;
  transition: all 0.2s;
}

.nav-link:hover {
  color: var(--color-primary);
  background: rgba(0, 123, 255, 0.1);
}

.nav-link.active {
  color: var(--color-primary);
  font-weight: 600;
}

.user-menu {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding-left: 1rem;
  border-left: 1px solid var(--color-border);
}

.user-email {
  font-size: 0.875rem;
  color: var(--color-text-secondary);
  font-weight: 500;
}

.logout-button {
  padding: 0.5rem 1rem;
  background: none;
  color: #dc3545;
  border: 1px solid #dc3545;
  border-radius: 6px;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.logout-button:hover {
  background: #dc3545;
  color: white;
}

@media (max-width: 768px) {
  .header-container {
    padding: 1rem;
  }

  .app-name {
    font-size: 1rem;
  }

  .header-nav {
    gap: 0.25rem;
  }

  .nav-link {
    padding: 0.5rem 0.75rem;
    font-size: 0.9rem;
  }

  .logo {
    height: 24px;
  }

  .user-email {
    display: none;
  }

  .user-menu {
    padding-left: 0.5rem;
    border-left: none;
  }
}
</style>
