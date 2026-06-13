<template>
  <aside class="col-span-3 border-l border-outline-variant dark:border-slate-800 bg-surface-container-lowest dark:bg-slate-900 flex flex-col overflow-hidden">
    <div class="p-md border-b border-outline-variant dark:border-slate-800 flex items-center justify-between">
      <h3 class="font-title-lg text-on-surface dark:text-slate-200 flex items-center gap-xs">
        <span class="material-symbols-outlined text-primary">edit_note</span>
        <span>Traducción &amp; Cascadas</span>
      </h3>
    </div>

    <!-- Panel Body -->
    <div class="flex-1 overflow-y-auto custom-scrollbar p-md space-y-lg">
      <!-- Empty state -->
      <div
        v-if="!state.selectedKey"
        class="flex flex-col items-center justify-center h-full text-center p-md opacity-60"
      >
        <span class="material-symbols-outlined text-[48px] text-on-surface-variant dark:text-slate-400">toc</span>
        <p class="font-title-md mt-sm text-on-surface-variant dark:text-slate-400">
          Selecciona una clave de la matriz para editar y evaluar sus cascadas jerárquicas.
        </p>
      </div>

      <!-- Edit form -->
      <div v-else class="space-y-md">
        <!-- Technical Name & Tag -->
        <div>
          <div class="flex justify-between items-start">
            <span
              v-if="activeRow?.label_type"
              class="px-2 py-0.5 bg-slate-100 dark:bg-slate-800 border border-outline-variant dark:border-slate-700 text-on-surface-variant dark:text-slate-300 rounded font-label-md text-[10px] uppercase"
            >
              {{ activeRow.label_type }}
            </span>
          </div>
          <h4 class="font-headline-md text-primary dark:text-primary-fixed-dim mt-sm break-all font-bold font-mono">
            {{ state.selectedKey.label_key }}
          </h4>
          <p v-if="activeRow?.description" class="text-xs text-on-surface-variant dark:text-slate-400 mt-1">
            {{ activeRow.description }}
          </p>
        </div>

        <!-- Variables (opcional) -->
        <div
          v-if="(activeRow?.params?.length ?? 0) > 0"
          class="p-sm bg-primary-container/10 border-l-2 border-primary rounded text-xs dark:text-slate-300"
        >
          <span class="font-bold flex items-center gap-xs">
            <span class="material-symbols-outlined text-sm">settings_input_composite</span>
            Variables esperadas:
          </span>
          <code class="font-mono text-primary bg-white/60 dark:bg-slate-800 px-xs py-0.5 rounded mt-1 inline-block">
            {{ activeRow?.params?.join(', ') }}
          </code>
        </div>

        <!-- Inputs por Locale -->
        <div class="space-y-md border-t border-outline-variant dark:border-slate-800 pt-md">
          <h5 class="font-title-md text-on-surface dark:text-slate-200">Traducciones en Locales Activos:</h5>
          <!-- es_PE -->
          <div class="space-y-xs">
            <div class="flex justify-between items-center">
              <label class="font-label-md text-on-surface-variant dark:text-slate-400 uppercase tracking-wider text-[10px]">es_PE (Spanish - PE)</label>
              <span
                v-if="esInherited"
                class="text-[10px] text-green-600 dark:text-green-400 font-bold uppercase"
              >
                Heredado
              </span>
            </div>
            <textarea
              v-model="esValue"
              rows="2"
              class="w-full bg-surface dark:bg-slate-800 border border-outline-variant dark:border-slate-700 rounded-lg p-md font-body-md text-sm text-on-surface dark:text-slate-200 focus:ring-primary focus:border-primary focus:outline-none"
            ></textarea>
          </div>
          <!-- en_US -->
          <div class="space-y-xs">
            <div class="flex justify-between items-center">
              <label class="font-label-md text-on-surface-variant dark:text-slate-400 uppercase tracking-wider text-[10px]">en_US (English - US)</label>
              <span
                v-if="enInherited"
                class="text-[10px] text-green-600 dark:text-green-400 font-bold uppercase"
              >
                Heredado
              </span>
            </div>
            <textarea
              v-model="enValue"
              rows="2"
              class="w-full bg-surface dark:bg-slate-800 border border-outline-variant dark:border-slate-700 rounded-lg p-md font-body-md text-sm text-on-surface dark:text-slate-200 focus:ring-primary focus:border-primary focus:outline-none"
            ></textarea>
          </div>
        </div>

        <!-- Arbol de Resolucion / Cascada Jerarquica (RF-05) -->
        <div class="border-t border-outline-variant dark:border-slate-800 pt-md space-y-md">
          <div class="flex justify-between items-center">
            <h5 class="font-title-md text-on-surface dark:text-slate-200">Árbol de Resolución (Cascada)</h5>
            <span
              class="material-symbols-outlined text-on-surface-variant dark:text-slate-400 cursor-pointer"
              title="Resolución basada en la cercanía al Producto"
            >
              help_outline
            </span>
          </div>
          <div class="space-y-sm text-xs relative pl-md">
            <!-- Nivel 1: Tenant -->
            <div class="relative flex items-center justify-between py-1 bg-surface-container-low dark:bg-slate-800 rounded px-sm">
              <span class="font-bold dark:text-slate-200">Nivel 1: Tenant ({{ state.workspaceContext.tenantId || '—' }})</span>
              <span class="text-[11px] text-on-surface-variant dark:text-slate-400 truncate max-w-[120px]">
                {{ tenantLevelValue || '[Vacío]' }}
              </span>
            </div>
            <!-- Nivel 2: Company -->
            <div class="tree-line relative flex items-center justify-between py-1 bg-surface-container-low dark:bg-slate-800 rounded px-sm">
              <span class="font-bold flex items-center gap-xs dark:text-slate-200">
                <span>Nivel 2: Company</span>
                <span
                  :class="[
                    'text-[9px] rounded px-xs font-bold',
                    state.workspaceContext.companyId
                      ? 'bg-blue-100 text-blue-700 dark:bg-blue-950/30 dark:text-blue-400'
                      : 'bg-slate-100 text-slate-500 dark:bg-slate-700 dark:text-slate-300',
                  ]"
                >
                  {{ state.workspaceContext.companyId || 'No select' }}
                </span>
              </span>
              <span class="text-[11px] text-on-surface-variant dark:text-slate-400 italic truncate max-w-[150px]">
                {{ companyLevelDisplay }}
              </span>
            </div>
            <!-- Nivel 3: Product -->
            <div class="tree-line relative flex items-center justify-between py-1 bg-surface-container-low dark:bg-slate-800 rounded px-sm">
              <span class="font-bold flex items-center gap-xs dark:text-slate-200">
                <span>Nivel 3: Product</span>
                <span
                  :class="[
                    'text-[9px] rounded px-xs font-bold',
                    state.workspaceContext.productId
                      ? 'bg-green-100 text-green-700 dark:bg-green-950/30 dark:text-green-400'
                      : 'bg-slate-100 text-slate-500 dark:bg-slate-700 dark:text-slate-300',
                  ]"
                >
                  {{ state.workspaceContext.productId || 'No select' }}
                </span>
              </span>
              <span class="text-[11px] text-on-surface-variant dark:text-slate-400 italic truncate max-w-[150px]">
                {{ productLevelDisplay }}
              </span>
            </div>
          </div>
        </div>

        <!-- Botones de Accion -->
        <div class="border-t border-outline-variant dark:border-slate-800 pt-md flex flex-col gap-sm">
          <button
            :disabled="saving"
            @click="saveKeyChanges"
            class="w-full py-2 bg-primary hover:bg-primary-container text-on-primary font-title-md rounded-lg shadow transition-all flex items-center justify-center gap-xs disabled:opacity-50"
          >
            <span class="material-symbols-outlined text-sm">save</span>
            <span>Guardar Cambios</span>
          </button>
          <button
            :disabled="!canRestore || restoring"
            @click="restoreInheritedValue"
            :class="[
              'w-full py-2 border border-outline text-on-surface dark:text-slate-200 dark:border-slate-700 hover:bg-surface-container-high dark:hover:bg-slate-800 font-title-md rounded-lg transition-colors text-xs flex items-center justify-center gap-xs',
              !canRestore || restoring ? 'opacity-50 cursor-not-allowed' : '',
            ]"
          >
            <span class="material-symbols-outlined text-sm">undo</span>
            <span>Restaurar (Eliminar Override)</span>
          </button>
        </div>
      </div>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useToastStore, extractErrorMessage } from 'shell/toastStore'
import { useUserContext } from 'shell/useUserContext'
import {
  listKeys,
  createKey,
  updateKey,
  updateKeyValue,
  restoreOverride,
  type LocalizedLabel,
} from '../../services/labels'
import { useLabelingState } from '../../composables/useLabelingState'

const PI02_MESSAGE =
  'La clave ha sido modificada por otro usuario. Por favor, recargue el editor para no perder los cambios.'

const state = useLabelingState()
const toast = useToastStore()
const userContext = useUserContext()

// All rows (across levels) matching the selected key, refreshed on selection change
const relatedRows = ref<LocalizedLabel[]>([])
const esValue = ref('')
const enValue = ref('')
const saving = ref(false)
const restoring = ref(false)

const isUXWriterOnly = computed(() => {
  const roles = userContext.roles ?? []
  const structureRoles = ['PlatformAdmin', 'TenantAdmin', 'TenantOwner', 'ProductManager']
  const hasStructure = structureRoles.some((r) => roles.includes(r))
  return !hasStructure && roles.includes('UXWriter')
})

// Determine the "active context level" rows: rows whose company_id/product_id
// match the active workspaceContext exactly.
const activeLevelRows = computed(() => {
  const ctx = state.workspaceContext
  return relatedRows.value.filter(
    (r) => (r.company_id ?? null) === (ctx.companyId ?? null) && (r.product_id ?? null) === (ctx.productId ?? null)
  )
})

const activeEsRow = computed(() => activeLevelRows.value.find((r) => r.locale === 'es_PE') ?? null)
const activeEnRow = computed(() => activeLevelRows.value.find((r) => r.locale === 'en_US') ?? null)

// activeRow used for header metadata (label_type/description/params) — prefer
// the active-level row, fall back to any row for the key.
const activeRow = computed<LocalizedLabel | null>(() => activeEsRow.value ?? activeEnRow.value ?? relatedRows.value[0] ?? null)

const esInherited = computed(() => !activeEsRow.value)
const enInherited = computed(() => !activeEnRow.value)

// Resolve a value by walking from product -> company -> tenant for a locale.
function resolveValue(locale: 'es_PE' | 'en_US', maxCompanyId: string | null, maxProductId: string | null): string {
  const ctx = state.workspaceContext
  if (maxProductId && ctx.productId) {
    const row = relatedRows.value.find(
      (r) => r.locale === locale && (r.company_id ?? null) === (ctx.companyId ?? null) && (r.product_id ?? null) === ctx.productId
    )
    if (row) return row.label_value
  }
  if (maxCompanyId && ctx.companyId) {
    const row = relatedRows.value.find((r) => r.locale === locale && (r.company_id ?? null) === ctx.companyId && r.product_id === null)
    if (row) return row.label_value
  }
  const tenantRow = relatedRows.value.find((r) => r.locale === locale && r.company_id === null && r.product_id === null)
  return tenantRow?.label_value ?? ''
}

const tenantLevelValue = computed(() => {
  const row = relatedRows.value.find((r) => r.locale === 'es_PE' && r.company_id === null && r.product_id === null)
  return row?.label_value ?? ''
})

const companyLevelDisplay = computed(() => {
  if (!state.workspaceContext.companyId) {
    return 'Hereda de Tenant (Nivel superior)'
  }
  const row = relatedRows.value.find(
    (r) => r.locale === 'es_PE' && r.company_id === state.workspaceContext.companyId && r.product_id === null
  )
  return row?.label_value || 'Hereda de Tenant'
})

const productLevelDisplay = computed(() => {
  if (!state.workspaceContext.productId) {
    return 'Hereda de Company / Tenant (Nivel superior)'
  }
  const row = relatedRows.value.find(
    (r) =>
      r.locale === 'es_PE' &&
      (r.company_id ?? null) === (state.workspaceContext.companyId ?? null) &&
      r.product_id === state.workspaceContext.productId
  )
  return row?.label_value || 'Hereda de Company / Tenant'
})

const canRestore = computed(() => !!activeEsRow.value || !!activeEnRow.value)

watch(
  () => state.selectedKey,
  async (key) => {
    if (!key) {
      relatedRows.value = []
      esValue.value = ''
      enValue.value = ''
      return
    }
    await refreshRelatedRows()
  },
  { immediate: true }
)

watch(
  () => state.workspaceContext,
  async () => {
    if (state.selectedKey) {
      await refreshRelatedRows()
    }
  },
  { deep: true }
)

async function refreshRelatedRows() {
  if (!state.selectedKey || !state.workspaceContext.tenantId) return
  try {
    // Fetch ALL rows for this key across the additive hierarchy (no company/product
    // filter) so we can compute inheritance per-level.
    const all = await listKeys({
      tenant_id: state.workspaceContext.tenantId,
      namespace: state.selectedKey.namespace,
    })
    relatedRows.value = all.filter((r) => r.label_key === state.selectedKey?.label_key)
  } catch (err: any) {
    toast.error(extractErrorMessage(err))
    relatedRows.value = []
  }

  // Initialize editable values from the resolved (cascaded) value for the active context
  esValue.value = resolveValue('es_PE', state.workspaceContext.companyId, state.workspaceContext.productId)
  enValue.value = resolveValue('en_US', state.workspaceContext.companyId, state.workspaceContext.productId)
}

async function saveKeyChanges() {
  if (!state.selectedKey) return

  saving.value = true
  try {
    if (isUXWriterOnly.value) {
      // UXWriter: value-only updates via updateKeyValue, one call per locale.
      await saveValueOnly('es_PE', esValue.value)
      await saveValueOnly('en_US', enValue.value)
    } else {
      await saveStructureUpdate()
    }

    toast.success('Cambios guardados correctamente')
    state.refreshTrigger++
    await refreshRelatedRows()

    // Refresh selectedKey reference to a fresh row for this key
    const refreshed = relatedRows.value.find((r) => r.label_key === state.selectedKey?.label_key)
    if (refreshed) {
      state.selectedKey = refreshed
    }
  } catch (err: any) {
    if (err?.response?.status === 409) {
      const detail = err.response?.data?.detail ?? PI02_MESSAGE
      toast.error(detail)
      // Per RF-04: offer to reload the drawer's current values/version on conflict.
      await refreshRelatedRows()
    } else {
      toast.error(extractErrorMessage(err))
    }
  } finally {
    saving.value = false
  }
}

async function saveValueOnly(locale: 'es_PE' | 'en_US', value: string) {
  const row = locale === 'es_PE' ? activeEsRow.value : activeEnRow.value
  if (row) {
    await updateKeyValue(row.id, { locale, label_value: value, version: row.version })
  } else {
    // No row at active context level for this locale — create an override.
    await createKey({
      tenant_id: state.workspaceContext.tenantId,
      company_id: state.workspaceContext.companyId,
      product_id: state.workspaceContext.productId,
      namespace: state.selectedKey!.namespace,
      label_key: state.selectedKey!.label_key,
      label_type: activeRow.value?.label_type ?? undefined,
      params: activeRow.value?.params ?? [],
      description: activeRow.value?.description ?? undefined,
      values: { [locale]: value },
    })
  }
}

async function saveStructureUpdate() {
  // Structure roles: if a row exists at the active level, PATCH it (structure +
  // both locale values); otherwise create a new override row with both locales.
  const existingRow = activeEsRow.value ?? activeEnRow.value
  if (existingRow) {
    await updateKey(existingRow.id, {
      values: { es_PE: esValue.value, en_US: enValue.value },
      params: activeRow.value?.params ?? [],
      description: activeRow.value?.description ?? null,
      label_type: activeRow.value?.label_type ?? null,
      version: existingRow.version,
    })
  } else {
    await createKey({
      tenant_id: state.workspaceContext.tenantId,
      company_id: state.workspaceContext.companyId,
      product_id: state.workspaceContext.productId,
      namespace: state.selectedKey!.namespace,
      label_key: state.selectedKey!.label_key,
      label_type: activeRow.value?.label_type ?? undefined,
      params: activeRow.value?.params ?? [],
      description: activeRow.value?.description ?? undefined,
      values: { es_PE: esValue.value, en_US: enValue.value },
    })
  }
}

async function restoreInheritedValue() {
  if (!state.selectedKey || !canRestore.value) return

  restoring.value = true
  try {
    await restoreOverride({
      tenant_id: state.workspaceContext.tenantId,
      company_id: state.workspaceContext.companyId,
      product_id: state.workspaceContext.productId,
      namespace: state.selectedKey.namespace,
      locale: 'es_PE',
      label_key: state.selectedKey.label_key,
    })
    await restoreOverride({
      tenant_id: state.workspaceContext.tenantId,
      company_id: state.workspaceContext.companyId,
      product_id: state.workspaceContext.productId,
      namespace: state.selectedKey.namespace,
      locale: 'en_US',
      label_key: state.selectedKey.label_key,
    })
    toast.success('Override eliminado. Volviendo a herencia.')
    state.refreshTrigger++
    await refreshRelatedRows()
    const refreshed = relatedRows.value.find((r) => r.label_key === state.selectedKey?.label_key)
    if (refreshed) {
      state.selectedKey = refreshed
    }
  } catch (err: any) {
    if (err?.response?.status === 404) {
      toast.success('No existe override en este nivel.')
    } else {
      toast.error(extractErrorMessage(err))
    }
  } finally {
    restoring.value = false
  }
}
</script>
