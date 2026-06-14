import type { RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/observability',
    name: 'observability',
    component: () => import('./views/ObservabilityView.vue'),
    meta: {
      requiresAuth: true,
      layout: 'main',
      title: 'Observability & SLA/SLO',
      roles: ['PlatformAdmin', 'TenantOwner', 'TenantAdmin'],
    },
  },
]

export default routes
