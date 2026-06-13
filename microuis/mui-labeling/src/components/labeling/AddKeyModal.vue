<template>
  <div class="fixed inset-0 z-[60] flex items-center justify-center">
    <div class="absolute inset-0 bg-on-background/50 backdrop-blur-sm" @click="close"></div>
    <div class="relative bg-white dark:bg-slate-900 w-[500px] rounded-xl shadow-2xl p-lg flex flex-col gap-md border border-outline-variant dark:border-slate-800 text-on-surface dark:text-slate-200">
      <div class="flex items-center justify-between border-b border-outline-variant dark:border-slate-800 pb-sm">
        <h3 class="font-headline-md">Agregar Clave al Namespace</h3>
        <button @click="close" class="p-1 hover:bg-surface-container-high dark:hover:bg-slate-800 rounded-full">
          <span class="material-symbols-outlined">close</span>
        </button>
      </div>
      <div class="space-y-sm">
        <div>
          <label class="block text-xs font-bold uppercase tracking-wider text-on-surface-variant dark:text-slate-400">
            Nombre de Clave (`label_key`)
          </label>
          <input
            v-model="labelKey"
            type="text"
            class="w-full bg-surface-container dark:bg-slate-800 border border-outline-variant dark:border-slate-700 rounded-lg p-md font-body-md text-sm mt-1 focus:ring-primary focus:border-primary text-on-surface dark:text-slate-200"
            placeholder="ej: lbl_submit_button"
          />
          <p v-if="keyError" class="text-[11px] text-red-600 dark:text-red-400 mt-1">{{ keyError }}</p>
        </div>
        <div class="grid grid-cols-2 gap-sm">
          <div>
            <label class="block text-xs font-bold uppercase tracking-wider text-on-surface-variant dark:text-slate-400">
              Tipo de Componente
            </label>
            <select
              v-model="labelType"
              class="w-full bg-surface-container dark:bg-slate-800 border border-outline-variant dark:border-slate-700 rounded-lg p-md font-body-md text-sm mt-1 focus:ring-primary focus:border-primary text-on-surface dark:text-slate-200"
            >
              <option v-for="t in labelTypes" :key="t" :value="t">{{ t }}</option>
            </select>
          </div>
          <div>
            <label class="block text-xs font-bold uppercase tracking-wider text-on-surface-variant dark:text-slate-400">
              Variables (opcional)
            </label>
            <input
              v-model="paramsInput"
              type="text"
              class="w-full bg-surface-container dark:bg-slate-800 border border-outline-variant dark:border-slate-700 rounded-lg p-md font-body-md text-sm mt-1 focus:ring-primary focus:border-primary text-on-surface dark:text-slate-200"
              placeholder="ej: min, username"
            />
          </div>
        </div>
        <div>
          <label class="block text-xs font-bold uppercase tracking-wider text-on-surface-variant dark:text-slate-400">
            Descripción del Contexto
          </label>
          <input
            v-model="description"
            type="text"
            class="w-full bg-surface-container dark:bg-slate-800 border border-outline-variant dark:border-slate-700 rounded-lg p-md font-body-md text-sm mt-1 focus:ring-primary focus:border-primary text-on-surface dark:text-slate-200"
            placeholder="ej: Botón principal de login en pantalla inicio."
          />
        </div>
        <div class="grid grid-cols-2 gap-sm border-t border-outline-variant dark:border-slate-800 pt-md">
          <div>
            <label class="block text-xs font-bold uppercase tracking-wider text-on-surface-variant dark:text-slate-400">
              es_PE (Valor)
            </label>
            <textarea
              v-model="esValue"
              rows="2"
              class="w-full bg-surface-container dark:bg-slate-800 border border-outline-variant dark:border-slate-700 rounded-lg p-md font-body-md text-sm mt-1 focus:ring-primary focus:border-primary text-on-surface dark:text-slate-200"
              placeholder="Valor en Español..."
            ></textarea>
            <p v-for="warn in esParamWarnings" :key="warn" class="text-[11px] text-amber-600 dark:text-amber-400 mt-1">{{ warn }}</p>
          </div>
          <div>
            <label class="block text-xs font-bold uppercase tracking-wider text-on-surface-variant dark:text-slate-400">
              en_US (Valor)
            </label>
            <textarea
              v-model="enValue"
              rows="2"
              class="w-full bg-surface-container dark:bg-slate-800 border border-outline-variant dark:border-slate-700 rounded-lg p-md font-body-md text-sm mt-1 focus:ring-primary focus:border-primary text-on-surface dark:text-slate-200"
              placeholder="Valor en Inglés..."
            ></textarea>
            <p v-for="warn in enParamWarnings" :key="warn" class="text-[11px] text-amber-600 dark:text-amber-400 mt-1">{{ warn }}</p>
          </div>
        </div>
      </div>
      <div class="flex justify-end gap-md pt-sm border-t border-outline-variant dark:border-slate-800">
        <button
          @click="close"
          class="px-md py-sm border border-outline dark:border-slate-700 rounded-lg text-sm hover:bg-surface-container-high dark:hover:bg-slate-800 transition-colors"
        >
          Cancelar
        </button>
        <button
          :disabled="saving"
          @click="onSubmit"
          class="px-md py-sm bg-primary text-on-primary hover:bg-primary-container rounded-lg text-sm transition-colors disabled:opacity-50"
        >
          Añadir Clave
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useToastStore, extractErrorMessage } from 'shell/toastStore'
import { createKey } from '../../services/labels'
import { useLabelingState } from '../../composables/useLabelingState'

const KEY_NAME_REGEX = /^[a-z][a-z0-9_]*$/
const PARAM_REGEX = /\{(\w+)\}/g

const labelTypes = ['LABEL', 'PLACEHOLDER', 'VALIDATION', 'TOOLTIP'] as const

const state = useLabelingState()
const toast = useToastStore()

const labelKey = ref('')
const labelType = ref<typeof labelTypes[number]>('LABEL')
const paramsInput = ref('')
const description = ref('')
const esValue = ref('')
const enValue = ref('')
const keyError = ref('')
const saving = ref(false)

const paramsList = computed(() =>
  paramsInput.value
    .split(',')
    .map((p) => p.trim())
    .filter((p) => p.length > 0)
)

function findUnrecognizedPlaceholders(value: string): string[] {
  const found = new Set<string>()
  for (const match of value.matchAll(PARAM_REGEX)) {
    const name = match[1]
    if (!paramsList.value.includes(name)) {
      found.add(name)
    }
  }
  return Array.from(found)
}

const esParamWarnings = computed(() =>
  findUnrecognizedPlaceholders(esValue.value).map((p) => `Unrecognized placeholder {${p}} — add it to Params`)
)
const enParamWarnings = computed(() =>
  findUnrecognizedPlaceholders(enValue.value).map((p) => `Unrecognized placeholder {${p}} — add it to Params`)
)

onMounted(() => {
  const prefill = state.quickCreatePrefill
  if (prefill) {
    labelKey.value = prefill.label_key
    if (prefill.namespace && prefill.namespace !== state.activeNamespace) {
      state.activeNamespace = prefill.namespace
    }
    state.quickCreatePrefill = null
  }
})

function close() {
  state.showAddKeyModal = false
}

async function onSubmit() {
  keyError.value = ''

  if (!labelKey.value) {
    keyError.value = 'El nombre de la clave es obligatorio'
    return
  }
  if (!KEY_NAME_REGEX.test(labelKey.value)) {
    keyError.value = 'Debe coincidir con ^[a-z][a-z0-9_]*$ (ej: lbl_submit_button)'
    return
  }
  if (!state.activeNamespace) {
    toast.error('Selecciona un namespace antes de agregar una clave')
    return
  }

  saving.value = true
  try {
    await createKey({
      tenant_id: state.workspaceContext.tenantId,
      company_id: state.workspaceContext.companyId,
      product_id: state.workspaceContext.productId,
      namespace: state.activeNamespace,
      label_key: labelKey.value,
      label_type: labelType.value,
      params: paramsList.value,
      description: description.value || undefined,
      values: { es_PE: esValue.value, en_US: enValue.value },
    })
    toast.success(`Clave '${labelKey.value}' agregada al namespace ${state.activeNamespace}`)
    state.refreshTrigger++
    close()
  } catch (err: any) {
    if (err?.response?.status === 409) {
      keyError.value = 'Ya existe una clave con este nombre en este contexto'
    } else {
      toast.error(extractErrorMessage(err))
    }
  } finally {
    saving.value = false
  }
}
</script>
