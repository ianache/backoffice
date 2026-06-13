import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as auditService from '../services/audit'
import type { AuditLogEntry, AuditLogFilters, AuditLogDiff } from '../services/audit'

export const useAuditStore = defineStore('audit', () => {
  const items = ref<AuditLogEntry[]>([])
  const total = ref(0)
  const page = ref(1)
  const limit = ref(25)
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  const diff = ref<AuditLogDiff | null>(null)
  const isLoadingDiff = ref(false)
  const diffError = ref<string | null>(null)

  async function fetchAuditLogs(filters: AuditLogFilters = {}) {
    isLoading.value = true
    try {
      const result = await auditService.listAuditLogs({ ...filters, page: filters.page ?? page.value, limit: filters.limit ?? limit.value })
      items.value = result.items
      total.value = result.total
      page.value = result.page
      limit.value = result.limit
      error.value = null
    } catch (err: any) {
      error.value = err.response?.data?.detail || err.message
    } finally {
      isLoading.value = false
    }
  }

  async function fetchDiff(id: number) {
    isLoadingDiff.value = true
    diff.value = null
    try {
      diff.value = await auditService.getAuditLogDiff(id)
      diffError.value = null
    } catch (err: any) {
      diffError.value = err.response?.data?.detail || err.message
    } finally {
      isLoadingDiff.value = false
    }
  }

  return { items, total, page, limit, isLoading, error, diff, isLoadingDiff, diffError, fetchAuditLogs, fetchDiff }
})
