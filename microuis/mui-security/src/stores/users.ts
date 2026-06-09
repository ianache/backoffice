import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as usersService from '../services/users'
import type { KcUser, UserPayload, UserFilters } from '../services/users'

export const useUsersStore = defineStore('users', () => {
  const users = ref<KcUser[]>([])
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  async function fetchUsers(filters?: UserFilters) {
    isLoading.value = true
    error.value = null
    try {
      users.value = await usersService.list(filters)
    } catch (err: any) {
      error.value = err.message
    } finally {
      isLoading.value = false
    }
  }

  async function createUser(payload: UserPayload): Promise<KcUser> {
    const created = await usersService.create(payload)
    users.value.unshift(created)
    return created
  }

  async function updateUser(id: string, payload: Partial<UserPayload>): Promise<KcUser> {
    const updated = await usersService.update(id, payload)
    const index = users.value.findIndex(u => u.id === id)
    if (index !== -1) users.value[index] = updated
    return updated
  }

  async function toggleUserStatus(id: string, enabled: boolean): Promise<void> {
    await usersService.setEnabled(id, enabled)
    const user = users.value.find(u => u.id === id)
    if (user) user.enabled = enabled
  }

  async function resetMfa(id: string): Promise<void> {
    await usersService.resetMfa(id)
  }

  // Computed helpers
  const activeCount = () => users.value.filter(u => u.enabled).length
  const pendingCount = () => 0  // Phase 3: no invitation pending state; placeholder for future

  return {
    users,
    isLoading,
    error,
    fetchUsers,
    createUser,
    updateUser,
    toggleUserStatus,
    resetMfa,
    activeCount,
    pendingCount,
  }
})
