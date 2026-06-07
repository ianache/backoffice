<script setup lang="ts">
import { ref } from 'vue'
import type { Tenant } from '../../services/tenants'
import StitchTextField from '../ui/StitchTextField.vue'

const props = defineProps<{
  tenants: Tenant[]
  isLoading: boolean
}>()

const emit = defineEmits(['edit', 'delete', 'suspend', 'search'])

const searchQuery = ref('')
const selectedIds = ref<Set<number>>(new Set())

const handleSearch = () => {
  emit('search', searchQuery.value)
}

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleDateString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  })
}

const toggleSelectAll = (event: any) => {
  if (event.target.checked) {
    props.tenants.forEach(t => selectedIds.value.add(t.id))
  } else {
    selectedIds.value.clear()
  }
}

const toggleSelect = (id: number, checked: boolean) => {
  if (checked) {
    selectedIds.value.add(id)
  } else {
    selectedIds.value.delete(id)
  }
}

// Menu handling
const activeMenu = ref<number | null>(null)
const toggleMenu = (id: number) => {
  if (activeMenu.value === id) {
    activeMenu.value = null
  } else {
    activeMenu.value = id
  }
}
</script>

<template>
  <div class="flex flex-col bg-surface overflow-hidden">
    <!-- Toolbar — search + bulk actions -->
    <div class="px-4 py-2 border-b border-outline-variant flex items-center justify-between gap-4 min-h-[52px]">
      <div class="w-full max-w-xs">
        <StitchTextField
          v-model="searchQuery"
          placeholder="Search tenants..."
          @input="handleSearch"
        >
          <template #leading-icon>
            <md-icon>search</md-icon>
          </template>
        </StitchTextField>
      </div>

      <div class="flex items-center gap-0.5 shrink-0">
        <md-icon-button :aria-disabled="selectedIds.size === 0 ? 'true' : 'false'" :title="'Delete selected'">
          <md-icon>delete</md-icon>
        </md-icon-button>
        <md-icon-button title="Filter">
          <md-icon>filter_list</md-icon>
        </md-icon-button>
        <md-icon-button title="More options">
          <md-icon>more_vert</md-icon>
        </md-icon-button>
      </div>
    </div>

    <!-- Data Table — high-density compact rows -->
    <div class="overflow-x-auto">
      <table class="w-full border-collapse text-left table-fixed">
        <colgroup>
          <col class="w-10" />
          <col class="w-[260px]" />
          <col class="w-[100px]" />
          <col class="w-[110px]" />
          <col />
          <col class="w-[110px]" />
          <col class="w-[88px]" />
        </colgroup>
        <thead>
          <tr class="bg-surface-container-low border-b border-outline-variant">
            <th class="pl-4 pr-2 py-2 w-10">
              <md-checkbox
                @change="toggleSelectAll"
                :indeterminate="selectedIds.size > 0 && selectedIds.size < tenants.length"
              ></md-checkbox>
            </th>
            <th class="px-4 py-2 table-col-header">Tenant Name</th>
            <th class="px-4 py-2 table-col-header text-center">Status</th>
            <th class="px-4 py-2 table-col-header">Country</th>
            <th class="px-4 py-2 table-col-header">Products</th>
            <th class="px-4 py-2 table-col-header">Created</th>
            <th class="px-4 py-2 table-col-header text-right pr-6">Actions</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-outline-variant">
          <!-- Loading state -->
          <tr v-if="isLoading">
            <td colspan="7" class="px-6 py-10 text-center text-on-surface-variant">
              <div class="flex flex-col items-center gap-3">
                <md-linear-progress indeterminate class="w-32"></md-linear-progress>
                <span class="text-sm">Loading tenants...</span>
              </div>
            </td>
          </tr>
          <!-- Empty state -->
          <tr v-else-if="tenants.length === 0">
            <td colspan="7" class="px-6 py-10 text-center text-on-surface-variant text-sm">
              No tenants found matching your search.
            </td>
          </tr>
          <!-- Data rows — compact 36px rows -->
          <tr
            v-for="tenant in tenants"
            :key="tenant.id"
            class="hover:bg-state-hover transition-colors duration-100 group"
          >
            <td class="pl-4 pr-2 py-0">
              <md-checkbox
                :checked="selectedIds.has(tenant.id)"
                @change="(e: any) => toggleSelect(tenant.id, e.target.checked)"
              ></md-checkbox>
            </td>
            <td class="px-4 py-0">
              <div class="flex items-center gap-3 h-9">
                <div class="w-7 h-7 rounded-lg bg-surface-container flex items-center justify-center border border-outline-variant overflow-hidden shrink-0">
                  <img v-if="tenant.logo_url" :src="tenant.logo_url" class="w-full h-full object-contain" />
                  <md-icon v-else class="text-on-surface-variant" style="font-size: 14px;">business</md-icon>
                </div>
                <div class="flex flex-col overflow-hidden">
                  <span class="text-sm font-medium text-on-surface truncate leading-tight">{{ tenant.name }}</span>
                  <span class="text-[10px] text-on-surface-variant font-mono leading-tight">#{{ tenant.id }}</span>
                </div>
              </div>
            </td>
            <td class="px-4 py-0 text-center">
              <span
                :class="[
                  'status-chip',
                  tenant.status === 'active' ? 'status-chip--active' : 'status-chip--suspended'
                ]"
              >
                {{ tenant.status }}
              </span>
            </td>
            <td class="px-4 py-0 text-sm text-on-surface-variant">
              {{ tenant.country }}
            </td>
            <td class="px-4 py-0">
              <div class="flex flex-wrap gap-1 py-1">
                <span
                  v-for="p in tenant.products"
                  :key="p"
                  class="product-chip"
                >
                  {{ p }}
                </span>
              </div>
            </td>
            <td class="px-4 py-0 text-sm text-on-surface-variant tabular-nums">
              {{ formatDate(tenant.created_at) }}
            </td>
            <td class="px-4 py-0 text-right pr-2">
              <!-- Stitch action menu pattern: visible edit + overflow menu -->
              <div class="flex justify-end items-center gap-0">
                <md-icon-button @click="emit('edit', tenant)" title="Edit">
                  <md-icon>edit</md-icon>
                </md-icon-button>

                <div class="relative">
                  <md-icon-button :id="`anchor-${tenant.id}`" @click="toggleMenu(tenant.id)" title="More actions">
                    <md-icon>more_vert</md-icon>
                  </md-icon-button>
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

    <!-- Table Footer / Pagination — compact Stitch style -->
    <div class="px-4 py-1.5 border-t border-outline-variant flex items-center justify-end bg-surface gap-4 min-h-[44px]">
      <span class="table-pagination-text">Rows per page: 10</span>
      <span class="table-pagination-text">
        {{ tenants.length === 0 ? '0' : `1–${tenants.length}` }} of {{ tenants.length }}
      </span>
      <div class="flex">
        <md-icon-button disabled title="Previous page"><md-icon>chevron_left</md-icon></md-icon-button>
        <md-icon-button disabled title="Next page"><md-icon>chevron_right</md-icon></md-icon-button>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Column header — Stitch enterprise label style */
.table-col-header {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  color: var(--on-surface-variant);
  white-space: nowrap;
}

/* High-density row hover — M3 state layer (8% primary tint) */
.hover\:bg-state-hover:hover {
  background-color: color-mix(in srgb, var(--primary) 8%, transparent);
}

/* Status chips — tonal container pattern */
.status-chip {
  display: inline-flex;
  align-items: center;
  padding: 1px 8px;
  border-radius: 4px;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  border: 1px solid transparent;
}

.status-chip--active {
  background-color: #e6f4ea;
  color: #137333;
  border-color: rgba(19, 115, 51, 0.2);
}

[data-theme='dark'] .status-chip--active {
  background-color: rgba(52, 168, 83, 0.15);
  color: #81c995;
  border-color: rgba(52, 168, 83, 0.25);
}

.status-chip--suspended {
  background-color: var(--error-container);
  color: var(--on-error-container);
  border-color: color-mix(in srgb, var(--error) 20%, transparent);
}

/* Product chips — secondary-container tonal style */
.product-chip {
  display: inline-flex;
  padding: 1px 6px;
  border-radius: 4px;
  background-color: var(--secondary-container);
  color: var(--on-secondary-container);
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.03em;
  text-transform: uppercase;
}

/* Pagination text */
.table-pagination-text {
  font-size: 11px;
  font-weight: 500;
  color: var(--on-surface-variant);
}

/* Danger menu item */
.menu-item-danger {
  --md-menu-item-label-text-color: var(--error);
}

.menu-item-danger md-icon {
  color: var(--error);
}
</style>
