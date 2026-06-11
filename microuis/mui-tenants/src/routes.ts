import type { RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/tenants',
    name: 'tenants',
    component: () => import('./views/TenantsView.vue'),
    meta: {
      requiresAuth: true,
      layout: 'main',
      title: 'Tenant Management',
      roles: ['PlatformAdmin'],
    },
  },
  {
    path: '/products',
    name: 'products',
    component: () => import('./views/ProductsView.vue'),
    meta: {
      requiresAuth: true,
      layout: 'main',
      title: 'Product Management',
      roles: ['PlatformAdmin'],
    },
  },
]

export default routes
