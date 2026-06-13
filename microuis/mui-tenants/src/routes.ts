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
  {
    path: '/companies',
    name: 'companies',
    component: () => import('./views/CompaniesView.vue'),
    meta: {
      requiresAuth: true,
      layout: 'main',
      title: 'Company Management',
      roles: ['PlatformAdmin', 'TenantAdmin', 'TenantOwner'],
    },
  },
  {
    path: '/audit-log',
    name: 'audit-log',
    component: () => import('./views/AuditLogView.vue'),
    meta: {
      requiresAuth: true,
      layout: 'main',
      title: 'Audit Log',
      roles: ['PlatformAdmin', 'TenantAdmin', 'TenantOwner'],
    },
  },
]

export default routes
