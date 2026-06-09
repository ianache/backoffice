<template>
  <div class="p-8 text-on-surface">
    <h1 class="text-2xl font-semibold mb-2 text-primary">Stub Domain</h1>
    <p class="text-sm opacity-70">
      This view is served from the <strong>mui-stub</strong> remote via Module Federation.
      If you see this, the federation singleton loop is working correctly.
    </p>
  </div>
</template>

<script setup lang="ts">
// No store access in stub — keeps Phase 9 test clean
</script>
