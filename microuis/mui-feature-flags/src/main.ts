import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { createRouter, createWebHistory } from 'vue-router'
import FlagsView from './views/FlagsView.vue'

const app = createApp(FlagsView)
app.use(createPinia())
app.use(createRouter({ history: createWebHistory(), routes: [] }))
app.mount('#app')
