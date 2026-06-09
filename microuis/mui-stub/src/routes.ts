import type { RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/stub',
    name: 'stub',
    component: () => import('./views/StubView.vue'),
    meta: {
      requiresAuth: true,
      layout: 'main',
      title: 'Stub Domain',
      roles: ['PlatformAdmin'],
    },
  },
]

export default routes
