import type { RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/flags',
    name: 'flags',
    component: () => import('./views/FlagsView.vue'),
    meta: { requiresAuth: true, layout: 'main', title: 'Feature Flags', roles: ['PlatformAdmin', 'TenantAdmin', 'TenantOwner', 'ProductManager'] },
  },
  {
    path: '/flags/:id/rules',
    name: 'rule-builder',
    component: () => import('./views/RuleBuilderView.vue'),
    meta: { requiresAuth: true, layout: 'main', title: 'Rule Builder', roles: ['PlatformAdmin', 'TenantAdmin', 'TenantOwner', 'ProductManager'] },
  },
  {
    path: '/segments',
    name: 'segments',
    component: () => import('./views/SegmentsView.vue'),
    meta: { requiresAuth: true, layout: 'main', title: 'Segments', roles: ['PlatformAdmin', 'TenantAdmin', 'TenantOwner', 'ProductManager'] },
  },
]

export default routes
