<script setup lang="ts">
import { ref, computed } from 'vue'
import type { Tenant } from '../../services/tenants'

const props = defineProps<{
  tenants: Tenant[]
  isLoading: boolean
}>()

const emit = defineEmits(['edit', 'delete', 'suspend'])

type StatusFilter = 'all' | 'active' | 'suspended'
const activeFilter = ref<StatusFilter>('all')
const isCompact = ref(false)
const activeMenu = ref<number | null>(null)

const filteredTenants = computed(() => {
  if (activeFilter.value === 'all') return props.tenants
  return props.tenants.filter(t => t.status === activeFilter.value)
})

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleDateString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  })
}

const derivePlan = (products?: string[]): string => {
  if (!products || products.length === 0) return '—'
  if (products.length <= 2) return 'Starter'
  if (products.length <= 4) return 'Pro'
  return 'Enterprise'
}

const countryMap: Record<string, string> = {
  ES: 'Spain',
  US: 'USA',
  DE: 'Germany',
  FR: 'France',
  GB: 'UK',
  PE: 'Peru'
}

const getCountryName = (code: string) => {
  return countryMap[code.toUpperCase()] || code
}

const toggleMenu = (id: number) => {
  activeMenu.value = activeMenu.value === id ? null : id
}

const ownerInitials = (owner: string) => {
  return owner
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map(w => w[0].toUpperCase())
    .join('')
}
</script>

<template>
  <div class="flex flex-col overflow-hidden">
    <!-- Toolbar -->
    <div class="px-md py-sm flex flex-wrap items-center justify-between gap-md border-b border-outline-variant bg-surface-container-low/50 min-h-[52px]">
      <div class="flex items-center gap-lg">
        <h2 class="text-title-md font-medium text-on-surface whitespace-nowrap">All Tenants</h2>
        <div class="flex items-center gap-xs bg-surface-container-lowest border border-outline-variant rounded-lg p-1">
          <button
            v-for="tab in (['all', 'active', 'suspended'] as StatusFilter[])"
            :key="tab"
            @click="activeFilter = tab"
            :class="[
              'px-md py-xs rounded-md text-label-md transition-colors capitalize whitespace-nowrap',
              activeFilter === tab
                ? 'bg-surface-container-high text-primary font-bold'
                : 'text-secondary hover:text-on-surface font-medium'
            ]"
          >
            {{ tab.charAt(0).toUpperCase() + tab.slice(1) }}
          </button>
        </div>
      </div>
      <div class="flex items-center gap-xs shrink-0">
        <button class="p-sm hover:bg-surface-variant rounded-lg transition-colors" title="Filter">
          <span class="material-symbols-outlined text-on-surface-variant icon-action">filter_list</span>
        </button>
        <button @click="isCompact = !isCompact" class="p-sm hover:bg-surface-variant rounded-lg transition-colors" title="Toggle density">
          <span class="material-symbols-outlined text-on-surface-variant icon-action">{{ isCompact ? 'density_small' : 'density_medium' }}</span>
        </button>
      </div>
    </div>

    <!-- Data Table -->
    <div class="overflow-x-auto">
      <table class="w-full text-left border-collapse">
        <colgroup>
          <col style="min-width: 220px" />
          <col style="width: 120px" />
          <col style="width: 100px" />
          <col style="width: 130px" />
          <col style="width: 140px" />
          <col style="width: 168px" />
        </colgroup>
        <thead>
          <tr class="bg-surface-container-low/30 border-b border-outline-variant">
            <th :class="['px-lg table-col-header', isCompact ? 'py-sm' : 'py-md']">Name</th>
            <th :class="['px-lg table-col-header', isCompact ? 'py-sm' : 'py-md']">Status</th>
            <th :class="['px-lg table-col-header', isCompact ? 'py-sm' : 'py-md']">Plan</th>
            <th :class="['px-lg table-col-header', isCompact ? 'py-sm' : 'py-md']">Created At</th>
            <th :class="['px-lg table-col-header', isCompact ? 'py-sm' : 'py-md']">Owner</th>
            <th :class="['px-lg table-col-header text-right', isCompact ? 'py-sm' : 'py-md']">Actions</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-outline-variant">
          <!-- Loading state -->
          <tr v-if="isLoading">
            <td colspan="6" class="px-lg py-10 text-center text-on-surface-variant">
              <div class="flex flex-col items-center gap-3">
                <md-linear-progress indeterminate class="w-32"></md-linear-progress>
                <span class="text-body-md">Loading tenants...</span>
              </div>
            </td>
          </tr>
          <!-- Empty state -->
          <tr v-else-if="filteredTenants.length === 0">
            <td colspan="6" class="px-lg py-10 text-center text-on-surface-variant text-body-md">
              No tenants found.
            </td>
          </tr>
          <!-- Data rows -->
          <tr
            v-for="tenant in filteredTenants"
            :key="tenant.id"
            class="hover:bg-surface-container-low transition-colors group"
          >
            <!-- Name -->
            <td :class="['px-lg', isCompact ? 'py-sm' : 'py-md']">
              <div class="flex items-center gap-md">
                <div class="w-10 h-10 rounded-lg bg-surface-variant flex items-center justify-center border border-outline-variant overflow-hidden shrink-0">
                  <img v-if="tenant.logo_url" :src="tenant.logo_url" :alt="tenant.name" class="w-full h-full object-cover" />
                  <span v-else class="material-symbols-outlined text-on-surface-variant" style="font-size: 18px">business</span>
                </div>
                <span class="text-title-md font-bold text-primary hover:underline cursor-pointer">{{ tenant.name }}</span>
              </div>
            </td>
            <!-- Status -->
            <td :class="['px-lg', isCompact ? 'py-sm' : 'py-md']">
              <span :class="['status-chip', tenant.status === 'active' ? 'status-active' : (tenant.status === 'pending' ? 'status-pending' : 'status-suspended')]">
                <span class="status-dot" :style="{ backgroundColor: tenant.status === 'active' ? 'var(--status-active-indicator)' : (tenant.status === 'pending' ? '#f59e0b' : 'var(--status-suspended-indicator)') }"></span>
                {{ tenant.status.charAt(0).toUpperCase() + tenant.status.slice(1) }}
              </span>
            </td>
            <!-- Plan -->
            <td :class="['px-lg text-body-md text-on-surface-variant', isCompact ? 'py-sm' : 'py-md']">
              {{ derivePlan(tenant.products) }}
            </td>
            <!-- Created At -->
            <td :class="['px-lg text-body-md text-on-surface-variant font-mono tabular-nums', isCompact ? 'py-sm' : 'py-md']">
              {{ formatDate(tenant.created_at) }}
            </td>
            <!-- Owner -->
            <td :class="['px-lg', isCompact ? 'py-sm' : 'py-md']">
              <div v-if="tenant.owner" class="flex items-center gap-xs">
                <div class="w-6 h-6 rounded-full border border-primary-container bg-primary-fixed text-on-primary-fixed flex items-center justify-center text-[10px] font-bold shrink-0">
                  {{ ownerInitials(tenant.owner) }}
                </div>
                <span class="text-body-md">{{ tenant.owner }}</span>
              </div>
              <span v-else class="text-body-md text-on-surface-variant">—</span>
            </td>
            <!-- Actions -->
            <td :class="['px-lg text-right', isCompact ? 'py-sm' : 'py-md']">
              <div class="flex items-center justify-end gap-xs">
                <button @click="emit('edit', tenant)" class="p-sm text-secondary hover:text-primary hover:bg-primary-fixed rounded-lg transition-all active:scale-95 flex items-center" title="Manage Products">
                  <span class="material-symbols-outlined icon-action">inventory</span>
                </button>
                <button @click="emit('edit', tenant)" class="p-sm text-secondary hover:text-primary hover:bg-primary-fixed rounded-lg transition-all active:scale-95 flex items-center" title="Configure WhiteLabel">
                  <span class="material-symbols-outlined icon-action">palette</span>
                </button>
                <button @click="emit('edit', tenant)" class="p-sm text-secondary hover:text-primary hover:bg-primary-fixed rounded-lg transition-all active:scale-95 flex items-center" title="View Analytics">
                  <span class="material-symbols-outlined icon-action">bar_chart</span>
                </button>
                <div class="relative">
                  <button :id="`anchor-${tenant.id}`" @click="toggleMenu(tenant.id)" class="p-sm text-secondary hover:text-on-surface hover:bg-surface-variant rounded-lg flex items-center" title="More actions">
                    <span class="material-symbols-outlined icon-action">more_vert</span>
                  </button>
                  <md-menu
                    :anchor="`anchor-${tenant.id}`"
                    :open="activeMenu === tenant.id"
                    @closed="activeMenu = null"
                    quick
                    positioning="popover"
                  >
                    <md-menu-item @click="emit('edit', tenant)">
                      <div slot="headline">Edit</div>
                      <md-icon slot="start">edit</md-icon>
                    </md-menu-item>
                    <md-menu-item v-if="tenant.status === 'active'" @click="emit('suspend', tenant)">
                      <div slot="headline">Suspend</div>
                      <md-icon slot="start">block</md-icon>
                    </md-menu-item>
                    <md-divider></md-divider>
                    <md-menu-item @click="emit('delete', tenant)" class="menu-item-danger">
                      <div slot="headline">Delete</div>
                      <md-icon slot="start">delete</md-icon>
                    </md-menu-item>
                  </md-menu>
                </div>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Pagination -->
    <div class="px-md py-sm border-t border-outline-variant flex items-center justify-between bg-surface-container-low/50 min-h-[48px]">
      <p class="text-label-md text-on-surface-variant">
        Showing {{ filteredTenants.length === 0 ? 0 : 1 }} to {{ filteredTenants.length }} of {{ tenants.length }} tenants
      </p>
      <div class="flex items-center gap-sm">
        <button class="p-xs border border-outline-variant rounded-lg bg-surface-container-lowest hover:bg-surface-variant transition-colors opacity-50 cursor-not-allowed" disabled>
          <span class="material-symbols-outlined icon-action">chevron_left</span>
        </button>
        <div class="flex items-center gap-xs">
          <button class="w-8 h-8 rounded-lg bg-primary text-on-primary font-bold text-label-md">1</button>
        </div>
        <button class="p-xs border border-outline-variant rounded-lg bg-surface-container-lowest hover:bg-surface-variant transition-colors opacity-50 cursor-not-allowed" disabled>
          <span class="material-symbols-outlined icon-action">chevron_right</span>
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.table-col-header {
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  color: var(--on-surface-variant);
  white-space: nowrap;
}

.icon-action {
  font-size: 20px;
  display: block;
}

.status-chip {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 10px;
  border-radius: 9999px;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.04em;
}

.status-active {
  background-color: #dcfce7;
  color: #166534;
}

.status-pending {
  background-color: #fef3c7;
  color: #92400e;
}

.status-suspended {
  background-color: #fee2e2;
  color: #991b1b;
}

[data-theme='dark'] .status-active {
  background-color: rgba(52, 168, 83, 0.15);
  color: #86efac;
}

[data-theme='dark'] .status-pending {
  background-color: rgba(245, 158, 11, 0.15);
  color: #fcd34d;
}

[data-theme='dark'] .status-suspended {
  background-color: rgba(239, 68, 68, 0.15);
  color: #fca5a5;
}

.country-initials {
  font-size: 9px;
  font-weight: 700;
  color: var(--on-surface-variant);
}

.action-btn {
  padding: 6px;
  color: var(--secondary);
  border-radius: 8px;
  transition: color 0.15s, background-color 0.15s, transform 0.1s;
  display: flex;
  align-items: center;
}

.action-btn:hover {
  color: var(--primary);
  background-color: color-mix(in srgb, var(--primary) 10%, transparent);
}

.action-btn:active {
  transform: scale(0.95);
}

.action-btn--disabled {
  opacity: 0.35;
  cursor: not-allowed;
  pointer-events: none;
}

.action-btn-muted {
  padding: 6px;
  color: var(--secondary);
  border-radius: 8px;
  transition: color 0.15s, background-color 0.15s;
  display: flex;
  align-items: center;
}

.action-btn-muted:hover {
  color: var(--on-surface);
  background-color: var(--surface-variant);
}

.menu-item-danger {
  --md-menu-item-label-text-color: var(--error);
}

.menu-item-danger md-icon {
  color: var(--error);
}
</style>
