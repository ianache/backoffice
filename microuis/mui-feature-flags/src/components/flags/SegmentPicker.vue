<script setup lang="ts">
import type { Segment } from '../../services/flags'

const props = defineProps<{
  segments: Segment[]
  modelValue: number[]
}>()

const emit = defineEmits<{
  'update:modelValue': [ids: number[]]
}>()

function toggleSegment(id: number) {
  const current = props.modelValue
  const idx = current.indexOf(id)
  if (idx === -1) {
    emit('update:modelValue', [...current, id])
  } else {
    emit('update:modelValue', current.filter(i => i !== id))
  }
}

function isSelected(id: number): boolean {
  return props.modelValue.includes(id)
}
</script>

<template>
  <div class="segment-picker flex flex-wrap gap-1.5">
    <p v-if="segments.length === 0" class="text-xs text-on-surface-variant">
      No segments available.
    </p>
    <button
      v-for="segment in segments"
      :key="segment.id"
      type="button"
      :class="[
        'px-2.5 py-1 rounded-full text-xs font-medium border transition-colors',
        isSelected(segment.id)
          ? 'bg-primary-container text-on-primary-container border-primary'
          : 'bg-surface-container text-on-surface-variant border-outline-variant hover:bg-surface-container-high'
      ]"
      @click="toggleSegment(segment.id)"
    >
      {{ segment.name }}
    </button>
  </div>
</template>
