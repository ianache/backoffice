<template>
  <div class="min-h-screen flex items-center justify-center bg-surface p-4 transition-colors duration-300">
    <div class="w-full max-w-md">
      <div class="flex flex-col items-center mb-8">
        <div class="h-12 w-12 rounded-xl bg-primary flex items-center justify-center mb-4 shadow-lg shadow-primary/20">
          <md-icon class="text-on-primary">shield</md-icon>
        </div>
        <h1 class="text-3xl font-bold text-on-surface tracking-tight mb-2">BackOffice</h1>
        <p class="text-on-surface-variant font-medium">Multi-Tenant Platform</p>
      </div>
      
      <div class="bg-surface-container rounded-2xl p-8 border border-outline-variant shadow-sm">
        <slot />
      </div>
      
      <div class="mt-8 text-center text-on-surface-variant text-sm">
        &copy; {{ new Date().getFullYear() }} Comsatel. All rights reserved.
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
</script>
