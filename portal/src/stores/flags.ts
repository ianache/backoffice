import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as flagsService from '../services/flags'
import type { FeatureFlag, Segment, FlagPayload, SegmentPayload, FlagFilters } from '../services/flags'

export const useFeatureFlagsStore = defineStore('featureFlags', () => {
  const flags = ref<FeatureFlag[]>([])
  const segments = ref<Segment[]>([])
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  async function fetchFlags(filters?: FlagFilters) {
    isLoading.value = true
    error.value = null
    try {
      flags.value = await flagsService.list(filters)
    } catch (err: any) {
      error.value = err.message
    } finally {
      isLoading.value = false
    }
  }

  async function createFlag(payload: FlagPayload): Promise<FeatureFlag> {
    const created = await flagsService.create(payload)
    flags.value.unshift(created)
    return created
  }

  async function updateFlag(id: number, payload: Partial<FlagPayload>): Promise<FeatureFlag> {
    const updated = await flagsService.update(id, payload)
    const index = flags.value.findIndex(f => f.id === id)
    if (index !== -1) flags.value[index] = updated
    return updated
  }

  async function toggleFlag(id: number, enabled: boolean): Promise<void> {
    await flagsService.setEnabled(id, enabled)
    const flag = flags.value.find(f => f.id === id)
    if (flag) flag.enabled = enabled
  }

  async function deleteFlag(id: number): Promise<void> {
    await flagsService.remove(id)
    flags.value = flags.value.filter(f => f.id !== id)
  }

  async function fetchSegments(tenantId?: string) {
    try {
      segments.value = await flagsService.listSegments(tenantId)
    } catch (err: any) {
      error.value = err.message
    }
  }

  async function createSegment(payload: SegmentPayload): Promise<Segment> {
    const created = await flagsService.createSegment(payload)
    segments.value.unshift(created)
    return created
  }

  return {
    flags,
    segments,
    isLoading,
    error,
    fetchFlags,
    createFlag,
    updateFlag,
    toggleFlag,
    deleteFlag,
    fetchSegments,
    createSegment,
  }
})
