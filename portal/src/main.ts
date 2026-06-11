import { createApp } from 'vue'
import { createPinia } from 'pinia'
import piniaPluginPersistedstate from 'pinia-plugin-persistedstate'
import App from './App.vue'
import router, { loadMicroUIRoutes } from './router/index'
import { useAuthStore } from './stores/auth'
import { useBoFlags } from './composables/useBoFlags'
import './assets/theme.css'
import './assets/tailwind.css'
import './assets/main.css'
import './plugins/material'

const app = createApp(App)
const pinia = createPinia()
pinia.use(piniaPluginPersistedstate)

app.use(pinia)

// Init Keycloak BEFORE registering the router or mounting — prevents flash of unauthenticated content and race conditions
// In Playwright E2E mode (VITE_E2E_SKIP_AUTH=true), skip Keycloak init so tests can inject auth via sessionStorage
const authStore = useAuthStore(pinia)
if (import.meta.env.VITE_E2E_SKIP_AUTH !== 'true') {
  await authStore.init()
} else {
  authStore.$patch({ isLoading: false })
}

// Initialize backoffice dogfooding flags (fail-open: defaults true if SDK unavailable)
if (authStore.isAuthenticated) {
  useBoFlags().init({ sub: authStore.user?.email ?? '', roles: authStore.roles })
    .catch(() => {}) // fail-open — UI visible even if SDK fails
}

// Load Micro-UI routes after auth is initialized but BEFORE the router is registered with the app
await loadMicroUIRoutes()

app.use(router)
app.mount('#app')
