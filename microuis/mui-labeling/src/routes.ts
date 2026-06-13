import type { RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/labeling',
    name: 'labeling',
    component: () => import('./views/LabelingView.vue'),
    meta: {
      requiresAuth: true,
      layout: 'main',
      title: 'Labeling & Namespaces',
      roles: ['PlatformAdmin', 'TenantAdmin', 'TenantOwner', 'ProductManager', 'UXWriter'],
    },
  },
]

export default routes
