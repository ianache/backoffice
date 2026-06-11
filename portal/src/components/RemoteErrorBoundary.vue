<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const displayName = computed(() => (route.meta.remoteDisplayName as string) ?? 'This module')
</script>

<template>
  <div class="flex items-center justify-center min-h-[400px]">
    <div class="rounded-xl border border-error/30 bg-error-container p-8 max-w-md text-center">
      <span class="material-symbols-outlined text-error text-[48px] mb-4 block">cloud_off</span>
      <h2 class="text-lg font-semibold text-on-error-container mb-2">
        {{ displayName }} is unavailable
      </h2>
      <p class="text-sm text-on-error-container/70">
        This module could not be loaded. Try a hard refresh to retry.
      </p>
    </div>
  </div>
</template>
