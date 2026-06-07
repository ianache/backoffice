<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useTenantsStore } from '../stores/tenants'
import { useToastStore, extractErrorMessage } from '../stores/toast'
import type { Tenant, TenantPayload } from '../services/tenants'
import TenantTable from '../components/tenants/TenantTable.vue'
import TenantDrawer from '../components/tenants/TenantDrawer.vue'
import ConfirmDialog from '../components/tenants/ConfirmDialog.vue'
import StitchButton from '../components/ui/StitchButton.vue'

const tenantsStore = useTenantsStore()
const toast = useToastStore()

const showDrawer = ref(false)
const selectedTenant = ref<Tenant | null>(null)

const confirmDialog = ref({
  show: false,
  title: '',
  message: '',
  confirmText: '',
  type: 'info' as 'info' | 'danger',
  action: null as (() => Promise<void>) | null
})

const activeCount = computed(() => tenantsStore.tenants.filter(t => t.status === 'active').length)
const uniqueProductCount = computed(() => new Set(tenantsStore.tenants.flatMap(t => t.products)).size)

onMounted(() => {
  tenantsStore.fetchTenants()
})

const openCreateDrawer = () => {
  selectedTenant.value = null
  showDrawer.value = true
}

const openEditDrawer = (tenant: Tenant) => {
  selectedTenant.value = tenant
  showDrawer.value = true
}

const handleSave = async (payload: TenantPayload) => {
  try {
    if (selectedTenant.value) {
      await tenantsStore.updateTenant(selectedTenant.value.id, payload)
      toast.success('Tenant updated successfully')
    } else {
      await tenantsStore.createTenant(payload)
      toast.success('Tenant created successfully')
    }
    showDrawer.value = false
  } catch (err: any) {
    toast.error(extractErrorMessage(err))
  }
}

const confirmSuspend = (tenant: Tenant) => {
  confirmDialog.value = {
    show: true,
    title: 'Suspend Tenant',
    message: `Are you sure you want to suspend "${tenant.name}"? They will lose access to all products.`,
    confirmText: 'Suspend',
    type: 'danger',
    action: async () => {
      await tenantsStore.updateTenant(tenant.id, { status: 'suspended' })
    }
  }
}

const confirmDelete = (tenant: Tenant) => {
  confirmDialog.value = {
    show: true,
    title: 'Delete Tenant',
    message: `Are you sure you want to delete "${tenant.name}"? This action cannot be undone.`,
    confirmText: 'Delete',
    type: 'danger',
    action: async () => {
      await tenantsStore.deleteTenant(tenant.id)
    }
  }
}

const handleConfirm = async () => {
  if (confirmDialog.value.action) {
    try {
      await confirmDialog.value.action()
      confirmDialog.value.show = false
      toast.success(`${confirmDialog.value.title} completed`)
    } catch (err: any) {
      confirmDialog.value.show = false
      toast.error(extractErrorMessage(err))
    }
  }
}
</script>

<template>
  <div class="flex flex-col gap-xl">
    <!-- Page Header -->
    <div class="flex flex-col md:flex-row md:items-center justify-between gap-md">
      <div>
        <h1 class="page-title">Tenant Management</h1>
        <p class="page-subtitle">Oversee and manage ecosystem-wide tenant configurations and health.</p>
      </div>
      <div class="flex items-center gap-md">
        <button class="flex items-center gap-sm px-md py-sm border border-outline rounded-lg text-on-surface hover:bg-surface-container-high transition-colors text-sm font-medium">
          <span class="material-symbols-outlined icon-sm">file_download</span>
          Export List
        </button>
        <StitchButton icon="add" @click="openCreateDrawer">
          Create New Tenant
        </StitchButton>
      </div>
    </div>

    <!-- Bento Summary Grid -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-lg">
      <!-- Active Tenants -->
      <div class="bg-surface-container-lowest border border-outline-variant rounded-xl p-lg flex flex-col justify-between relative overflow-hidden hover:shadow-sm transition-all stat-card">
        <div class="accent-bar bg-primary"></div>
        <div class="flex justify-between items-start mb-md">
          <div>
            <p class="stat-label">Active Tenants</p>
            <h3 class="stat-value">{{ activeCount.toLocaleString() }}</h3>
          </div>
          <div class="p-sm bg-surface-container-high rounded-lg">
            <span class="material-symbols-outlined text-primary">groups</span>
          </div>
        </div>
        <div class="flex items-center gap-sm">
          <span class="text-sm font-bold text-green-600 flex items-center gap-0.5">
            <span class="material-symbols-outlined icon-sm leading-none">trending_up</span>
            +12%
          </span>
          <p class="text-xs text-on-surface-variant">vs last month</p>
        </div>
      </div>

      <!-- Total Products -->
      <div class="bg-surface-container-lowest border border-outline-variant rounded-xl p-lg flex flex-col justify-between relative overflow-hidden hover:shadow-sm transition-all stat-card">
        <div class="accent-bar bg-tertiary"></div>
        <div class="flex justify-between items-start mb-md">
          <div>
            <p class="stat-label">Total Products</p>
            <h3 class="stat-value">{{ uniqueProductCount }}</h3>
          </div>
          <div class="p-sm bg-surface-container-high rounded-lg">
            <span class="material-symbols-outlined text-tertiary">shopping_bag</span>
          </div>
        </div>
        <div class="flex items-center gap-sm">
          <span class="text-sm font-bold text-on-surface">{{ tenantsStore.tenants.length }}</span>
          <p class="text-xs text-on-surface-variant">Tenants loaded</p>
        </div>
      </div>

      <!-- System Health -->
      <div class="bg-surface-container-lowest border border-outline-variant rounded-xl p-lg flex flex-col justify-between relative overflow-hidden hover:shadow-sm transition-all stat-card">
        <div class="accent-bar bg-primary"></div>
        <div class="flex justify-between items-start mb-md">
          <div>
            <p class="stat-label">System Health</p>
            <h3 class="stat-value">99.98%</h3>
          </div>
          <div class="p-sm bg-surface-container-high rounded-lg">
            <span class="material-symbols-outlined text-primary" style="font-variation-settings: 'FILL' 1">check_circle</span>
          </div>
        </div>
        <div class="w-full bg-surface-container-high h-1.5 rounded-full overflow-hidden">
          <div class="bg-primary h-full" style="width: 99.98%"></div>
        </div>
      </div>
    </div>

    <!-- Table Section -->
    <div class="bg-surface-container-lowest rounded-xl border border-outline-variant overflow-hidden shadow-sm">
      <TenantTable
        :tenants="tenantsStore.tenants"
        :is-loading="tenantsStore.isLoading"
        @edit="openEditDrawer"
        @suspend="confirmSuspend"
        @delete="confirmDelete"
      />
    </div>

    <TenantDrawer
      :show="showDrawer"
      :tenant="selectedTenant"
      @close="showDrawer = false"
      @save="handleSave"
    />

    <ConfirmDialog
      v-bind="confirmDialog"
      @confirm="handleConfirm"
      @cancel="confirmDialog.show = false"
    />
  </div>
</template>

<style scoped>
.page-title {
  font-size: 2rem;
  font-weight: 600;
  line-height: 2.5rem;
  letter-spacing: -0.01em;
  color: var(--on-surface);
  margin: 0 0 4px 0;
}

.page-subtitle {
  font-size: 1rem;
  font-weight: 400;
  color: var(--on-surface-variant);
  margin: 0;
}

.stat-card:hover {
  transform: translateY(-2px);
}

.accent-bar {
  position: absolute;
  top: 0;
  left: 0;
  width: 6px;
  height: 100%;
}

.stat-label {
  font-size: 0.75rem;
  font-weight: 700;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  color: var(--on-surface-variant);
  margin: 0 0 4px 0;
}

.stat-value {
  font-size: 2rem;
  font-weight: 600;
  line-height: 2.5rem;
  color: var(--on-surface);
  margin: 0;
}

.icon-sm {
  font-size: 20px;
}
</style>
