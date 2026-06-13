<template>
  <div class="fixed inset-0 z-[60] flex items-center justify-center">
    <div class="absolute inset-0 bg-on-background/50 backdrop-blur-sm" @click="close"></div>
    <div class="relative bg-white dark:bg-slate-900 w-[520px] rounded-xl shadow-2xl p-lg flex flex-col gap-md border border-outline-variant dark:border-slate-800 text-on-surface dark:text-slate-200">
      <div class="flex items-center justify-between border-b border-outline-variant dark:border-slate-800 pb-sm">
        <h3 class="font-headline-md">Exportar Namespace</h3>
        <button @click="close" class="p-1 hover:bg-surface-container-high dark:hover:bg-slate-800 rounded-full">
          <span class="material-symbols-outlined">close</span>
        </button>
      </div>

      <div class="space-y-md py-md">
        <p class="text-xs text-on-surface-variant dark:text-slate-400">
          Descarga las claves y traducciones del namespace
          <strong class="text-on-surface dark:text-slate-200">{{ state.activeNamespace ?? '—' }}</strong>
          para el contexto activo (tenant {{ state.workspaceContext.tenantId || '—' }}).
        </p>
        <div class="grid grid-cols-2 gap-sm">
          <button
            :disabled="exporting || !canExport"
            @click="onExport('json')"
            class="p-md border border-outline-variant dark:border-slate-700 rounded-lg hover:border-primary flex flex-col items-center gap-xs bg-surface-container-low dark:bg-slate-800 transition-colors disabled:opacity-50"
          >
            <span class="material-symbols-outlined text-primary text-3xl">data_object</span>
            <span class="font-bold text-sm">Formato JSON</span>
            <span class="text-[10px] text-on-surface-variant dark:text-slate-400">Ideal para bootstrapping en SDK</span>
          </button>
          <button
            :disabled="exporting || !canExport"
            @click="onExport('csv')"
            class="p-md border border-outline-variant dark:border-slate-700 rounded-lg hover:border-primary flex flex-col items-center gap-xs bg-surface-container-low dark:bg-slate-800 transition-colors disabled:opacity-50"
          >
            <span class="material-symbols-outlined text-green-600 text-3xl">table_chart</span>
            <span class="font-bold text-sm">Formato CSV</span>
            <span class="text-[10px] text-on-surface-variant dark:text-slate-400">Ideal para agencias de traducción</span>
          </button>
        </div>
      </div>

      <div class="flex justify-end gap-md pt-sm border-t border-outline-variant dark:border-slate-800">
        <button
          @click="close"
          class="px-md py-sm border border-outline dark:border-slate-700 rounded-lg text-sm hover:bg-surface-container-high dark:hover:bg-slate-800 transition-colors"
        >
          Cerrar
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useToastStore, extractErrorMessage } from 'shell/toastStore'
import { exportNamespace } from '../../services/labels'
import { useLabelingState } from '../../composables/useLabelingState'

const state = useLabelingState()
const toast = useToastStore()
const exporting = ref(false)

const canExport = computed(() => !!state.activeNamespace && !!state.workspaceContext.tenantId)

function close() {
  state.showImportExport = false
}

async function onExport(format: 'json' | 'csv') {
  if (!state.activeNamespace || !state.workspaceContext.tenantId) return

  exporting.value = true
  try {
    const responseBlob = await exportNamespace(format, {
      tenant_id: state.workspaceContext.tenantId,
      company_id: state.workspaceContext.companyId ?? undefined,
      product_id: state.workspaceContext.productId ?? undefined,
      namespace: state.activeNamespace,
    })
    const mimeType = format === 'csv' ? 'text/csv' : 'application/json'
    const blob = responseBlob.type ? responseBlob : new Blob([responseBlob], { type: mimeType })

    const filename = `${state.activeNamespace}_${state.workspaceContext.tenantId}.${format}`
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = filename
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)

    toast.success(`Export ${format.toUpperCase()} descargado: ${filename}`)
  } catch (err: any) {
    toast.error(extractErrorMessage(err))
  } finally {
    exporting.value = false
  }
}
</script>
