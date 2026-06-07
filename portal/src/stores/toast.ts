import { defineStore } from 'pinia'
import { ref } from 'vue'

export type ToastType = 'success' | 'error'

export interface Toast {
  id: number
  type: ToastType
  message: string
}

let _nextId = 1

export const useToastStore = defineStore('toast', () => {
  const toasts = ref<Toast[]>([])

  function add(type: ToastType, message: string, durationMs = 4000) {
    const id = _nextId++
    toasts.value.push({ id, type, message })
    setTimeout(() => remove(id), durationMs)
  }

  function remove(id: number) {
    toasts.value = toasts.value.filter(t => t.id !== id)
  }

  const success = (message: string) => add('success', message)
  const error = (message: string) => add('error', message)

  return { toasts, success, error, remove }
})

// Extract a human-readable message from an axios or fetch error
export function extractErrorMessage(err: unknown, fallback = 'An unexpected error occurred'): string {
  if (!err || typeof err !== 'object') return fallback
  const e = err as any
  return e.response?.data?.detail ?? e.message ?? fallback
}
