import { createApp } from 'vue'
import { createPinia } from 'pinia'
import piniaPluginPersistedstate from 'pinia-plugin-persistedstate'
import App from './App.vue'
import router from './router/index'
import { useAuthStore } from './stores/auth'
import './assets/theme.css'
import './assets/tailwind.css'
import './assets/main.css'
import './plugins/material'

const app = createApp(App)
const pinia = createPinia()
pinia.use(piniaPluginPersistedstate)

app.use(pinia)

// Init Keycloak BEFORE registering the router or mounting — prevents flash of unauthenticated content and race conditions
const authStore = useAuthStore(pinia)
await authStore.init()

app.use(router)
app.mount('#app')
