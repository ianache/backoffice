import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as tenantsService from '../services/tenants'
import type { Tenant, TenantPayload, TenantFilters } from '../services/tenants'

export const useTenantsStore = defineStore('tenants', () => {
  const tenants = ref<Tenant[]>([])
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  async function fetchTenants(filters?: TenantFilters) {
    isLoading.value = true
    try {
      tenants.value = await tenantsService.list(filters)
    } catch (err: any) {
      error.value = err.message
    } finally {
      isLoading.value = false
    }
  }

  async function createTenant(payload: TenantPayload) {
    const created = await tenantsService.create(payload)
    tenants.value.unshift(created)
    return created
  }

  async function updateTenant(id: number, payload: Partial<TenantPayload>) {
    const updated = await tenantsService.update(id, payload)
    const index = tenants.value.findIndex(t => t.id === id)
    if (index !== -1) {
      tenants.value[index] = updated
    }
    return updated
  }

  async function deleteTenant(id: number) {
    await tenantsService.remove(id)
    tenants.value = tenants.value.filter(t => t.id !== id)
  }

  return { tenants, isLoading, error, fetchTenants, createTenant, updateTenant, deleteTenant }
})
