import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [vue()],

  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },

  server: {
    host: '0.0.0.0',
    port: 5173,
    strictPort: true,
    watch: {
      usePolling: true // Needed for Docker on some systems
    },
    // Proxy requests through Evoke (Layer 0 API Service)
    // Layered architecture: Guardian → Evoke → Bolt → Manifast → Backend
    proxy: {
      '/evoke': {
        target: 'http://localhost:3000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/evoke/, '')
      }
    }
  },

  preview: {
    host: '0.0.0.0',
    port: 5173,
    strictPort: true
  },

  build: {
    outDir: 'dist',
    sourcemap: true,
    rollupOptions: {
      output: {
        manualChunks: {
          'vue-vendor': ['vue', 'vue-router', 'pinia']
        }
      }
    }
  },

  test: {
    globals: true,
    environment: 'jsdom'
  }
})
