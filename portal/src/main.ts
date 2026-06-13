import { createApp } from 'vue'
import { createPinia } from 'pinia'
import piniaPluginPersistedstate from 'pinia-plugin-persistedstate'
import App from './App.vue'
import router, { loadMicroUIRoutes } from './router/index'
import { useAuthStore } from './stores/auth'
import { useBoFlags } from './composables/useBoFlags'
import { useLoginLabels } from './composables/useLoginLabels'
import './assets/theme.css'
import './assets/tailwind.css'
import './assets/main.css'
import './plugins/material'

const app = createApp(App)
const pinia = createPinia()
pinia.use(piniaPluginPersistedstate)

app.use(pinia)

const loginLabels = useLoginLabels()
app.use(loginLabels.plugin)

// Start label initialization asynchronously (independently of auth)
const labelInitPromise = loginLabels.initialize().catch((err) => {
  console.warn('[main] Labels initialize warning (non-blocking):', err)
})

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
  useBoFlags().init({
    sub: authStore.user?.email ?? '',
    roles: authStore.roles,
    // Platform tenant for rule matching (e.g. bo.feature.create's tenant_id rule)
    tenant_id: import.meta.env.VITE_BO_TENANT_ID ?? '',
  })
    .catch(() => {}) // fail-open — UI visible even if SDK fails
}

// Load Micro-UI routes after auth is initialized but BEFORE the router is registered with the app
await loadMicroUIRoutes()

// Await the 1-second mount deadline for labels
try {
  await loginLabels.waitForInitialLabels(1000)
} catch (err) {
  console.warn('[main] Labels wait warning (non-blocking):', err)
}

app.use(router)
app.mount('#app')
