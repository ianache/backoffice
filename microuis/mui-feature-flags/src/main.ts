// Tailwind only for standalone dev — in the shell, the portal's single sheet
// covers all remotes (see portal/tailwind.config.js content globs)
import './assets/tailwind.css'
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { createRouter, createWebHistory } from 'vue-router'
import FlagsView from './views/FlagsView.vue'

const app = createApp(FlagsView)
app.use(createPinia())
app.use(createRouter({ history: createWebHistory(), routes: [] }))
app.mount('#app')
