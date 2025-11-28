import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import { applyBrandingTheme } from './config/branding'
import { useAuthStore } from './stores/auth'
import './assets/styles/main.css'

// Create Vue app instance
const app = createApp(App)

// Initialize Pinia state management
const pinia = createPinia()
app.use(pinia)

// Initialize Vue Router
app.use(router)

// Apply branding theme from environment variables
applyBrandingTheme()

// Initialize authentication from localStorage
const authStore = useAuthStore()
authStore.initAuth()

// Mount the application
app.mount('#app')
