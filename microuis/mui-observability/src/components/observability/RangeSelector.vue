<script setup lang="ts">
defineProps<{
  modelValue: '24h' | '7d' | '30d'
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: '24h' | '7d' | '30d'): void
}>()
</script>

<template>
  <div class="inline-flex items-center gap-xs p-xs bg-surface-container rounded-full select-none">
    <button
      v-for="range in (['24h', '7d', '30d'] as const)"
      :key="range"
      type="button"
      :class="[
        'px-md py-1 rounded-full text-label-md font-bold transition-colors cursor-pointer',
        modelValue === range
          ? 'bg-primary text-on-primary'
          : 'text-on-surface-variant hover:bg-surface-container-high'
      ]"
      @click="emit('update:modelValue', range)"
    >
      {{ range }}
    </button>
  </div>
</template>
