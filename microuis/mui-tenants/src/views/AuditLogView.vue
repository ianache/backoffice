<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useAuditStore } from '../stores/audit'
import type { AuditLogFilters, AuditLogEntry } from '../services/audit'
import DiffModal from '../components/audit/DiffModal.vue'

const auditStore = useAuditStore()

// Filter state
const environmentFilter = ref('')
const actionTypeFilter = ref('')
const userFilter = ref('')
const startDate = ref('')
const endDate = ref('')

// Last-applied filters (used by pagination so it doesn't reset filters)
const lastFilters = ref<AuditLogFilters>({})

const ACTION_TYPES = [
  'CREATE_FLAG',
  'UPDATE_FLAG',
  'DELETE_FLAG',
  'ENABLE_FLAG',
  'DISABLE_FLAG',
  'CREATE_SEGMENT',
  'UPDATE_SEGMENT',
  'DELETE_SEGMENT',
  'CREATE_USER',
  'UPDATE_USER',
  'ENABLE_USER',
  'DISABLE_USER',
  'RESET_MFA',
  'CREATE_TENANT',
  'UPDATE_TENANT',
  'DELETE_TENANT',
  'CREATE_COMPANY',
  'UPDATE_COMPANY',
]

const showDiffModal = ref(false)

onMounted(() => {
  auditStore.fetchAuditLogs()
})

function applyFilters() {
  const filters: AuditLogFilters = {
    environment: environmentFilter.value || undefined,
    action_type: actionTypeFilter.value || undefined,
    user_id: userFilter.value || undefined,
    start_date: startDate.value || undefined,
    end_date: endDate.value || undefined,
    page: 1,
  }
  lastFilters.value = filters
  auditStore.fetchAuditLogs(filters)
}

function goToPage(n: number) {
  auditStore.fetchAuditLogs({ ...lastFilters.value, page: n })
}

function openDiff(id: number) {
  showDiffModal.value = true
  auditStore.fetchDiff(id)
}

// --- Formatting helpers ---

function formatActionLabel(actionType: string): string {
  return actionType
    .toLowerCase()
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}

function iconForAction(actionType: string): string {
  if (actionType.startsWith('CREATE_')) return 'add_circle'
  if (actionType.startsWith('DELETE_')) return 'delete'
  return 'published_with_changes'
}

function iconColorClass(actionType: string): string {
  if (actionType.startsWith('CREATE_')) return 'icon-badge-create'
  if (actionType.startsWith('DELETE_')) return 'icon-badge-delete'
  return 'icon-badge-update'
}

function environmentBadgeClass(environment: string): string {
  switch (environment) {
    case 'production':
      return 'bg-error-container text-on-error-container'
    case 'staging':
      return 'bg-tertiary-container text-on-tertiary-container'
    case 'development':
      return 'bg-secondary-container text-on-secondary-container'
    default:
      return 'bg-surface-container-high text-on-surface-variant'
  }
}

function formatDateDivider(dateStr: string): string {
  const date = new Date(dateStr)
  const today = new Date()
  const yesterday = new Date(today)
  yesterday.setDate(today.getDate() - 1)

  if (date.toDateString() === today.toDateString()) {
    return `Today, ${date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}`
  }
  if (date.toDateString() === yesterday.toDateString()) {
    return `Yesterday, ${date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}`
  }
  return date.toLocaleDateString('en-US', { weekday: 'long', month: 'short', day: 'numeric', year: 'numeric' })
}

// --- Grouped entries by date ---

interface EntryGroup {
  dateKey: string
  dateLabel: string
  entries: AuditLogEntry[]
}

const groupedEntries = computed<EntryGroup[]>(() => {
  const groups: EntryGroup[] = []
  const map = new Map<string, EntryGroup>()

  for (const entry of auditStore.items) {
    const dateKey = new Date(entry.created_at).toDateString()
    let group = map.get(dateKey)
    if (!group) {
      group = { dateKey, dateLabel: formatDateDivider(entry.created_at), entries: [] }
      map.set(dateKey, group)
      groups.push(group)
    }
    group.entries.push(entry)
  }

  return groups
})

// --- Pagination ---

const from = computed(() => (auditStore.total === 0 ? 0 : (auditStore.page - 1) * auditStore.limit + 1))
const to = computed(() => Math.min(auditStore.page * auditStore.limit, auditStore.total))
const totalPages = computed(() => Math.max(1, Math.ceil(auditStore.total / auditStore.limit)))

const pageNumbers = computed(() => {
  const pages: number[] = []
  const current = auditStore.page
  const total = totalPages.value
  let start = Math.max(1, current - 2)
  let end = Math.min(total, start + 4)
  start = Math.max(1, end - 4)

  for (let i = start; i <= end; i++) {
    pages.push(i)
  }
  return pages
})
</script>

<template>
  <div class="flex flex-col gap-lg">
    <!-- Page Header -->
    <div class="max-w-3xl">
      <h1 class="text-headline-lg font-semibold text-on-surface leading-tight tracking-tight">Audit Log</h1>
      <p class="text-body-md text-on-surface-variant mt-1">Track every configuration change across the platform.</p>
    </div>

    <!-- Filter Bar -->
    <div class="grid grid-cols-1 md:grid-cols-4 lg:grid-cols-5 gap-md p-md bg-surface-container-lowest border border-outline-variant rounded-xl shadow-sm">
      <div class="flex flex-col gap-1">
        <label class="text-xs font-bold text-on-surface-variant uppercase">Environment</label>
        <select v-model="environmentFilter" class="bg-surface border border-outline-variant rounded-lg px-sm py-2 text-sm focus:ring-1 focus:ring-primary focus:border-primary outline-none">
          <option value="">All Environments</option>
          <option value="development">Development</option>
          <option value="staging">QA / Staging</option>
          <option value="production">Production</option>
        </select>
      </div>

      <div class="flex flex-col gap-1">
        <label class="text-xs font-bold text-on-surface-variant uppercase">Action Type</label>
        <select v-model="actionTypeFilter" class="bg-surface border border-outline-variant rounded-lg px-sm py-2 text-sm focus:ring-1 focus:ring-primary focus:border-primary outline-none">
          <option value="">All Action Types</option>
          <option v-for="action in ACTION_TYPES" :key="action" :value="action">{{ formatActionLabel(action) }}</option>
        </select>
      </div>

      <div class="flex flex-col gap-1">
        <label class="text-xs font-bold text-on-surface-variant uppercase">User</label>
        <input
          v-model="userFilter"
          type="text"
          placeholder="User ID"
          class="bg-surface border border-outline-variant rounded-lg px-sm py-2 text-sm focus:ring-1 focus:ring-primary focus:border-primary outline-none"
        />
      </div>

      <div class="flex flex-col gap-1">
        <label class="text-xs font-bold text-on-surface-variant uppercase">Start Date</label>
        <input
          v-model="startDate"
          type="date"
          class="bg-surface border border-outline-variant rounded-lg px-sm py-2 text-sm focus:ring-1 focus:ring-primary focus:border-primary outline-none"
        />
      </div>

      <div class="flex flex-col gap-1">
        <label class="text-xs font-bold text-on-surface-variant uppercase">End Date</label>
        <input
          v-model="endDate"
          type="date"
          class="bg-surface border border-outline-variant rounded-lg px-sm py-2 text-sm focus:ring-1 focus:ring-primary focus:border-primary outline-none"
        />
      </div>

      <div class="flex items-end md:col-span-4 lg:col-span-5">
        <button
          @click="applyFilters"
          class="h-10 px-lg flex items-center justify-center bg-primary text-on-primary font-bold rounded-lg hover:bg-primary-container transition-all"
        >
          Apply Filters
        </button>
      </div>
    </div>

    <!-- Loading state -->
    <div v-if="auditStore.isLoading" class="text-center text-on-surface-variant py-xl">
      Loading audit log…
    </div>

    <!-- Empty state -->
    <div v-else-if="auditStore.items.length === 0" class="text-center text-on-surface-variant py-xl bg-surface-container-lowest border border-outline-variant rounded-xl">
      No audit log entries found for the selected filters.
    </div>

    <!-- Timeline -->
    <section v-else class="relative timeline-line pl-md">
      <template v-for="group in groupedEntries" :key="group.dateKey">
        <!-- Date Divider -->
        <div class="relative z-10 mb-lg mt-lg first:mt-0">
          <div class="inline-flex items-center bg-surface-container-high px-md py-1 rounded-full text-xs font-bold text-on-surface-variant uppercase tracking-wider border border-outline-variant">
            {{ group.dateLabel }}
          </div>
        </div>

        <!-- Timeline Entries -->
        <div v-for="entry in group.entries" :key="entry.id" class="relative pl-12 mb-lg">
          <div :class="['absolute left-0 top-1 w-10 h-10 rounded-full flex items-center justify-center ring-4 ring-background z-10', iconColorClass(entry.action_type)]">
            <span class="material-symbols-outlined">{{ iconForAction(entry.action_type) }}</span>
          </div>
          <div class="bg-surface-container-lowest border border-outline-variant rounded-xl p-md shadow-sm hover:shadow-md transition-shadow">
            <div class="flex flex-wrap items-start justify-between gap-md">
              <div>
                <p class="text-on-surface font-title-md">
                  <span class="font-bold">{{ entry.user_email || entry.user_id }}</span>
                  performed {{ formatActionLabel(entry.action_type) }}
                  on {{ entry.target_type }} <span class="font-mono text-primary">{{ entry.target_id }}</span>
                </p>
                <div class="flex items-center mt-2 gap-md text-sm flex-wrap">
                  <div class="flex items-center text-on-surface-variant">
                    <span class="material-symbols-outlined text-[16px] mr-1">schedule</span>
                    {{ new Date(entry.created_at).toLocaleString() }}
                  </div>
                  <div :class="['flex items-center px-2 py-0.5 rounded-full text-[10px] font-black uppercase', environmentBadgeClass(entry.environment)]">
                    {{ entry.environment }}
                  </div>
                </div>
              </div>
              <button
                @click="openDiff(entry.id)"
                class="flex items-center px-md py-1.5 border border-primary text-primary font-bold text-sm rounded-lg hover:bg-primary-container hover:text-on-primary-container transition-all shrink-0"
              >
                View Diff
              </button>
            </div>
          </div>
        </div>
      </template>
    </section>

    <!-- Pagination -->
    <div v-if="auditStore.total > 0" class="flex items-center justify-between border-t border-outline-variant pt-lg flex-wrap gap-md">
      <p class="text-sm text-on-surface-variant">Showing {{ from }} to {{ to }} of {{ auditStore.total }} entries</p>
      <div class="flex items-center gap-sm">
        <button
          class="px-md py-sm border border-outline-variant rounded-lg text-sm font-bold text-on-surface hover:bg-surface-container-low disabled:opacity-50"
          :disabled="auditStore.page <= 1"
          @click="goToPage(auditStore.page - 1)"
        >
          Previous
        </button>
        <div class="flex items-center gap-1">
          <button
            v-for="n in pageNumbers"
            :key="n"
            :class="[
              'w-10 h-10 rounded-lg text-sm font-bold transition-colors',
              n === auditStore.page ? 'bg-primary text-on-primary' : 'hover:bg-surface-container-low'
            ]"
            @click="goToPage(n)"
          >
            {{ n }}
          </button>
        </div>
        <button
          class="px-md py-sm border border-outline-variant rounded-lg text-sm font-bold text-on-surface hover:bg-surface-container-low disabled:opacity-50"
          :disabled="auditStore.page >= totalPages"
          @click="goToPage(auditStore.page + 1)"
        >
          Next
        </button>
      </div>
    </div>

    <DiffModal
      :show="showDiffModal"
      :diff="auditStore.diff"
      :is-loading="auditStore.isLoadingDiff"
      :error="auditStore.diffError"
      @close="showDiffModal = false"
    />
  </div>
</template>

<style scoped>
.timeline-line {
  position: relative;
}
.timeline-line::before {
  content: '';
  position: absolute;
  left: 20px;
  top: 0;
  bottom: 0;
  width: 2px;
  background-color: var(--outline-variant);
  z-index: 0;
}
.icon-badge-create {
  background: var(--secondary-container);
  color: var(--on-secondary-container);
}
.icon-badge-delete {
  background: var(--error-container);
  color: var(--on-error-container);
}
.icon-badge-update {
  background: var(--primary-container);
  color: var(--on-primary-container);
}
</style>
