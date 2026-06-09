<script setup lang="ts">
import type { Segment } from '../../services/flags'

defineProps<{
  segments: Segment[]
  isLoading: boolean
}>()

const emit = defineEmits<{
  edit: [segment: Segment]
  delete: [segment: Segment]
}>()
</script>

<template>
  <table class="w-full text-sm">
    <thead>
      <tr class="border-b border-outline-variant bg-surface-container-low">
        <th class="table-th text-left">Name</th>
        <th class="table-th text-left">Type</th>
        <th class="table-th text-left">Members / Rules</th>
        <th class="table-th text-left">Flag Refs</th>
        <th class="table-th text-left">Actions</th>
      </tr>
    </thead>
    <tbody>
      <!-- Loading state -->
      <tr v-if="isLoading">
        <td colspan="5" class="px-4 py-8 text-center text-on-surface-variant">
          <span class="material-symbols-outlined text-[20px] animate-spin mr-2">refresh</span>
          Loading...
        </td>
      </tr>

      <!-- Empty state -->
      <tr v-else-if="segments.length === 0">
        <td colspan="5" class="px-4 py-12 text-center text-on-surface-variant">
          <span class="material-symbols-outlined text-[40px] block mb-2 opacity-40">group</span>
          No segments found. Create your first segment.
        </td>
      </tr>

      <!-- Data rows -->
      <tr
        v-else
        v-for="segment in segments"
        :key="segment.id"
        :class="[
          'group border-b border-outline-variant transition-colors',
          segment.flag_count === 0
            ? 'hover:bg-surface-container-low'
            : 'hover:bg-surface-container-low'
        ]"
      >
        <!-- Name + orphan chip -->
        <td class="px-4 py-3">
          <div class="flex items-center gap-2">
            <span :class="['font-medium', segment.flag_count === 0 ? 'text-on-surface/50' : 'text-on-surface']">
              {{ segment.name }}
            </span>
            <span
              v-if="segment.flag_count === 0"
              class="rounded-full bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-200 px-2 py-0.5 text-xs font-medium"
            >
              Orphan
            </span>
          </div>
          <p v-if="segment.description" class="text-xs text-on-surface-variant mt-0.5 truncate max-w-[280px]">
            {{ segment.description }}
          </p>
        </td>

        <!-- Type badge -->
        <td class="px-4 py-3">
          <span
            :class="[
              'rounded-full px-2 py-0.5 text-xs font-medium',
              segment.type === 'rule_based'
                ? 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200'
                : 'bg-surface-container-high text-on-surface-variant'
            ]"
          >
            {{ segment.type === 'rule_based' ? 'Rule-based' : 'Manual' }}
          </span>
        </td>

        <!-- Members / Rules count -->
        <td class="px-4 py-3 text-on-surface-variant text-xs">
          <span v-if="segment.type === 'rule_based'">
            {{ segment.conditions.length }} condition{{ segment.conditions.length !== 1 ? 's' : '' }}
          </span>
          <span v-else>
            {{ segment.members.length }} member{{ segment.members.length !== 1 ? 's' : '' }}
          </span>
        </td>

        <!-- flag_count badge -->
        <td class="px-4 py-3">
          <span class="rounded-full bg-primary-container text-on-primary-container px-2 py-0.5 text-xs font-medium">
            {{ segment.flag_count }} flag{{ segment.flag_count !== 1 ? 's' : '' }}
          </span>
        </td>

        <!-- Actions (hover-reveal) -->
        <td class="px-4 py-3">
          <div class="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
            <button
              type="button"
              @click="emit('edit', segment)"
              class="flex items-center justify-center w-8 h-8 rounded-lg text-on-surface-variant hover:bg-surface-container-high hover:text-primary transition-colors"
              title="Edit"
            >
              <span class="material-symbols-outlined text-[18px]">edit</span>
            </button>
            <button
              type="button"
              @click="emit('delete', segment)"
              class="flex items-center justify-center w-8 h-8 rounded-lg text-on-surface-variant hover:bg-error-container hover:text-on-error-container transition-colors"
              title="Delete"
            >
              <span class="material-symbols-outlined text-[18px]">delete</span>
            </button>
          </div>
        </td>
      </tr>
    </tbody>
  </table>
</template>

<style scoped>
.table-th {
  padding: 12px 16px;
  font-size: 0.75rem;
  font-weight: 600;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: var(--on-surface-variant);
}
</style>
