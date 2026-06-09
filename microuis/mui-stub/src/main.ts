import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { createRouter, createWebHistory } from 'vue-router'
import StubView from './views/StubView.vue'

const app = createApp(StubView)
app.use(createPinia())
app.use(createRouter({ history: createWebHistory(), routes: [] }))
app.mount('#app')
