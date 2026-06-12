<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useCompaniesStore } from '../stores/companies'
import { useToastStore, extractErrorMessage } from 'shell/toastStore'
import type { Company, CompanyPayload } from '../services/companies'
import CompanyTable from '../components/companies/CompanyTable.vue'
import CompanyDrawer from '../components/companies/CompanyDrawer.vue'
import StitchButton from 'shell/StitchButton'

const companiesStore = useCompaniesStore()
const toast = useToastStore()

const showDrawer = ref(false)
const selectedCompany = ref<Company | null>(null)

const recentChanges = computed(() =>
  [...companiesStore.companies]
    .sort((a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime())
    .slice(0, 3)
)

const formatRelative = (iso: string) => {
  const diffMs = Date.now() - new Date(iso).getTime()
  const mins = Math.floor(diffMs / 60000)
  if (mins < 60) return `${Math.max(mins, 1)} min ago`
  const hours = Math.floor(mins / 60)
  if (hours < 24) return `${hours}h ago`
  const days = Math.floor(hours / 24)
  return `${days}d ago`
}

onMounted(() => {
  companiesStore.fetchCompanies()
})

const openCreateDrawer = () => {
  selectedCompany.value = null
  companiesStore.error = null
  showDrawer.value = true
}

const openEditDrawer = (company: Company) => {
  selectedCompany.value = company
  companiesStore.error = null
  showDrawer.value = true
}

const handleSave = async (payload: CompanyPayload) => {
  try {
    if (selectedCompany.value) {
      const { id, tenant_id, ...updatePayload } = payload
      await companiesStore.updateCompany(selectedCompany.value.id, updatePayload)
      toast.success('Company updated successfully')
    } else {
      await companiesStore.createCompany(payload)
      toast.success('Company created successfully')
    }
    showDrawer.value = false
  } catch (err: any) {
    toast.error(extractErrorMessage(err))
  }
}
</script>

<template>
  <div class="flex flex-col gap-lg">
    <!-- Page Header -->
    <div class="flex flex-col md:flex-row md:items-end justify-between gap-md">
      <div class="max-w-3xl">
        <h1 class="text-headline-lg font-semibold text-on-surface leading-tight tracking-tight">Company Management</h1>
        <p class="text-body-md text-on-surface-variant mt-1">Manage the catalog of companies that company-scoped flags can target.</p>
      </div>
      <div class="flex items-center gap-md">
        <StitchButton icon="add" @click="openCreateDrawer">
          New Company
        </StitchButton>
      </div>
    </div>

    <!-- Main Grid: table (9) + insights sidebar (3) per Stitch design -->
    <div class="grid grid-cols-12 gap-lg">
      <!-- Table Area -->
      <div class="col-span-12 lg:col-span-9">
        <div class="bg-surface-container-lowest rounded-xl border border-outline-variant overflow-hidden shadow-sm">
          <CompanyTable
            :companies="companiesStore.companies"
            :loading="companiesStore.isLoading"
            @edit="openEditDrawer"
          />
        </div>
      </div>

      <!-- Insights Sidebar -->
      <aside class="col-span-12 lg:col-span-3 flex flex-col gap-lg">
        <!-- Recent Changes (derived from real updated_at) -->
        <div class="bg-surface-container-lowest border border-outline-variant rounded-xl p-lg shadow-sm">
          <h3 class="text-label-md font-bold text-on-surface mb-lg">Recent Changes</h3>
          <div v-if="recentChanges.length" class="flex flex-col gap-md">
            <div v-for="(company, i) in recentChanges" :key="company.id" class="flex gap-md">
              <div class="relative">
                <div class="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center text-primary">
                  <span class="material-symbols-outlined text-sm">edit</span>
                </div>
                <div v-if="i < recentChanges.length - 1" class="absolute top-8 left-1/2 -translate-x-1/2 w-0.5 h-full bg-outline-variant/30"></div>
              </div>
              <div class="flex flex-col pb-4">
                <p class="text-xs text-on-surface font-bold">{{ company.name }} updated</p>
                <p class="text-[10px] text-secondary">{{ formatRelative(company.updated_at) }}</p>
              </div>
            </div>
          </div>
          <p v-else class="text-xs text-on-surface-variant">No catalog activity yet.</p>
        </div>

        <!-- Promo Card (Stitch decorative) -->
        <div class="bg-primary-container rounded-xl p-lg text-on-primary-container shadow-lg relative overflow-hidden group">
          <div class="absolute -right-4 -bottom-4 opacity-10 rotate-12 transition-transform group-hover:scale-110 duration-500">
            <span class="material-symbols-outlined text-[120px]" style="font-variation-settings: 'FILL' 1">apartment</span>
          </div>
          <h4 class="text-label-md font-bold mb-2">Scope Targeting</h4>
          <p class="text-xs opacity-80 mb-lg leading-relaxed">Companies registered here become available as targets for company-scoped feature flags.</p>
        </div>
      </aside>
    </div>

    <!-- Create/Edit Drawer -->
    <CompanyDrawer
      :show="showDrawer"
      :company="selectedCompany"
      :error="companiesStore.error"
      @close="showDrawer = false"
      @save="handleSave"
    />
  </div>
</template>
