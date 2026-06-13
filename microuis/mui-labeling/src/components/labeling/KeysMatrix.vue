<template>
  <section class="col-span-6 flex flex-col overflow-hidden bg-background">
    <!-- Info del Namespace Seleccionado -->
    <div class="p-md border-b border-outline-variant bg-surface-container-lowest flex items-center justify-between">
      <div>
        <div class="flex items-center gap-sm">
          <h2 id="activeNamespaceTitle" class="font-headline-md text-on-surface">
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
        <p id="activeNamespaceDesc" class="text-xs text-on-surface-variant mt-1">
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
    <div class="px-md py-sm bg-surface-container-low border-b border-outline-variant flex items-center justify-between gap-sm">
      <div class="flex gap-xs" id="tableFilters">
        <button
          v-for="f in filters"
          :key="f.value"
          @click="activeFilter = f.value"
          :class="[
            'px-sm py-1 rounded font-title-md text-xs transition-colors',
            activeFilter === f.value
              ? 'bg-surface border border-outline-variant text-primary shadow-sm'
              : 'bg-transparent text-on-surface-variant hover:text-on-surface',
          ]"
          :data-filter="f.value"
        >
          {{ f.label }}
        </button>
      </div>
      <span id="keysCount" class="text-xs text-on-surface-variant">Total: {{ filteredKeys.length }} claves</span>
    </div>

    <!-- Table Matrix container -->
    <div class="flex-1 overflow-auto custom-scrollbar">
      <table class="w-full text-left border-collapse">
        <thead>
          <tr class="text-on-surface-variant font-label-md uppercase tracking-wider border-b border-outline-variant bg-surface-container-low/50 text-[11px]">
            <th class="px-md py-3 w-1/3">Clave Técnica (`label_key`)</th>
            <th class="px-md py-3">es_PE</th>
            <th class="px-md py-3">en_US</th>
            <th class="px-md py-3 text-right">Estado</th>
          </tr>
        </thead>
        <tbody id="keysTableBody" class="divide-y divide-outline-variant">
          <tr v-if="filteredKeys.length === 0">
            <td colspan="4" class="p-lg text-center text-on-surface-variant italic">
              No se encontraron claves para el filtro/búsqueda activo.
            </td>
          </tr>
          <tr
            v-for="row in filteredKeys"
            :key="row.label_key"
            @click="selectKey(row)"
            :class="[
              'cursor-pointer transition-colors border-b border-outline-variant',
              state.selectedKey?.label_key === row.label_key
                ? 'bg-primary-container/10'
                : 'hover:bg-surface-container-low',
            ]"
          >
            <td class="px-md py-3 font-mono font-bold text-sm text-on-surface">
              <div class="flex items-center gap-xs">
                {{ row.label_key }}
                <span
                  v-if="row.label_type"
                  class="px-1.5 py-0.2 bg-amber-100 text-amber-800 rounded text-[9px] font-bold"
                  :title="row.label_type"
                >
                  {{ row.label_type }}
                </span>
              </div>
            </td>
            <td class="px-md py-3 text-xs text-on-surface-variant truncate max-w-[150px]" :title="row.es_PE">
              <span v-if="row.es_PE">{{ row.es_PE }}</span>
              <span v-else class="text-red-500 font-bold italic">Missing</span>
            </td>
            <td class="px-md py-3 text-xs text-on-surface-variant truncate max-w-[150px]" :title="row.en_US">
              <span v-if="row.en_US">{{ row.en_US }}</span>
              <span v-else class="text-red-500 font-bold italic">Missing</span>
            </td>
            <td class="px-md py-3 text-right">
              <span class="px-2 py-0.5 bg-slate-100 text-slate-600 rounded-full text-[9px] font-bold uppercase">
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

watch([() => state.activeNamespace, () => state.workspaceContext], fetchKeys, { deep: true })

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
  // TODO: 20-08 — wire to the Add Key modal (RF-06/RF-07).
  console.warn('TODO: 20-08 — Add Key modal not yet implemented')
}
</script>
