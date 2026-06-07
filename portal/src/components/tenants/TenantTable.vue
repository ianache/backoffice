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
    <!-- Table Header / Toolbar -->
    <div class="p-4 border-b border-outline-variant flex items-center justify-between">
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
      
      <div class="flex items-center gap-1">
         <md-icon-button :disabled="selectedIds.size === 0">
           <md-icon>delete</md-icon>
         </md-icon-button>
         <md-icon-button>
           <md-icon>filter_list</md-icon>
         </md-icon-button>
         <md-icon-button>
           <md-icon>more_vert</md-icon>
         </md-icon-button>
      </div>
    </div>

    <!-- Table -->
    <div class="overflow-x-auto">
      <table class="w-full border-collapse text-left">
        <thead>
          <tr class="bg-surface-container-low border-b border-outline-variant">
            <th class="pl-4 pr-2 py-3 w-10">
              <md-checkbox 
                @change="toggleSelectAll"
                :indeterminate="selectedIds.size > 0 && selectedIds.size < tenants.length"
              ></md-checkbox>
            </th>
            <th class="px-4 py-3 text-[11px] font-bold uppercase tracking-wider text-on-surface-variant">Tenant Name</th>
            <th class="px-4 py-3 text-[11px] font-bold uppercase tracking-wider text-on-surface-variant text-center">Status</th>
            <th class="px-4 py-3 text-[11px] font-bold uppercase tracking-wider text-on-surface-variant">Country</th>
            <th class="px-4 py-3 text-[11px] font-bold uppercase tracking-wider text-on-surface-variant">Products</th>
            <th class="px-4 py-3 text-[11px] font-bold uppercase tracking-wider text-on-surface-variant">Created</th>
            <th class="px-4 py-3 text-[11px] font-bold uppercase tracking-wider text-on-surface-variant text-right pr-6">Actions</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-outline-variant">
          <tr v-if="isLoading">
             <td colspan="7" class="px-6 py-12 text-center text-on-surface-variant italic">
               <div class="flex flex-col items-center gap-3">
                 <md-linear-progress indeterminate class="w-32"></md-linear-progress>
                 <span class="text-sm">Loading tenants...</span>
               </div>
             </td>
          </tr>
          <tr v-else-if="tenants.length === 0">
             <td colspan="7" class="px-6 py-12 text-center text-on-surface-variant italic text-sm">
               No tenants found matching your search.
             </td>
          </tr>
          <tr 
            v-for="tenant in tenants" 
            :key="tenant.id"
            class="hover:bg-surface-container-lowest transition-colors group"
          >
            <td class="pl-4 pr-2 py-1">
              <md-checkbox 
                :checked="selectedIds.has(tenant.id)"
                @change="(e: any) => toggleSelect(tenant.id, e.target.checked)"
              ></md-checkbox>
            </td>
            <td class="px-4 py-1">
              <div class="flex items-center gap-3">
                <div class="w-8 h-8 rounded-lg bg-surface-container flex items-center justify-center border border-outline-variant overflow-hidden shrink-0">
                  <img v-if="tenant.logo_url" :src="tenant.logo_url" class="w-full h-full object-contain" />
                  <md-icon v-else class="text-on-surface-variant text-sm">business</md-icon>
                </div>
                <div class="flex flex-col overflow-hidden">
                  <span class="text-sm font-medium text-on-surface truncate">{{ tenant.name }}</span>
                  <span class="text-[10px] text-on-surface-variant font-mono">#{{ tenant.id }}</span>
                </div>
              </div>
            </td>
            <td class="px-4 py-1 text-center">
              <span 
                :class="[
                  'px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-tighter border',
                  tenant.status === 'active' 
                    ? 'bg-success-container text-on-success-container border-success/20' 
                    : 'bg-error-container text-on-error-container border-error/20'
                ]"
              >
                {{ tenant.status }}
              </span>
            </td>
            <td class="px-4 py-1 text-sm text-on-surface-variant">
              {{ tenant.country }}
            </td>
            <td class="px-4 py-1">
              <div class="flex flex-wrap gap-1">
                <span 
                  v-for="p in tenant.products" 
                  :key="p" 
                  class="px-1.5 py-0.5 rounded bg-secondary-container text-on-secondary-container text-[10px] font-bold uppercase"
                >
                  {{ p }}
                </span>
              </div>
            </td>
            <td class="px-4 py-1 text-sm text-on-surface-variant">
              {{ formatDate(tenant.created_at) }}
            </td>
            <td class="px-4 py-1 text-right pr-4">
              <div class="flex justify-end gap-0.5">
                <md-icon-button @click="emit('edit', tenant)">
                  <md-icon>edit</md-icon>
                </md-icon-button>
                
                <div class="relative">
                  <md-icon-button :id="`anchor-${tenant.id}`" @click="toggleMenu(tenant.id)">
                    <md-icon>more_vert</md-icon>
                  </md-icon-button>
                  <md-menu 
                    :anchor="`anchor-${tenant.id}`" 
                    :open="activeMenu === tenant.id"
                    @closed="activeMenu = null"
                    quick
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
                    <md-menu-item @click="emit('delete', tenant)">
                      <div slot="headline" class="text-error">Delete</div>
                      <md-icon slot="start" class="text-error">delete</md-icon>
                    </md-menu-item>
                  </md-menu>
                </div>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    
    <!-- Table Footer / Pagination -->
    <div class="p-2 border-t border-outline-variant flex items-center justify-end bg-surface text-[11px] text-on-surface-variant font-medium">
      <span class="mr-4">Rows per page: 10</span>
      <span class="mr-4">1-{{ tenants.length }} of {{ tenants.length }}</span>
      <div class="flex">
        <md-icon-button disabled><md-icon>chevron_left</md-icon></md-icon-button>
        <md-icon-button disabled><md-icon>chevron_right</md-icon></md-icon-button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.text-error {
  color: var(--error);
}
</style>
