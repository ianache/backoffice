import type { RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/users',
    name: 'users',
    component: () => import('./views/UsersView.vue'),
    meta: {
      requiresAuth: true,
      layout: 'main',
      title: 'Access Management',
      roles: ['PlatformAdmin', 'TenantOwner', 'TenantAdmin'],
    },
  },
]

export default routes
