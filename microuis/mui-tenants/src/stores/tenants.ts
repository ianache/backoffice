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

  // Subscriptions are separate resources (POST/DELETE /tenants/{id}/products/{pid});
  // the backend ignores a products array inside tenant create/update payloads.
  async function syncProductSubscriptions(tenantId: number, current: string[], desired: string[]) {
    const toAdd = desired.filter(p => !current.includes(p))
    const toRemove = current.filter(p => !desired.includes(p))
    await Promise.all([
      ...toAdd.map(p => tenantsService.subscribeProduct(tenantId, p)),
      ...toRemove.map(p => tenantsService.unsubscribeProduct(tenantId, p)),
    ])
  }

  async function createTenant(payload: TenantPayload) {
    const { products = [], ...rest } = payload
    const created = await tenantsService.create({ ...rest, products: [] })
    if (products.length) {
      await syncProductSubscriptions(created.id, [], products)
      created.products = [...products]
    }
    tenants.value.unshift(created)
    return created
  }

  async function updateTenant(id: number, payload: Partial<TenantPayload>) {
    const { products, ...rest } = payload
    if (products) {
      const current = tenants.value.find(t => t.id === id)?.products ?? []
      await syncProductSubscriptions(id, current, products)
    }
    // PATCH after the sync so the response carries the fresh subscription set
    const updated = await tenantsService.update(id, rest)
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
