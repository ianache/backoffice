import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { createRouter, createWebHistory } from 'vue-router'
import TenantsView from './views/TenantsView.vue'

const app = createApp(TenantsView)
app.use(createPinia())
app.use(createRouter({ history: createWebHistory(), routes: [] }))
app.mount('#app')
