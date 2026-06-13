<template>
  <section class="bg-surface-container-low dark:bg-slate-900 border-b border-outline-variant dark:border-slate-800 px-lg py-md flex flex-wrap items-center justify-between gap-md">
    <!-- Selector de Contexto (RF-01) -->
    <div class="flex flex-wrap items-center gap-md">
      <div class="flex items-center gap-xs">
        <span class="material-symbols-outlined text-primary dark:text-primary-fixed-dim">layers</span>
        <span class="font-label-sm uppercase tracking-wider text-on-surface-variant dark:text-slate-400">Contexto de Resolución:</span>
      </div>
      <!-- Tenant Selector -->
      <div class="flex flex-col">
        <label class="text-[10px] text-on-surface-variant dark:text-slate-400 uppercase font-bold">Tenant</label>
        <select
          id="tenantSelect"
          v-model="selectedTenantId"
          :disabled="!isPlatformAdmin"
          class="bg-surface dark:bg-slate-800 border border-outline-variant dark:border-slate-700 rounded px-sm py-1 font-body-md text-sm text-on-surface dark:text-slate-200 focus:ring-primary focus:border-primary disabled:opacity-60"
        >
          <option v-for="opt in tenantOptions" :key="opt.id" :value="opt.id">
            {{ opt.name }} ({{ opt.id }})
          </option>
        </select>
      </div>
      <span class="text-on-surface-variant dark:text-slate-600 mt-3 font-black">/</span>
      <!-- Company Selector -->
      <div class="flex flex-col">
        <label class="text-[10px] text-on-surface-variant dark:text-slate-400 uppercase font-bold">Company (Override N2)</label>
        <select
          id="companySelect"
          v-model="selectedCompanyId"
          class="bg-surface dark:bg-slate-800 border border-outline-variant dark:border-slate-700 rounded px-sm py-1 font-body-md text-sm text-on-surface dark:text-slate-200 focus:ring-primary focus:border-primary"
        >
          <option value="">Ninguno (Global Tenant)</option>
          <option v-for="opt in companyOptions" :key="opt.id" :value="opt.id">
            {{ opt.name }} ({{ opt.id }})
          </option>
        </select>
      </div>
      <span class="text-on-surface-variant dark:text-slate-600 mt-3 font-black">/</span>
      <!-- Product Selector -->
      <div class="flex flex-col">
        <label class="text-[10px] text-on-surface-variant dark:text-slate-400 uppercase font-bold">Product (Override N3)</label>
        <select
          id="productSelect"
          v-model="selectedProductId"
          class="bg-surface dark:bg-slate-800 border border-outline-variant dark:border-slate-700 rounded px-sm py-1 font-body-md text-sm text-on-surface dark:text-slate-200 focus:ring-primary focus:border-primary"
        >
          <option value="">Ninguno (Global Company/Tenant)</option>
          <option v-for="opt in productOptions" :key="opt.id" :value="opt.id">
            {{ opt.name }} ({{ opt.id }})
          </option>
        </select>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useUserContext } from 'shell/useUserContext'
import { listProductsLookup, listCompaniesLookup, listTenantsLookup, type LookupOption } from '../../services/lookups'
import { useLabelingState } from '../../composables/useLabelingState'

const state = useLabelingState()

const tenantOptions = ref<LookupOption[]>([])
// TODO: companies/products lookups don't return tenant_id on LookupOption —
// filter by selected tenant client-side once the lookup response includes it.
const companyOptions = ref<LookupOption[]>([])
const productOptions = ref<LookupOption[]>([])

const isPlatformAdmin = ref(false)

const selectedTenantId = ref('')
const selectedCompanyId = ref('')
const selectedProductId = ref('')

onMounted(async () => {
  const ctx = useUserContext()
  isPlatformAdmin.value = ctx.roles?.includes('PlatformAdmin') ?? false

  if (isPlatformAdmin.value) {
    try {
      tenantOptions.value = await listTenantsLookup()
    } catch {
      tenantOptions.value = ctx.tenant_id ? [{ id: ctx.tenant_id, name: 'My tenant' }] : []
    }
  } else {
    tenantOptions.value = ctx.tenant_id ? [{ id: ctx.tenant_id, name: 'My tenant' }] : []
  }

  selectedTenantId.value = ctx.tenant_id || tenantOptions.value[0]?.id || ''

  try {
    companyOptions.value = await listCompaniesLookup()
  } catch {
    companyOptions.value = []
  }
  try {
    productOptions.value = await listProductsLookup()
  } catch {
    productOptions.value = []
  }

  syncWorkspaceContext()
})

watch([selectedTenantId, selectedCompanyId, selectedProductId], () => {
  syncWorkspaceContext()
})

function syncWorkspaceContext() {
  state.workspaceContext = {
    tenantId: selectedTenantId.value,
    companyId: selectedCompanyId.value || null,
    productId: selectedProductId.value || null,
  }
}
</script>
