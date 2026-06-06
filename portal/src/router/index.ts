import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '../stores/auth'

declare module 'vue-router' {
  interface RouteMeta {
    requiresAuth?: boolean
    roles?: string[]
  }
}

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    redirect: '/dashboard',
  },
  {
    path: '/login',
    component: () => import('../views/LoginView.vue'),
  },
  {
    path: '/unauthorized',
    component: () => import('../views/UnauthorizedView.vue'),
  },
  {
    path: '/dashboard',
    component: () => import('../views/DashboardView.vue'),
    meta: { requiresAuth: true },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to) => {
  const authStore = useAuthStore()

  // Wait for Keycloak init to complete (isLoading = true during init)
  // If still loading, allow navigation — the auth store init() in main.ts
  // completes before app.mount(), so by the time guards run, loading is false
  if (authStore.isLoading) return true

  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    authStore.login()  // Redirects to Keycloak login page
    return false
  }

  const requiredRoles = to.meta.roles
  if (requiredRoles?.length && !requiredRoles.some(r => authStore.hasRole(r))) {
    return { path: '/unauthorized' }
  }

  return true
})

export default router
