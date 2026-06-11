<script setup lang="ts">
import type { FeatureFlag } from '../../services/flags'
import { useBoFlags } from 'shell/boFlags'

const { boFeatureCreate, boFeatureUpdate } = useBoFlags()

defineProps<{
  flags: FeatureFlag[]
  isLoading: boolean
}>()

const emit = defineEmits<{
  edit: [flag: FeatureFlag]
  clone: [flag: FeatureFlag]
  promote: [flag: FeatureFlag]
  disable: [flag: FeatureFlag]
  enable: [flag: FeatureFlag]
}>()

function handleToggle(flag: FeatureFlag) {
  if (flag.enabled) {
    emit('disable', flag)
  } else {
    emit('enable', flag)
  }
}

function formatRelativeTime(dateStr: string): string {
  const now = new Date()
  const date = new Date(dateStr)
  const diffMs = now.getTime() - date.getTime()
  const diffSec = Math.floor(diffMs / 1000)
  const diffMin = Math.floor(diffSec / 60)
  const diffHour = Math.floor(diffMin / 60)
  const diffDay = Math.floor(diffHour / 24)

  if (diffDay > 30) return date.toLocaleDateString()
  if (diffDay > 0) return `${diffDay}d ago`
  if (diffHour > 0) return `${diffHour}h ago`
  if (diffMin > 0) return `${diffMin}m ago`
  return 'Just now'
}

function formatTtl(ttl: number | null): string {
  if (!ttl) return 'No expiry'
  return `${ttl}d Rem.`
}
</script>

<template>
  <table class="w-full text-sm">
    <thead>
      <tr class="border-b border-outline-variant bg-surface-container-low">
        <th class="table-th text-left">Flag Name &amp; Description</th>
        <th class="table-th text-left">Status</th>
        <th class="table-th text-left">Complexity</th>
        <th class="table-th text-left">Rollout</th>
        <th class="table-th text-left">TTL</th>
        <th class="table-th text-left">Last Updated</th>
        <th class="table-th text-left">Actions</th>
      </tr>
    </thead>
    <tbody>
      <!-- Loading state -->
      <tr v-if="isLoading">
        <td colspan="7" class="px-4 py-8 text-center text-on-surface-variant">
          <span class="material-symbols-outlined text-[20px] animate-spin mr-2">refresh</span>
          Loading...
        </td>
      </tr>

      <!-- Empty state -->
      <tr v-else-if="flags.length === 0">
        <td colspan="7" class="px-4 py-12 text-center text-on-surface-variant">
          <span class="material-symbols-outlined text-[40px] block mb-2 opacity-40">toggle_on</span>
          No feature flags found. Create your first flag.
        </td>
      </tr>

      <!-- Data rows -->
      <tr
        v-else
        v-for="flag in flags"
        :key="flag.id"
        class="hover:bg-surface-container-low transition-colors group border-b border-outline-variant last:border-0"
      >
        <!-- Flag Name & Description -->
        <td class="table-td">
          <div class="flex flex-col gap-0.5">
            <span class="font-semibold text-primary">{{ flag.name }}</span>
            <span v-if="flag.description" class="text-xs text-on-surface-variant">{{ flag.description }}</span>
            <div v-if="flag.tags && flag.tags.length" class="flex flex-wrap gap-1 mt-1">
              <span
                v-for="tag in flag.tags"
                :key="tag"
                class="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-secondary-container text-on-secondary-container"
              >{{ tag }}</span>
            </div>
          </div>
        </td>

        <!-- Status (toggle) -->
        <td class="table-td">
          <button
            :class="[
              'inline-flex items-center h-6 w-11 rounded-full relative transition-colors duration-200 cursor-pointer focus:outline-none',
              flag.enabled ? 'toggle-checked' : ''
            ]"
            @click="handleToggle(flag)"
            :aria-label="flag.enabled ? 'Disable flag' : 'Enable flag'"
          >
            <span class="toggle-track absolute inset-0 rounded-full bg-outline transition-colors duration-200"></span>
            <span class="toggle-dot absolute left-1 top-1 bg-white w-4 h-4 rounded-full shadow transition-transform duration-200 ease-in-out"></span>
          </button>
        </td>

        <!-- Complexity badge -->
        <td class="table-td">
          <span
            v-if="flag.complex"
            class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold bg-primary-fixed text-primary border border-primary/20"
          >
            <span class="material-symbols-outlined text-[14px]">bolt</span>
            Complex
          </span>
          <span
            v-else
            class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold bg-surface-container text-on-surface-variant"
          >
            <span class="material-symbols-outlined text-[14px]">psychology</span>
            Simple
          </span>
        </td>

        <!-- Rollout progress bar -->
        <td class="table-td">
          <div class="flex flex-col gap-1 min-w-[80px]">
            <div class="h-2 w-full bg-surface-variant rounded-full overflow-hidden">
              <div
                class="h-full bg-primary rounded-full transition-all duration-300"
                :style="{ width: `${flag.rollout}%` }"
              ></div>
            </div>
            <span class="text-xs text-on-surface-variant">{{ flag.rollout }}%</span>
          </div>
        </td>

        <!-- TTL -->
        <td class="table-td text-on-surface-variant">
          {{ formatTtl(flag.ttl) }}
        </td>

        <!-- Last Updated -->
        <td class="table-td text-on-surface-variant">
          {{ formatRelativeTime(flag.updated_at) }}
        </td>

        <!-- Actions (hover only) -->
        <td class="table-td">
          <div class="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity duration-150">
            <button
              v-if="boFeatureUpdate"
              class="p-1.5 rounded-lg hover:bg-surface-container-high transition-colors text-on-surface-variant"
              title="Edit"
              @click="emit('edit', flag)"
            >
              <span class="material-symbols-outlined text-[18px]">edit</span>
            </button>
            <button
              v-if="boFeatureCreate"
              class="p-1.5 rounded-lg hover:bg-surface-container-high transition-colors text-on-surface-variant"
              title="Clone"
              @click="emit('clone', flag)"
            >
              <span class="material-symbols-outlined text-[18px]">content_copy</span>
            </button>
            <button
              class="p-1.5 rounded-lg hover:bg-surface-container-high transition-colors text-primary"
              title="Promote"
              @click="emit('promote', flag)"
            >
              <span class="material-symbols-outlined text-[18px]">rocket_launch</span>
            </button>
          </div>
        </td>
      </tr>
    </tbody>
  </table>
</template>

<style scoped>
.table-th {
  padding: 10px 16px;
  font-size: 0.75rem;
  font-weight: 700;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  color: var(--on-surface-variant);
  white-space: nowrap;
}

.table-td {
  padding: 12px 16px;
  color: var(--on-surface);
  vertical-align: middle;
}

/* Toggle CSS matching design/stitch/feature-flags.html */
.toggle-checked .toggle-dot {
  transform: translateX(18px);
}

.toggle-checked .toggle-track {
  background-color: #d41117;
}
</style>
