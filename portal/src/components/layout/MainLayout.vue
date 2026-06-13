<template>
  <div class="min-h-screen bg-background text-on-background">
    <!-- ─── Top Header ──────────────────────────────────────────────────────── -->
    <header class="fixed top-0 left-0 right-0 flex items-center h-16 w-full bg-surface-container-lowest border-b border-outline-variant shadow-sm z-50">
      <!-- Brand block — same width as sidebar -->
      <div class="flex items-center h-full w-64 px-2 border-r border-outline-variant bg-surface-container-low shrink-0">
        <div class="flex items-center gap-2 px-2">
          <div class="w-10 h-10 bg-primary rounded-lg flex items-center justify-center shrink-0">
            <span class="material-symbols-outlined text-on-primary text-[22px]">corporate_fare</span>
          </div>
          <div class="min-w-0">
            <h2 class="text-[15px] font-black text-on-surface truncate leading-tight">BackOffice CC</h2>
            <p class="text-xs text-on-surface-variant truncate">Global Admin</p>
          </div>
        </div>
      </div>

      <!-- Header content -->
      <div class="flex flex-1 items-center justify-between px-6 h-full">
        <!-- Breadcrumb -->
        <nav class="flex items-center gap-2 text-on-surface-variant text-sm">
          <a
            href="#"
            class="flex items-center hover:text-primary transition-colors"
            @click.prevent="router.push('/stub')"
          >
            <span class="material-symbols-outlined text-[20px]">home</span>
          </a>
          <span class="material-symbols-outlined text-secondary text-[16px]">chevron_right</span>
          <span class="text-on-surface font-semibold">{{ breadcrumbLabel }}</span>
        </nav>

        <!-- Right controls -->
        <div class="flex items-center gap-4">
          <!-- Search bar -->
          <div class="hidden md:flex items-center bg-surface-container-low px-4 py-1.5 rounded-full border border-outline-variant gap-1">
            <span class="material-symbols-outlined text-on-surface-variant text-[20px]">search</span>
            <input
              type="text"
              placeholder="Search..."
              class="bg-transparent border-none focus:ring-0 text-sm w-48 outline-none placeholder:text-on-surface-variant"
            />
          </div>

          <div class="flex items-center gap-0.5">
            <!-- Theme toggle -->
            <button
              @click="uiStore.toggleTheme"
              class="p-2 rounded-full hover:bg-surface-container transition-colors active:scale-95 duration-150"
              title="Toggle Theme"
            >
              <span class="material-symbols-outlined text-secondary text-[20px]">
                {{ uiStore.theme === 'dark' ? 'dark_mode' : 'light_mode' }}
              </span>
            </button>

            <!-- Notifications -->
            <button class="p-2 rounded-full hover:bg-surface-container transition-colors active:scale-95 duration-150">
              <span class="material-symbols-outlined text-secondary text-[20px]">notifications</span>
            </button>

            <!-- Help -->
            <button class="p-2 rounded-full hover:bg-surface-container transition-colors active:scale-95 duration-150">
              <span class="material-symbols-outlined text-secondary text-[20px]">help</span>
            </button>

            <!-- Apps -->
            <button class="p-2 rounded-full hover:bg-surface-container transition-colors active:scale-95 duration-150">
              <span class="material-symbols-outlined text-secondary text-[20px]">apps</span>
            </button>

            <!-- User avatar + logout -->
            <div class="flex items-center gap-1 ml-2">
              <div
                class="w-8 h-8 rounded-full bg-secondary-container border border-outline-variant flex items-center justify-center text-on-secondary-container font-bold text-sm cursor-pointer"
                :title="authStore.user?.name || 'User'"
              >
                {{ (authStore.user?.name || 'U').charAt(0).toUpperCase() }}
              </div>
              <button
                @click="authStore.logout"
                class="p-1.5 rounded-full hover:bg-surface-container transition-colors active:scale-95 duration-150"
                title="Sign out"
              >
                <span class="material-symbols-outlined text-secondary text-[18px]">logout</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </header>

    <!-- ─── Left Sidebar ───────────────────────────────────────────────────── -->
    <aside class="fixed left-0 top-16 bottom-0 w-64 bg-surface-container-low border-r border-outline-variant flex flex-col z-40">
      <nav class="flex-1 flex flex-col gap-0.5 overflow-y-auto p-2 pt-3">
        <!-- Tenants -->
        <button
          v-if="authStore.hasRole('PlatformAdmin')"
          @click="router.push('/tenants')"
          :class="[
            'w-full flex items-center gap-4 px-4 py-2 rounded-lg transition-all duration-200 text-left',
            remoteStatuses['mui-tenants'] === 'error' ? 'opacity-50 cursor-not-allowed' : '',
            isActive('/tenants')
              ? 'bg-primary text-on-primary font-semibold'
              : 'text-on-surface-variant hover:bg-surface-container-high'
          ]"
          :disabled="remoteStatuses['mui-tenants'] === 'error'"
          title="Tenants"
        >
          <span class="material-symbols-outlined text-[22px]">corporate_fare</span>
          <span class="text-sm">Tenants</span>
        </button>

        <!-- Stub Domain — Testing for Phase 9 -->
        <button
          v-if="authStore.hasRole('PlatformAdmin')"
          @click="router.push('/stub')"
          :class="[
            'w-full flex items-center gap-4 px-4 py-2 rounded-lg transition-all duration-200 text-left',
            remoteStatuses['mui-stub'] === 'error' ? 'opacity-50 cursor-not-allowed' : '',
            isActive('/stub')
              ? 'bg-primary text-on-primary font-semibold'
              : 'text-on-surface-variant hover:bg-surface-container-high'
          ]"
          :disabled="remoteStatuses['mui-stub'] === 'error'"
          title="Stub Domain"
        >
          <span class="material-symbols-outlined text-[22px]">widgets</span>
          <span class="text-sm">Stub Domain</span>
        </button>

        <!-- Products (served by mui-tenants remote) -->
        <button
          @click="router.push('/products')"
          :class="[
            'w-full flex items-center gap-4 px-4 py-2 rounded-lg transition-all duration-200 text-left',
            remoteStatuses['mui-tenants'] === 'error' ? 'opacity-50 cursor-not-allowed' : '',
            isActive('/products')
              ? 'bg-primary text-on-primary font-semibold'
              : 'text-on-surface-variant hover:bg-surface-container-high'
          ]"
          :disabled="remoteStatuses['mui-tenants'] === 'error'"
          title="Products"
        >
          <span class="material-symbols-outlined text-[22px]">inventory_2</span>
          <span class="text-sm">Products</span>
        </button>

        <!-- Companies (served by mui-tenants remote) -->
        <button
          v-if="authStore.hasRole('PlatformAdmin') || authStore.hasRole('TenantAdmin') || authStore.hasRole('TenantOwner')"
          @click="router.push('/companies')"
          :class="[
            'w-full flex items-center gap-4 px-4 py-2 rounded-lg transition-all duration-200 text-left',
            remoteStatuses['mui-tenants'] === 'error' ? 'opacity-50 cursor-not-allowed' : '',
            isActive('/companies')
              ? 'bg-primary text-on-primary font-semibold'
              : 'text-on-surface-variant hover:bg-surface-container-high'
          ]"
          :disabled="remoteStatuses['mui-tenants'] === 'error'"
          title="Companies"
        >
          <span class="material-symbols-outlined text-[22px]">apartment</span>
          <span class="text-sm">Companies</span>
        </button>

        <!-- Users / Access Management (served by mui-security remote) -->
        <button
          v-if="authStore.hasRole('PlatformAdmin') || authStore.hasRole('TenantOwner') || authStore.hasRole('TenantAdmin')"
          @click="router.push('/users')"
          :class="[
            'w-full flex items-center gap-4 px-4 py-2 rounded-lg transition-all duration-200 text-left',
            remoteStatuses['mui-security'] === 'error' ? 'opacity-50 cursor-not-allowed' : '',
            isActive('/users')
              ? 'bg-primary text-on-primary font-semibold'
              : 'text-on-surface-variant hover:bg-surface-container-high'
          ]"
          :disabled="remoteStatuses['mui-security'] === 'error'"
          title="Users"
        >
          <span class="material-symbols-outlined text-[22px]">manage_accounts</span>
          <span class="text-sm">Users</span>
        </button>

        <!-- WhiteLabels (placeholder) -->
        <button
          class="w-full flex items-center gap-4 px-4 py-2 rounded-lg text-on-surface-variant hover:bg-surface-container-high transition-all duration-200 text-left cursor-not-allowed opacity-70"
          disabled
        >
          <span class="material-symbols-outlined text-[22px]">branding_watermark</span>
          <span class="text-sm">WhiteLabels</span>
        </button>

        <!-- Feature Flags (gated by bo.feature dogfooding flag) -->
        <button
          v-if="boFeature"
          @click="router.push('/flags')"
          :class="[
            'w-full flex items-center gap-4 px-4 py-2 rounded-lg transition-all duration-200 text-left',
            remoteStatuses['mui-feature-flags'] === 'error' ? 'opacity-50 cursor-not-allowed' : '',
            isActive('/flags')
              ? 'bg-primary text-on-primary font-semibold'
              : 'text-on-surface-variant hover:bg-surface-container-high'
          ]"
          :disabled="remoteStatuses['mui-feature-flags'] === 'error'"
          title="Feature Flags"
        >
          <span class="material-symbols-outlined text-[22px]">toggle_on</span>
          <span class="text-sm">Feature Flags</span>
        </button>

        <!-- Segments (gated by bo.feature — part of Feature Flags domain) -->
        <button
          v-if="boFeature"
          @click="router.push('/segments')"
          :class="[
            'w-full flex items-center gap-4 px-4 py-2 rounded-lg transition-all duration-200 text-left',
            remoteStatuses['mui-feature-flags'] === 'error' ? 'opacity-50 cursor-not-allowed' : '',
            isActive('/segments')
              ? 'bg-primary text-on-primary font-semibold'
              : 'text-on-surface-variant hover:bg-surface-container-high'
          ]"
          :disabled="remoteStatuses['mui-feature-flags'] === 'error'"
          title="Segments"
        >
          <span class="material-symbols-outlined text-[22px]">group</span>
          <span class="text-sm">Segments</span>
        </button>

        <!-- Audit Log (served by mui-tenants remote) -->
        <button
          v-if="authStore.hasRole('PlatformAdmin') || authStore.hasRole('TenantAdmin') || authStore.hasRole('TenantOwner')"
          @click="router.push('/audit-log')"
          :class="[
            'w-full flex items-center gap-4 px-4 py-2 rounded-lg transition-all duration-200 text-left',
            remoteStatuses['mui-tenants'] === 'error' ? 'opacity-50 cursor-not-allowed' : '',
            isActive('/audit-log')
              ? 'bg-primary text-on-primary font-semibold'
              : 'text-on-surface-variant hover:bg-surface-container-high'
          ]"
          :disabled="remoteStatuses['mui-tenants'] === 'error'"
          title="Audit Log"
        >
          <span class="material-symbols-outlined text-[22px]">history_edu</span>
          <span class="text-sm">Audit Log</span>
        </button>

        <!-- Platform Settings (placeholder) -->
        <button
          class="w-full flex items-center gap-4 px-4 py-2 rounded-lg text-on-surface-variant hover:bg-surface-container-high transition-all duration-200 text-left cursor-not-allowed opacity-70"
          disabled
        >
          <span class="material-symbols-outlined text-[22px]">settings</span>
          <span class="text-sm">Platform Settings</span>
        </button>
      </nav>

      <!-- Status footer -->
      <div class="border-t border-outline-variant p-2">
        <div class="flex items-center justify-between px-4 py-2">
          <div class="flex items-center gap-2">
            <div class="w-2 h-2 rounded-full bg-green-500 shrink-0"></div>
            <span class="material-symbols-outlined text-secondary text-[20px]">cloud_done</span>
            <span class="text-xs text-on-surface-variant">All systems operational</span>
          </div>
          <span class="text-xs text-on-surface-variant font-mono">v2.4.12</span>
        </div>
      </div>
    </aside>

    <!-- ─── Page Content ───────────────────────────────────────────────────── -->
    <main class="ml-64 pt-16 min-h-screen bg-background">
      <div class="p-6 max-w-[1440px] mx-auto">
        <slot />
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../../stores/auth'
import { useUIStore } from '../../stores/ui'
import { remoteStatuses } from '../../router/index'
import { useBoFlags } from '../../composables/useBoFlags'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const uiStore = useUIStore()
const { boFeature } = useBoFlags()

const breadcrumbLabel = computed(() => {
  const segment = route.path.split('/').filter(Boolean)[0]
  if (!segment || segment === 'dashboard') return 'Dashboard'
  if (segment === 'stub') return 'Stub Domain'
  if (segment === 'tenants') return 'Tenants'
  if (segment === 'users') return 'Access Management'
  if (segment === 'flags') return 'Feature Flags'
  if (segment === 'segments') return 'Segments'
  return segment.charAt(0).toUpperCase() + segment.slice(1)
})

function isActive(path: string): boolean {
  return route.path.startsWith(path) || (path === '/tenants' && route.path === '/') || (path === '/users' && route.path === '/') || (path === '/stub' && route.path === '/')
}
</script>
