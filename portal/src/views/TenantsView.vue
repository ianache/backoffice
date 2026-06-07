<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useTenantsStore } from '../stores/tenants'
import type { Tenant, TenantPayload } from '../services/tenants'
import TenantTable from '../components/tenants/TenantTable.vue'
import TenantDrawer from '../components/tenants/TenantDrawer.vue'
import ConfirmDialog from '../components/tenants/ConfirmDialog.vue'

const tenantsStore = useTenantsStore()

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

onMounted(() => {
  tenantsStore.fetchTenants()
})

const handleSearch = (q: string) => {
  tenantsStore.fetchTenants({ q })
}

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
    } else {
      await tenantsStore.createTenant(payload)
    }
    showDrawer.value = false
  } catch (err: any) {
    alert(`Error: ${err.message}`)
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
    } catch (err: any) {
      alert(`Error: ${err.message}`)
    }
  }
}
</script>

<template>
  <div class="tenants-view">
    <div class="page-header">
      <div>
        <h1>Tenant Management</h1>
        <p class="subtitle">Manage platform tenants, whitelabeling, and product access.</p>
      </div>
      <button class="btn btn-primary" @click="openCreateDrawer">
        Create Tenant
      </button>
    </div>

    <TenantTable 
      :tenants="tenantsStore.tenants" 
      :is-loading="tenantsStore.isLoading"
      @edit="openEditDrawer"
      @suspend="confirmSuspend"
      @delete="confirmDelete"
      @search="handleSearch"
    />

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
.tenants-view {
  padding: 2rem;
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 2rem;
}

.page-header h1 {
  margin: 0;
  font-size: 1.875rem;
  font-weight: 700;
  color: #111827;
}

.subtitle {
  margin: 0.25rem 0 0 0;
  color: #6b7280;
}

.btn {
  padding: 0.625rem 1.25rem;
  border-radius: 6px;
  font-weight: 500;
  cursor: pointer;
  border: 1px solid transparent;
}

.btn-primary {
  background: #2563eb;
  color: white;
}

.btn-primary:hover {
  background: #1d4ed8;
}
</style>
