<template>
  <div class="flex h-screen w-full overflow-hidden bg-background transition-colors duration-300">
    <!-- Navigation Rail -->
    <aside class="flex w-[72px] flex-col border-r border-outline-variant bg-surface-container-low z-20">
      <div class="flex h-16 items-center justify-center">
        <div class="h-10 w-10 rounded-xl bg-primary flex items-center justify-center shadow-lg shadow-primary/20">
          <md-icon class="text-on-primary">shield</md-icon>
        </div>
      </div>
      
      <nav class="flex flex-1 flex-col items-center gap-2 pt-4">
        <md-navigation-tab
          label="Tenants"
          @click="router.push('/tenants')"
          :active="route.path.startsWith('/tenants') || route.path === '/'"
        >
          <md-icon slot="active-icon">business</md-icon>
          <md-icon slot="inactive-icon">business</md-icon>
        </md-navigation-tab>
        
        <md-navigation-tab
          label="Users"
          @click="router.push('/users')"
          :active="route.path.startsWith('/users')"
        >
          <md-icon slot="active-icon">group</md-icon>
          <md-icon slot="inactive-icon">group</md-icon>
        </md-navigation-tab>

        <md-navigation-tab
          label="Audit"
          @click="router.push('/audit')"
          :active="route.path.startsWith('/audit')"
        >
          <md-icon slot="active-icon">history</md-icon>
          <md-icon slot="inactive-icon">history</md-icon>
        </md-navigation-tab>
      </nav>

      <div class="pb-6 flex flex-col items-center gap-2">
        <md-navigation-tab
          label="Settings"
          @click="router.push('/settings')"
          :active="route.path.startsWith('/settings')"
        >
          <md-icon slot="active-icon">settings</md-icon>
          <md-icon slot="inactive-icon">settings</md-icon>
        </md-navigation-tab>
      </div>
    </aside>

    <!-- Main Content Area -->
    <div class="flex flex-1 flex-col overflow-hidden">
      <!-- App Bar -->
      <header class="flex h-16 items-center justify-between border-b border-outline-variant px-8 bg-surface z-10">
        <div class="flex items-center gap-4">
          <h2 class="text-xl font-semibold text-on-surface tracking-tight">
            {{ pageTitle }}
          </h2>
        </div>

        <div class="flex items-center gap-2">
          <!-- Theme Toggle -->
          <md-icon-button @click="uiStore.toggleTheme">
            <md-icon>{{ uiStore.theme === 'dark' ? 'light_mode' : 'dark_mode' }}</md-icon>
          </md-icon-button>

          <div class="h-8 w-px bg-outline-variant mx-2"></div>

          <!-- User Profile -->
          <div class="flex items-center gap-4">
            <div class="flex flex-col items-end">
              <span class="text-sm font-bold text-on-surface leading-none">{{ authStore.user?.name || 'User' }}</span>
              <span class="text-[10px] text-on-surface-variant uppercase tracking-widest font-bold mt-1">
                {{ authStore.roles.find(r => r.includes('Admin')) || 'Viewer' }}
              </span>
            </div>
            
            <div class="flex items-center">
              <div class="h-10 w-10 rounded-full bg-secondary-container flex items-center justify-center text-on-secondary-container font-bold border border-outline-variant overflow-hidden">
                {{ (authStore.user?.name || 'U').charAt(0).toUpperCase() }}
              </div>
              
              <md-icon-button @click="authStore.logout" class="ml-1">
                <md-icon>logout</md-icon>
              </md-icon-button>
            </div>
          </div>
        </div>
      </header>

      <!-- Page Content -->
      <main class="flex-1 overflow-y-auto p-8 bg-background scroll-smooth">
        <div class="max-w-7xl mx-auto">
          <slot />
        </div>
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useAuthStore } from '../../stores/auth';
import { useUIStore } from '../../stores/ui';

const route = useRoute();
const router = useRouter();
const authStore = useAuthStore();
const uiStore = useUIStore();

const pageTitle = computed(() => {
  return (route.meta.title as string) || 'Dashboard';
});
</script>

<style scoped>
md-navigation-tab {
  --md-navigation-tab-container-height: 64px;
  --md-navigation-tab-icon-size: 24px;
  --md-navigation-tab-label-text-size: 11px;
  --md-navigation-tab-active-indicator-color: var(--primary-container);
  --md-navigation-tab-active-icon-color: var(--on-primary-container);
  --md-navigation-tab-active-label-text-color: var(--on-surface);
  --md-navigation-tab-inactive-icon-color: var(--on-surface-variant);
  --md-navigation-tab-inactive-label-text-color: var(--on-surface-variant);
}
</style>
