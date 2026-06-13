<template>
  <div class="fixed inset-0 z-[60] flex items-center justify-center">
    <div class="absolute inset-0 bg-on-background/50 backdrop-blur-sm" @click="close"></div>
    <div class="relative bg-white dark:bg-slate-900 w-[600px] rounded-xl shadow-2xl p-lg flex flex-col gap-md border border-outline-variant dark:border-slate-800 text-on-surface dark:text-slate-200">
      <div class="flex items-center justify-between border-b border-outline-variant dark:border-slate-800 pb-sm">
        <div class="flex items-center gap-sm">
          <span class="material-symbols-outlined text-error">warning</span>
          <h3 class="font-headline-md">Missing Keys Diagnostic Panel</h3>
        </div>
        <button @click="close" class="p-1 hover:bg-surface-container-high dark:hover:bg-slate-800 rounded-full">
          <span class="material-symbols-outlined">close</span>
        </button>
      </div>
      <p class="text-xs text-on-surface-variant dark:text-slate-400">
        Estas claves técnicas han sido solicitadas por los SDKs clientes en producción o staging, pero no existen
        traducciones registradas en el namespace correspondiente de la base de datos.
      </p>

      <div class="overflow-x-auto border border-outline-variant dark:border-slate-800 rounded-lg max-h-64 custom-scrollbar">
        <table class="w-full text-left text-xs">
          <thead>
            <tr class="bg-surface-container-low dark:bg-slate-800 text-on-surface-variant dark:text-slate-400 uppercase tracking-wider font-bold">
              <th class="p-sm">Namespace</th>
              <th class="p-sm">Clave Faltante</th>
              <th class="p-sm">Locale</th>
              <th class="p-sm">Hits</th>
              <th class="p-sm">Último Reporte</th>
              <th class="p-sm text-right">Acción</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-outline-variant dark:divide-slate-800">
            <tr v-if="loading">
              <td colspan="6" class="p-md text-center text-on-surface-variant dark:text-slate-400 italic">Cargando...</td>
            </tr>
            <tr v-else-if="reports.length === 0">
              <td colspan="6" class="p-md text-center text-on-surface-variant dark:text-slate-400 italic">
                No missing labels reported
              </td>
            </tr>
            <tr v-for="row in reports" :key="row.id" class="hover:bg-slate-50 dark:hover:bg-slate-800/40">
              <td class="p-sm font-mono">{{ row.namespace }}</td>
              <td class="p-sm font-mono font-bold text-red-600 dark:text-red-400">{{ row.label_key }}</td>
              <td class="p-sm font-mono">{{ row.locale }}</td>
              <td class="p-sm">{{ row.hits }}</td>
              <td class="p-sm">{{ formatDate(row.last_reported_at) }}</td>
              <td class="p-sm text-right">
                <button
                  @click="quickCreateMissing(row)"
                  class="px-sm py-0.5 bg-primary text-on-primary rounded font-bold text-[10px]"
                >
                  CREAR
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="flex justify-end pt-sm border-t border-outline-variant dark:border-slate-800">
        <button
          @click="close"
          class="px-md py-sm bg-primary text-on-primary hover:bg-primary-container rounded-lg text-sm transition-colors"
        >
          Listo
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useToastStore, extractErrorMessage } from 'shell/toastStore'
import { listMissingLabels, type MissingLabelReport } from '../../services/labels'
import { useLabelingState } from '../../composables/useLabelingState'

const state = useLabelingState()
const toast = useToastStore()

const reports = ref<MissingLabelReport[]>([])
const loading = ref(false)

onMounted(async () => {
  if (!state.workspaceContext.tenantId) return
  loading.value = true
  try {
    reports.value = await listMissingLabels(state.workspaceContext.tenantId)
  } catch (err: any) {
    toast.error(extractErrorMessage(err))
  } finally {
    loading.value = false
  }
})

function formatDate(value: string): string {
  try {
    return new Date(value).toLocaleString()
  } catch {
    return value
  }
}

function quickCreateMissing(row: MissingLabelReport) {
  state.quickCreatePrefill = { namespace: row.namespace, label_key: row.label_key }
  state.showAddKeyModal = true
  close()
}

function close() {
  state.showDiagnostics = false
}
</script>
