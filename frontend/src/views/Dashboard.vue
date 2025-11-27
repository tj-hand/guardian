<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

async function handleLogout() {
  await authStore.logout()
  router.push('/login')
}
</script>

<template>
  <div class="dashboard-page">
    <header class="dashboard-header">
      <div class="header-left">
        <img src="/logo.svg" alt="Guardian" class="header-logo" />
        <span class="header-title">Guardian</span>
      </div>
      <div class="header-right">
        <span class="user-email">{{ authStore.user?.email }}</span>
        <button class="logout-btn" @click="handleLogout">Logout</button>
      </div>
    </header>

    <main class="dashboard-content">
      <div class="welcome-card">
        <h1>Welcome to Guardian</h1>
        <p>You are successfully authenticated!</p>
      </div>

      <div class="info-grid">
        <div class="info-card">
          <h3>User Information</h3>
          <dl>
            <dt>Email</dt>
            <dd>{{ authStore.user?.email }}</dd>
            <dt>User ID</dt>
            <dd>{{ authStore.user?.id }}</dd>
            <dt>Status</dt>
            <dd>
              <span :class="['status-badge', authStore.user?.is_active ? 'active' : 'inactive']">
                {{ authStore.user?.is_active ? 'Active' : 'Inactive' }}
              </span>
            </dd>
            <dt>Created</dt>
            <dd>{{ new Date(authStore.user?.created_at || '').toLocaleDateString() }}</dd>
          </dl>
        </div>

        <div class="info-card">
          <h3>Session Information</h3>
          <dl>
            <dt>Authentication</dt>
            <dd>
              <span class="status-badge active">Authenticated</span>
            </dd>
            <dt>Token Type</dt>
            <dd>JWT Bearer</dd>
          </dl>
          <p class="info-note">
            Your session is secured with a JSON Web Token.
          </p>
        </div>
      </div>
    </main>
  </div>
</template>

<style scoped>
.dashboard-page {
  min-height: 100vh;
  background: var(--color-background);
}

.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 2rem;
  background: var(--color-surface);
  border-bottom: 1px solid var(--color-border);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.header-logo {
  width: 32px;
  height: 32px;
}

.header-title {
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--color-text);
}

.header-right {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.user-email {
  color: var(--color-text-muted);
  font-size: 0.875rem;
}

.logout-btn {
  padding: 0.5rem 1rem;
  background: transparent;
  color: var(--color-text);
  border: 1px solid var(--color-border);
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.875rem;
  transition: all 0.2s;
}

.logout-btn:hover {
  background: var(--color-error-bg);
  border-color: var(--color-error);
  color: var(--color-error);
}

.dashboard-content {
  max-width: 1000px;
  margin: 0 auto;
  padding: 2rem;
}

.welcome-card {
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-primary-dark) 100%);
  color: white;
  padding: 2rem;
  border-radius: 12px;
  margin-bottom: 2rem;
}

.welcome-card h1 {
  font-size: 1.5rem;
  margin-bottom: 0.5rem;
}

.welcome-card p {
  opacity: 0.9;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 1.5rem;
}

.info-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 12px;
  padding: 1.5rem;
}

.info-card h3 {
  font-size: 1rem;
  font-weight: 600;
  color: var(--color-text);
  margin-bottom: 1rem;
  padding-bottom: 0.75rem;
  border-bottom: 1px solid var(--color-border);
}

.info-card dl {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 0.75rem 1rem;
}

.info-card dt {
  color: var(--color-text-muted);
  font-size: 0.875rem;
}

.info-card dd {
  color: var(--color-text);
  font-size: 0.875rem;
  word-break: break-all;
}

.status-badge {
  display: inline-block;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 500;
}

.status-badge.active {
  background: var(--color-success-bg);
  color: var(--color-success);
}

.status-badge.inactive {
  background: var(--color-error-bg);
  color: var(--color-error);
}

.info-note {
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid var(--color-border);
  color: var(--color-text-muted);
  font-size: 0.875rem;
}
</style>
