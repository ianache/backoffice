import { reactive } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import RemoteErrorBoundary from '../components/RemoteErrorBoundary.vue'

declare module 'vue-router' {
  interface RouteMeta {
    requiresAuth?: boolean
    roles?: string[]
    layout?: 'main' | 'auth'
    title?: string
    remoteDisplayName?: string
  }
}

interface RemoteManifest {
  name: string
  envVar: string
  displayName: string
  pathPrefix: string
}

const REMOTE_MANIFEST: RemoteManifest[] = [
  { name: 'mui-stub', envVar: 'VITE_REMOTE_STUB', displayName: 'Stub Domain', pathPrefix: 'stub' },
  { name: 'mui-security', envVar: 'VITE_REMOTE_SECURITY', displayName: 'Access Management', pathPrefix: 'users' },
  { name: 'mui-tenants', envVar: 'VITE_REMOTE_TENANTS', displayName: 'Tenant Management', pathPrefix: 'tenants' },
  { name: 'mui-feature-flags', envVar: 'VITE_REMOTE_FEATURE_FLAGS', displayName: 'Feature Flags', pathPrefix: 'flags' },
]

export const remoteStatuses = reactive<Record<string, 'loaded' | 'error'>>({})

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    redirect: '/tenants',
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
]

export const router = createRouter({
  history: createWebHistory(),
  routes,
})

export async function loadMicroUIRoutes() {
  const activeRemotes = REMOTE_MANIFEST.filter(remote => !!import.meta.env[remote.envVar])
  
  const importRemote = (name: string) => {
    switch (name) {
      case 'mui-stub': 
        // @ts-ignore - Module Federation remote
        return import('mui-stub/routes');
      case 'mui-security':
        // @ts-ignore - Module Federation remote
        return import('mui-security/routes');
      case 'mui-tenants':
        // @ts-ignore - Module Federation remote
        return import('mui-tenants/routes');
      case 'mui-feature-flags':
        // @ts-ignore - Module Federation remote
        return import('mui-feature-flags/routes');
      default: throw new Error(`Unknown remote: ${name}`);
    }
  }

  const results = await Promise.allSettled(
    activeRemotes.map(async (remote) => {
      try {
        const mod = await importRemote(remote.name)
        const remoteRoutes = mod.default ?? mod.routes ?? []

        
        remoteRoutes.forEach((route: RouteRecordRaw) => {
          router.addRoute(route)
        })
        
        remoteStatuses[remote.name] = 'loaded'
      } catch (err) {
        console.warn(`Failed to load remote [${remote.name}]:`, err)
        remoteStatuses[remote.name] = 'error'
        
        router.addRoute({
          path: `/${remote.pathPrefix}/:pathMatch(.*)*`,
          name: `${remote.name}-error`,
          component: RemoteErrorBoundary,
          meta: {
            requiresAuth: true,
            layout: 'main',
            remoteDisplayName: remote.displayName
          }
        })
      }
    })
  )
  
  return results
}

router.beforeEach((to) => {
  const authStore = useAuthStore()

  if (authStore.isLoading) return true

  if (to.path === '/login' && authStore.isAuthenticated) {
    return { path: '/' }
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
