<script setup lang="ts">
import { ref, computed } from 'vue'
import type { Company } from '../../services/companies'

type StatusFilter = 'all' | 'active' | 'inactive'

const props = defineProps<{
  companies: Company[]
  loading?: boolean
}>()

const emit = defineEmits(['edit'])

const statusFilter = ref<StatusFilter>('all')

const filteredCompanies = computed(() => {
  if (statusFilter.value === 'all') return props.companies
  return props.companies.filter(c => c.status === statusFilter.value)
})

const formatDate = (iso: string) => {
  return new Date(iso).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  })
}
</script>

<template>
  <div class="flex flex-col overflow-hidden">
    <!-- Toolbar -->
    <div class="px-md py-sm flex flex-wrap items-center justify-between gap-md border-b border-outline-variant bg-surface-container-low/50 min-h-[52px]">
      <div class="flex items-center gap-lg">
        <h2 class="text-title-md font-medium text-on-surface whitespace-nowrap">Company Catalog</h2>
        <div class="flex items-center gap-xs bg-surface-container-lowest border border-outline-variant rounded-lg p-1">
          <button
            v-for="tab in (['all', 'active', 'inactive'] as StatusFilter[])"
            :key="tab"
            @click="statusFilter = tab"
            :class="[
              'px-md py-1.5 rounded-md text-label-md transition-colors capitalize',
              statusFilter === tab
                ? 'bg-surface-container-high font-bold text-primary'
                : 'text-secondary hover:text-on-surface font-medium'
            ]"
          >
            {{ tab }}
          </button>
        </div>
      </div>
    </div>

    <!-- Table -->
    <div class="overflow-x-auto">
      <table class="w-full text-left border-collapse">
        <thead>
          <tr class="bg-surface-container-low border-b border-outline-variant">
            <th class="px-lg py-md table-col-header">Id</th>
            <th class="px-lg py-md table-col-header">Name</th>
            <th class="px-lg py-md table-col-header">Tenant</th>
            <th class="px-lg py-md table-col-header">Status</th>
            <th class="px-lg py-md table-col-header">Created</th>
            <th class="px-lg py-md table-col-header">Last Updated</th>
            <th class="px-lg py-md table-col-header text-right">Actions</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-outline-variant">
          <tr
            v-for="company in filteredCompanies"
            :key="company.id"
            class="hover:bg-surface-container-lowest transition-colors group cursor-pointer"
            @click="emit('edit', company)"
          >
            <!-- Id (slug) -->
            <td class="px-lg py-lg">
              <span class="text-label-md font-mono text-primary">{{ company.id }}</span>
            </td>
            <!-- Name -->
            <td class="px-lg py-lg">
              <span class="text-label-md font-bold text-on-background group-hover:text-primary transition-colors">{{ company.name }}</span>
            </td>
            <!-- Tenant -->
            <td class="px-lg py-lg text-body-md text-on-surface-variant font-mono tabular-nums">
              {{ company.tenant_id }}
            </td>
            <!-- Status -->
            <td class="px-lg py-lg">
              <div class="flex items-center gap-2">
                <span :class="['flex h-2 w-2 rounded-full', company.status === 'active' ? 'bg-emerald-500' : 'bg-slate-400']"></span>
                <span :class="['text-label-sm capitalize', company.status === 'active' ? 'text-emerald-700 font-bold' : 'text-secondary']">{{ company.status }}</span>
              </div>
            </td>
            <!-- Created -->
            <td class="px-lg py-lg text-body-md text-on-surface-variant font-mono tabular-nums">
              {{ formatDate(company.created_at) }}
            </td>
            <!-- Last Updated -->
            <td class="px-lg py-lg text-body-md text-on-surface-variant font-mono tabular-nums">
              {{ formatDate(company.updated_at) }}
            </td>
            <!-- Actions -->
            <td class="px-lg py-lg text-right">
              <button
                @click.stop="emit('edit', company)"
                class="p-sm text-secondary hover:text-primary hover:bg-primary-fixed rounded-lg transition-all active:scale-95"
                title="Edit Company"
              >
                <span class="material-symbols-outlined icon-action">edit</span>
              </button>
            </td>
          </tr>
          <tr v-if="!loading && filteredCompanies.length === 0">
            <td colspan="7" class="px-lg py-xl text-center text-on-surface-variant text-body-md">
              No companies found. Create your first company.
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Footer -->
    <div class="p-md bg-surface flex items-center justify-between border-t border-outline-variant">
      <span class="text-label-sm text-secondary">Showing {{ filteredCompanies.length }} of {{ companies.length }} companies</span>
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
}
</style>
