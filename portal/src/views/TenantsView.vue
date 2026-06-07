<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useTenantsStore } from '../stores/tenants'
import type { Tenant, TenantPayload } from '../services/tenants'
import TenantTable from '../components/tenants/TenantTable.vue'
import TenantDrawer from '../components/tenants/TenantDrawer.vue'
import ConfirmDialog from '../components/tenants/ConfirmDialog.vue'
import StitchButton from '../components/ui/StitchButton.vue'

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
  <div class="flex flex-col gap-6">
    <!-- Action Bar -->
    <div class="flex items-center justify-between">
      <div>
        <p class="text-on-surface-variant text-sm">
          Manage platform tenants, whitelabeling, and product access.
        </p>
      </div>
      <StitchButton @click="openCreateDrawer">
        <template #icon>
          <md-icon>add</md-icon>
        </template>
        Create Tenant
      </StitchButton>
    </div>

    <!-- Table Section -->
    <div class="bg-surface-container-lowest rounded-xl border border-outline-variant overflow-hidden">
      <TenantTable 
        :tenants="tenantsStore.tenants" 
        :is-loading="tenantsStore.isLoading"
        @edit="openEditDrawer"
        @suspend="confirmSuspend"
        @delete="confirmDelete"
        @search="handleSearch"
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
/* Scoped styles mostly removed in favor of Tailwind and Stitch components */
</style>
