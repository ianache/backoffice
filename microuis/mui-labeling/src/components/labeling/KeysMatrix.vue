<template>
  <section class="col-span-6 flex flex-col overflow-hidden bg-background dark:bg-slate-950">
    <!-- Info del Namespace Seleccionado -->
    <div class="p-md border-b border-outline-variant dark:border-slate-800 bg-surface-container-lowest dark:bg-slate-900/40 flex items-center justify-between">
      <div>
        <div class="flex items-center gap-sm">
          <h2 id="activeNamespaceTitle" class="font-headline-md text-on-surface dark:text-slate-200">
            {{ activeNamespaceMeta?.id ?? state.activeNamespace ?? '—' }}
          </h2>
          <span
            v-if="activeNamespaceMeta"
            id="activeNamespaceBadge"
            class="px-2 py-0.5 bg-primary/10 text-primary border border-primary/20 rounded-full font-label-md text-[10px]"
          >
            {{ activeNamespaceMeta.strategy === 'eager' ? 'CRITICAL / EAGER' : 'LAZY LOADING' }}
          </span>
        </div>
        <p id="activeNamespaceDesc" class="text-xs text-on-surface-variant dark:text-slate-400 mt-1">
          {{ activeNamespaceMeta?.description ?? '' }}
        </p>
      </div>
      <button
        @click="onAddKeyClick"
        class="flex items-center gap-xs bg-primary text-on-primary px-md py-1.5 rounded-lg font-title-md text-sm hover:shadow-lg transition-all active:scale-[0.98]"
      >
        <span class="material-symbols-outlined text-sm">add_circle</span>
        <span>Agregar Clave</span>
      </button>
    </div>

    <!-- Filters & Search Interna -->
    <div class="px-md py-sm bg-surface-container-low dark:bg-slate-900/80 border-b border-outline-variant dark:border-slate-800 flex items-center justify-between gap-sm">
      <div class="flex gap-xs" id="tableFilters">
        <button
          v-for="f in filters"
          :key="f.value"
          @click="activeFilter = f.value"
          :class="[
            'px-sm py-1 rounded font-title-md text-xs transition-colors',
            activeFilter === f.value
              ? 'bg-surface dark:bg-slate-800 border border-outline-variant dark:border-slate-700 text-primary dark:text-primary-fixed-dim shadow-sm'
              : 'bg-transparent text-on-surface-variant dark:text-slate-400 hover:text-on-surface dark:hover:text-slate-200',
          ]"
          :data-filter="f.value"
        >
          {{ f.label }}
        </button>
      </div>
      <span id="keysCount" class="text-xs text-on-surface-variant dark:text-slate-400">Total: {{ filteredKeys.length }} claves</span>
    </div>

    <!-- Table Matrix container -->
    <div class="flex-1 overflow-auto custom-scrollbar">
      <table class="w-full text-left border-collapse">
        <thead>
          <tr class="text-on-surface-variant dark:text-slate-400 font-label-md uppercase tracking-wider border-b border-outline-variant dark:border-slate-800 bg-surface-container-low/50 dark:bg-slate-900/30 text-[11px]">
            <th class="px-md py-3 w-1/3">Clave Técnica (`label_key`)</th>
            <th class="px-md py-3">es_PE</th>
            <th class="px-md py-3">en_US</th>
            <th class="px-md py-3 text-right">Estado</th>
          </tr>
        </thead>
        <tbody id="keysTableBody" class="divide-y divide-outline-variant dark:divide-slate-800">
          <tr v-if="filteredKeys.length === 0">
            <td colspan="4" class="p-lg text-center text-on-surface-variant dark:text-slate-400 italic">
              No se encontraron claves para el filtro/búsqueda activo.
            </td>
          </tr>
          <tr
            v-for="row in filteredKeys"
            :key="row.label_key"
            @click="selectKey(row)"
            :class="[
              'cursor-pointer transition-colors border-b border-outline-variant dark:border-slate-800',
              state.selectedKey?.label_key === row.label_key
                ? 'bg-primary-container/10 dark:bg-slate-900'
                : 'hover:bg-surface-container-low dark:hover:bg-slate-900/40',
            ]"
          >
            <td class="px-md py-3 font-mono font-bold text-sm text-on-surface dark:text-slate-200">
              <div class="flex items-center gap-xs">
                {{ row.label_key }}
                <span
                  v-if="row.label_type"
                  class="px-1.5 py-0.2 bg-amber-100 text-amber-800 dark:bg-amber-950/20 dark:text-amber-400 rounded text-[9px] font-bold"
                  :title="row.label_type"
                >
                  {{ row.label_type }}
                </span>
              </div>
            </td>
            <td class="px-md py-3 text-xs text-on-surface-variant dark:text-slate-400 truncate max-w-[150px]" :title="row.es_PE">
              <span v-if="row.es_PE">{{ row.es_PE }}</span>
              <span v-else class="text-red-500 dark:text-red-400 font-bold italic">Missing</span>
            </td>
            <td class="px-md py-3 text-xs text-on-surface-variant dark:text-slate-400 truncate max-w-[150px]" :title="row.en_US">
              <span v-if="row.en_US">{{ row.en_US }}</span>
              <span v-else class="text-red-500 dark:text-red-400 font-bold italic">Missing</span>
            </td>
            <td class="px-md py-3 text-right">
              <span class="px-2 py-0.5 bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400 rounded-full text-[9px] font-bold uppercase">
                {{ row.params.length > 0 ? row.params.join(', ') : '—' }}
              </span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { useToastStore, extractErrorMessage } from 'shell/toastStore'
import { listNamespaces, listKeys, type Namespace, type LocalizedLabel } from '../../services/labels'
import { useLabelingState } from '../../composables/useLabelingState'

const state = useLabelingState()
const toast = useToastStore()

const keys = ref<LocalizedLabel[]>([])
const namespacesCache = ref<Namespace[]>([])
const activeFilter = ref<'all' | 'overridden' | 'missing'>('all')

const filters = [
  { value: 'all' as const, label: 'Todas' },
  { value: 'overridden' as const, label: 'Sobrescritas' },
  { value: 'missing' as const, label: 'Falta traducción' },
]

const activeNamespaceMeta = computed(() =>
  namespacesCache.value.find((ns) => ns.id === state.activeNamespace) ?? null
)

// Group raw LocalizedLabel rows (one per locale) into one row per label_key
// with es_PE/en_US columns, matching the prototype's #keysTableBody layout.
interface KeyRow {
  label_key: string
  label_type: string | null
  params: string[]
  es_PE: string
  en_US: string
  hasOverride: boolean
}

const groupedKeys = computed<KeyRow[]>(() => {
  const byKey = new Map<string, KeyRow>()
  for (const k of keys.value) {
    let row = byKey.get(k.label_key)
    if (!row) {
      row = {
        label_key: k.label_key,
        label_type: k.label_type,
        params: k.params ?? [],
        es_PE: '',
        en_US: '',
        hasOverride: false,
      }
      byKey.set(k.label_key, row)
    }
    if (k.locale === 'es_PE') row.es_PE = k.label_value
    if (k.locale === 'en_US') row.en_US = k.label_value
    if (k.company_id || k.product_id) row.hasOverride = true
  }
  return Array.from(byKey.values())
})

const filteredKeys = computed<KeyRow[]>(() => {
  const search = state.searchQuery.trim().toLowerCase()
  return groupedKeys.value.filter((row) => {
    if (search) {
      const matches =
        row.label_key.toLowerCase().includes(search) ||
        row.es_PE.toLowerCase().includes(search) ||
        row.en_US.toLowerCase().includes(search)
      if (!matches) return false
    }

    if (activeFilter.value === 'overridden') return row.hasOverride
    if (activeFilter.value === 'missing') return row.es_PE === '' || row.en_US === ''
    return true
  })
})

onMounted(async () => {
  await fetchNamespacesCache()
  await fetchKeys()
})

watch([() => state.activeNamespace, () => state.workspaceContext, () => state.refreshTrigger], fetchKeys, { deep: true })

async function fetchNamespacesCache() {
  try {
    namespacesCache.value = await listNamespaces()
  } catch {
    namespacesCache.value = []
  }
}

async function fetchKeys() {
  if (!state.activeNamespace || !state.workspaceContext.tenantId) {
    keys.value = []
    return
  }
  try {
    keys.value = await listKeys({
      tenant_id: state.workspaceContext.tenantId,
      company_id: state.workspaceContext.companyId ?? undefined,
      product_id: state.workspaceContext.productId ?? undefined,
      namespace: state.activeNamespace,
    })
  } catch (err: any) {
    toast.error(extractErrorMessage(err))
  }
}

function selectKey(row: KeyRow) {
  const match = keys.value.find((k) => k.label_key === row.label_key) ?? null
  state.selectedKey = match
}

function onAddKeyClick() {
  state.showAddKeyModal = true
}
</script>
