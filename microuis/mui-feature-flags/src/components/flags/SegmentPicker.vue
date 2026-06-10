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
  <div class="segment-picker">
    <!-- Empty state -->
    <div v-if="segments.length === 0" class="empty-state">
      <span class="material-symbols-outlined text-[32px] opacity-40">group</span>
      <p class="text-sm text-on-surface-variant">No segments available.</p>
    </div>

    <!-- Segment list -->
    <div v-else class="flex flex-col gap-1">
      <button
        v-for="segment in segments"
        :key="segment.id"
        type="button"
        class="segment-item"
        :class="{ 'segment-item--selected': isSelected(segment.id) }"
        @click="toggleSegment(segment.id)"
      >
        <div class="flex items-center gap-sm">
          <div
            class="check-box"
            :class="{ 'check-box--checked': isSelected(segment.id) }"
          >
            <span v-if="isSelected(segment.id)" class="material-symbols-outlined text-[14px] text-on-primary">check</span>
          </div>
          <div class="flex flex-col text-left">
            <span class="text-sm font-medium text-on-surface">{{ segment.name }}</span>
            <span v-if="segment.description" class="text-xs text-on-surface-variant">{{ segment.description }}</span>
          </div>
        </div>
        <span class="text-xs text-on-surface-variant">{{ segment.members.length }} members</span>
      </button>
    </div>
  </div>
</template>

<style scoped>
.segment-picker {
  border: 1px solid var(--outline-variant);
  border-radius: var(--rounded);
  overflow: hidden;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 24px;
  color: var(--on-surface-variant);
}

.segment-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  border: none;
  background: var(--surface-container-lowest);
  cursor: pointer;
  transition: background-color 0.15s;
  border-bottom: 1px solid var(--outline-variant);
  width: 100%;
}

.segment-item:last-child {
  border-bottom: none;
}

.segment-item:hover {
  background: var(--surface-container-low);
}

.segment-item--selected {
  background: color-mix(in srgb, var(--primary) 8%, transparent);
}

.check-box {
  width: 18px;
  height: 18px;
  border-radius: 4px;
  border: 2px solid var(--outline);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: all 0.15s;
}

.check-box--checked {
  background: var(--primary);
  border-color: var(--primary);
}
</style>
