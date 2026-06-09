import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '../stores/auth'

declare module 'vue-router' {
  interface RouteMeta {
    requiresAuth?: boolean
    roles?: string[]
    layout?: 'main' | 'auth'
    title?: string
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
    meta: { layout: 'auth', title: 'Login' }
  },
  {
    path: '/unauthorized',
    component: () => import('../views/UnauthorizedView.vue'),
    meta: { layout: 'main', title: 'Unauthorized', requiresAuth: true }
  },
  {
    path: '/dashboard',
    component: () => import('../views/DashboardView.vue'),
    meta: { requiresAuth: true, layout: 'main', title: 'Dashboard' },
  },
  {
    path: '/tenants',
    name: 'tenants',
    component: () => import('../views/TenantsView.vue'),
    meta: { requiresAuth: true, roles: ['PlatformAdmin'], layout: 'main', title: 'Tenant Management' },
  },
  {
    path: '/users',
    name: 'users',
    component: () => import('../views/UsersView.vue'),
    meta: { requiresAuth: true, roles: ['TenantAdmin', 'TenantOwner'], layout: 'main', title: 'Access Management' },
  },
  {
    path: '/flags',
    name: 'flags',
    component: () => import('../views/FlagsView.vue'),
    meta: { requiresAuth: true, roles: ['PlatformAdmin', 'TenantAdmin', 'TenantOwner', 'ProductManager'], layout: 'main', title: 'Feature Flags' },
  },
  {
    path: '/flags/:id/rules',
    name: 'rule-builder',
    component: () => import('../views/RuleBuilderView.vue'),
    meta: {
      requiresAuth: true,
      roles: ['PlatformAdmin', 'TenantAdmin', 'TenantOwner', 'ProductManager'],
      layout: 'main',
      title: 'Rule Builder'
    },
  },
  {
    path: '/segments',
    name: 'segments',
    component: () => import('../views/SegmentsView.vue'),
    meta: {
      requiresAuth: true,
      roles: ['PlatformAdmin', 'TenantAdmin', 'TenantOwner', 'ProductManager'],
      layout: 'main',
      title: 'Segments'
    },
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

  if (to.path === '/login' && authStore.isAuthenticated) {
    return { path: '/dashboard' }
  }

  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    return { path: '/login', query: to.path !== '/' ? { redirect: to.fullPath } : undefined }
  }

  const requiredRoles = to.meta.roles
  if (requiredRoles?.length && !requiredRoles.some(r => authStore.hasRole(r))) {
    return { path: '/unauthorized' }
  }

  return true
})

export default router
