<template>
  <div class="font-body-md text-on-surface bg-background dark:bg-slate-950 dark:text-slate-200 h-screen flex flex-col overflow-hidden">
    <!-- Top App Bar -->
    <header class="w-full h-16 bg-surface-bright dark:bg-slate-900 border-b border-outline-variant dark:border-slate-800 shadow-sm z-40 flex items-center justify-between px-lg shrink-0">
      <div class="flex items-center gap-sm text-on-surface-variant dark:text-slate-400">
        <span class="font-label-md">Section:</span>
        <span class="font-title-md text-on-surface dark:text-slate-200 font-bold">Localization Engine</span>
        <span class="material-symbols-outlined text-outline">chevron_right</span>
        <span class="font-title-md text-primary dark:text-primary-fixed-dim font-bold">Namespaces & Keys</span>
      </div>
      <div class="flex items-center gap-lg">
        <div class="relative group">
          <span class="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-outline">search</span>
          <input
            id="globalSearch"
            v-model="state.searchQuery"
            class="pl-10 pr-4 py-1.5 bg-surface-container dark:bg-slate-800 border border-outline-variant dark:border-slate-700 rounded-full text-body-md focus:ring-2 focus:ring-primary outline-none transition-all w-64 text-on-surface dark:text-slate-200"
            placeholder="Search key or text..."
            type="text"
          />
        </div>
        <button
          @click="toggleDarkMode"
          class="material-symbols-outlined text-on-surface-variant dark:text-slate-400 hover:text-primary transition-colors"
          title="Toggle Theme"
        >
          {{ isDark ? 'light_mode' : 'dark_mode' }}
        </button>
      </div>
    </header>

    <!-- Workspace Context Selector (RF-01) -->
    <WorkspaceContextSelector />

    <!-- Page Layout Main Content (3 Columns Grid) -->
    <div class="flex-1 grid grid-cols-12 overflow-hidden">
      <NamespaceSidebar />
      <KeysMatrix />
      <TranslationDrawer />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import WorkspaceContextSelector from '../components/labeling/WorkspaceContextSelector.vue'
import NamespaceSidebar from '../components/labeling/NamespaceSidebar.vue'
import KeysMatrix from '../components/labeling/KeysMatrix.vue'
import TranslationDrawer from '../components/labeling/TranslationDrawer.vue'
import { useLabelingState } from '../composables/useLabelingState'

const state = useLabelingState()
const isDark = ref(false)

const DARK_MODE_KEY = 'mui-labeling-dark-mode'

onMounted(() => {
  const stored = localStorage.getItem(DARK_MODE_KEY)
  isDark.value = stored === 'true'
  applyDarkMode()
})

function toggleDarkMode() {
  isDark.value = !isDark.value
  localStorage.setItem(DARK_MODE_KEY, String(isDark.value))
  applyDarkMode()
}

function applyDarkMode() {
  document.documentElement.classList.toggle('dark', isDark.value)
}
</script>
