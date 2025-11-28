<script setup lang="ts">
import { useAuthStore } from '@/stores/auth'
import AppLayout from '@/components/layout/AppLayout.vue'

const authStore = useAuthStore()
</script>

<template>
  <AppLayout>
    <div class="dashboard">
      <h1>Dashboard</h1>
      <div class="welcome">
        <p>Welcome, <strong>{{ authStore.user?.email }}</strong>!</p>
        <p class="subtitle">You are successfully authenticated.</p>
      </div>

      <div class="info-box">
        <h2>Session Information</h2>
        <dl>
          <dt>Email:</dt>
          <dd>{{ authStore.user?.email }}</dd>

          <dt>User ID:</dt>
          <dd>{{ authStore.user?.id }}</dd>

          <dt>Account Status:</dt>
          <dd>{{ authStore.user?.is_active ? 'Active' : 'Inactive' }}</dd>

          <dt>Registered:</dt>
          <dd>{{ authStore.user?.created_at ? new Date(authStore.user.created_at).toLocaleDateString() : 'N/A' }}</dd>
        </dl>
      </div>
    </div>
  </AppLayout>
</template>

<style scoped>
.dashboard {
  max-width: 800px;
  margin: 0 auto;
  padding: 2rem;
}

h1 {
  color: var(--color-heading);
  margin-bottom: 1rem;
  font-size: 2rem;
  font-weight: 700;
}

.welcome {
  background-color: #d4edda;
  border: 1px solid #c3e6cb;
  padding: 1.5rem;
  border-radius: 8px;
  margin-bottom: 2rem;
}

.welcome p {
  margin: 0.5rem 0;
  color: #155724;
}

.subtitle {
  font-size: 0.875rem;
  opacity: 0.8;
}

.info-box {
  background-color: white;
  border: 1px solid var(--color-border);
  border-radius: 8px;
  padding: 1.5rem;
}

.info-box h2 {
  font-size: 1.125rem;
  margin-bottom: 1rem;
  color: var(--color-heading);
}

dl {
  display: grid;
  grid-template-columns: 150px 1fr;
  gap: 0.75rem;
}

dt {
  font-weight: 600;
  color: var(--color-text-secondary);
}

dd {
  color: var(--color-text);
  margin: 0;
}

@media (max-width: 768px) {
  .dashboard {
    padding: 1rem;
  }

  h1 {
    font-size: 1.5rem;
  }

  dl {
    grid-template-columns: 120px 1fr;
    gap: 0.5rem;
  }
}
</style>
