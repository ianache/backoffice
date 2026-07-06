<template>
  <section class="col-span-3 border-r border-outline-variant dark:border-slate-800 bg-surface-container-lowest dark:bg-slate-900/60 flex flex-col overflow-hidden">
    <div class="p-md border-b border-outline-variant dark:border-slate-800 flex items-center justify-between">
      <h3 class="font-title-lg text-on-surface dark:text-slate-200 flex items-center gap-xs">
        <span class="material-symbols-outlined text-primary">folder_open</span>
        <span>Namespaces</span>
      </h3>
      <button
        @click="openCreateModal"
        class="flex items-center gap-xs px-sm py-1 bg-primary text-on-primary hover:bg-primary-container rounded font-title-md text-xs transition-colors shadow"
      >
        <span class="material-symbols-outlined text-xs">add</span>
        <span>Namespace</span>
      </button>
    </div>

    <div id="namespacesList" class="flex-1 overflow-y-auto custom-scrollbar p-sm space-y-1">
      <div
        v-for="ns in namespaces"
        :key="ns.id"
        @click="selectNamespace(ns.id)"
        :class="[
          'relative flex justify-between items-center p-md min-h-[82px] cursor-pointer transition-all rounded-lg border',
          state.activeNamespace === ns.id
            ? 'bg-primary/10 border-primary/20 text-primary dark:bg-slate-800 dark:border-slate-700 dark:text-primary-fixed-dim'
            : 'bg-surface-container-lowest border-outline-variant hover:bg-surface-container-low text-on-surface dark:bg-slate-900/40 dark:border-slate-800 dark:text-slate-300 dark:hover:bg-slate-800',
        ]"
      >
        <div class="flex flex-col gap-xs overflow-hidden pr-16">
          <span class="font-bold text-sm truncate">{{ ns.id }}</span>
          <span class="text-[10px] text-on-surface-variant dark:text-slate-400 uppercase tracking-wider">
            {{ ns.strategy === 'eager' ? 'CRITICAL / EAGER' : 'LAZY LOADING' }}
          </span>
          <span class="text-[10px] text-on-surface-variant dark:text-slate-500 truncate">
            {{ scopeLabel(ns) }}
          </span>
        </div>

        <div v-if="state.activeNamespace === ns.id" class="absolute top-2 right-2 flex items-center gap-1">
          <button
            type="button"
            class="w-8 h-8 inline-flex items-center justify-center rounded-full bg-surface-container-lowest/90 border border-outline-variant text-on-surface-variant hover:text-primary hover:border-primary dark:bg-slate-900 dark:border-slate-700"
            title="Editar namespace"
            @click.stop="openEditModal(ns)"
          >
            <span class="material-symbols-outlined text-[18px]">edit</span>
          </button>
          <button
            type="button"
            class="w-8 h-8 inline-flex items-center justify-center rounded-full bg-surface-container-lowest/90 border border-outline-variant text-on-surface-variant hover:text-error hover:border-error dark:bg-slate-900 dark:border-slate-700"
            title="Eliminar namespace"
            @click.stop="openDeleteModal(ns)"
          >
            <span class="material-symbols-outlined text-[18px]">delete</span>
          </button>
        </div>
      </div>

      <div v-if="!loading && namespaces.length === 0" class="p-md text-xs text-on-surface-variant dark:text-slate-400 italic text-center">
        No hay namespaces. Crea el primero.
      </div>
    </div>

    <div class="p-md bg-surface-container-low dark:bg-slate-900 border-t border-outline-variant dark:border-slate-800">
      <div class="flex items-start gap-sm">
        <span class="material-symbols-outlined text-primary mt-0.5">info</span>
        <div>
          <h4 class="text-xs font-bold text-on-surface dark:text-slate-200">Estrategia de Hydration</h4>
          <p class="text-[11px] text-on-surface-variant dark:text-slate-400 leading-relaxed mt-1">
            Namespaces <b>Eager</b> se cargan en el bootstrap principal. Los <b>Lazy</b> se descargan bajo demanda.
          </p>
        </div>
      </div>
    </div>

    <div v-if="showNamespaceModal" class="fixed inset-0 z-[60] flex items-center justify-center">
      <div class="absolute inset-0 bg-on-background/50 backdrop-blur-sm" @click="closeNamespaceModal"></div>
      <div class="relative bg-surface dark:bg-slate-900 w-[520px] rounded-xl shadow-2xl p-lg flex flex-col gap-md border border-outline-variant dark:border-slate-800 text-on-surface dark:text-slate-200">
        <div class="flex items-center justify-between border-b border-outline-variant dark:border-slate-800 pb-sm">
          <h3 class="font-headline-md">
            {{ modalMode === 'create' ? 'Crear Nuevo Namespace' : 'Editar Namespace' }}
          </h3>
          <button @click="closeNamespaceModal" class="p-1 hover:bg-surface-container-high dark:hover:bg-slate-800 rounded-full">
            <span class="material-symbols-outlined">close</span>
          </button>
        </div>

        <div class="space-y-sm">
          <div>
            <label class="block text-xs font-bold uppercase tracking-wider text-on-surface-variant dark:text-slate-400">Identificador (ID)</label>
            <input
              v-model="namespaceForm.id"
              type="text"
              class="w-full bg-surface-container dark:bg-slate-800 border border-outline-variant dark:border-slate-700 rounded-lg p-md font-body-md text-sm mt-1 focus:ring-primary focus:border-primary text-on-surface dark:text-slate-200"
              placeholder="ej: page_dashboard_profile"
            />
            <p v-if="idError" class="text-[11px] text-error mt-1">{{ idError }}</p>
          </div>

          <div>
            <label class="block text-xs font-bold uppercase tracking-wider text-on-surface-variant dark:text-slate-400">Tenant</label>
            <input
              v-model="namespaceForm.tenant_id"
              type="text"
              class="w-full bg-surface-container dark:bg-slate-800 border border-outline-variant dark:border-slate-700 rounded-lg p-md font-body-md text-sm mt-1 focus:ring-primary focus:border-primary text-on-surface dark:text-slate-200"
              placeholder="Global si se deja vacio"
            />
          </div>

          <div class="grid grid-cols-2 gap-sm">
            <div>
              <label class="block text-xs font-bold uppercase tracking-wider text-on-surface-variant dark:text-slate-400">Company</label>
              <input
                v-model="namespaceForm.company_id"
                type="text"
                class="w-full bg-surface-container dark:bg-slate-800 border border-outline-variant dark:border-slate-700 rounded-lg p-md font-body-md text-sm mt-1 focus:ring-primary focus:border-primary text-on-surface dark:text-slate-200"
                placeholder="Opcional"
              />
            </div>
            <div>
              <label class="block text-xs font-bold uppercase tracking-wider text-on-surface-variant dark:text-slate-400">Product</label>
              <input
                v-model="namespaceForm.product_id"
                type="text"
                class="w-full bg-surface-container dark:bg-slate-800 border border-outline-variant dark:border-slate-700 rounded-lg p-md font-body-md text-sm mt-1 focus:ring-primary focus:border-primary text-on-surface dark:text-slate-200"
                placeholder="Opcional"
              />
            </div>
          </div>

          <div>
            <label class="block text-xs font-bold uppercase tracking-wider text-on-surface-variant dark:text-slate-400">Estrategia de Carga</label>
            <select
              v-model="namespaceForm.strategy"
              class="w-full bg-surface-container dark:bg-slate-800 border border-outline-variant dark:border-slate-700 rounded-lg p-md font-body-md text-sm mt-1 focus:ring-primary focus:border-primary text-on-surface dark:text-slate-200"
            >
              <option value="lazy">Lazy Loading (Carga diferida bajo demanda)</option>
              <option value="eager">Eager Loading (Carga critica al iniciar)</option>
            </select>
          </div>

          <div>
            <label class="block text-xs font-bold uppercase tracking-wider text-on-surface-variant dark:text-slate-400">Descripcion</label>
            <textarea
              v-model="namespaceForm.description"
              rows="2"
              class="w-full bg-surface-container dark:bg-slate-800 border border-outline-variant dark:border-slate-700 rounded-lg p-md font-body-md text-sm mt-1 focus:ring-primary focus:border-primary text-on-surface dark:text-slate-200"
              placeholder="Describe brevemente el alcance de este namespace..."
            ></textarea>
          </div>
        </div>

        <div class="flex justify-end gap-md pt-sm border-t border-outline-variant dark:border-slate-800">
          <button @click="closeNamespaceModal" class="px-md py-sm border border-outline dark:border-slate-700 rounded-lg text-sm hover:bg-surface-container-high dark:hover:bg-slate-800 transition-colors">
            Cancelar
          </button>
          <button @click="saveNamespace" :disabled="saving" class="px-md py-sm bg-primary text-on-primary hover:bg-primary-container rounded-lg text-sm transition-colors disabled:opacity-50">
            {{ modalMode === 'create' ? 'Crear Namespace' : 'Guardar Cambios' }}
          </button>
        </div>
      </div>
    </div>

    <div v-if="showDeleteModal" class="fixed inset-0 z-[70] flex items-center justify-center">
      <div class="absolute inset-0 bg-on-background/50 backdrop-blur-sm" @click="closeDeleteModal"></div>
      <div class="relative bg-surface dark:bg-slate-900 w-[440px] rounded-xl shadow-2xl p-lg flex flex-col gap-md border border-error/30 text-on-surface dark:text-slate-200">
        <div class="flex items-center justify-between border-b border-outline-variant dark:border-slate-800 pb-sm">
          <h3 class="font-headline-md flex items-center gap-xs text-error">
            <span class="material-symbols-outlined">delete</span>
            <span>Eliminar Namespace</span>
          </h3>
          <button @click="closeDeleteModal" class="p-1 hover:bg-surface-container-high dark:hover:bg-slate-800 rounded-full">
            <span class="material-symbols-outlined">close</span>
          </button>
        </div>

        <p class="text-sm text-on-surface-variant dark:text-slate-400">
          Esta accion eliminara el namespace
          <strong class="text-on-surface dark:text-slate-200">{{ namespaceToDelete?.id }}</strong>.
          Para confirmar, escribe el nombre exacto del namespace.
        </p>

        <div>
          <label class="block text-xs font-bold uppercase tracking-wider text-on-surface-variant dark:text-slate-400">Confirmacion</label>
          <input
            v-model="deleteConfirmation"
            type="text"
            class="w-full bg-surface-container dark:bg-slate-800 border border-outline-variant dark:border-slate-700 rounded-lg p-md font-body-md text-sm mt-1 focus:ring-error focus:border-error text-on-surface dark:text-slate-200"
            :placeholder="namespaceToDelete?.id"
          />
        </div>

        <div class="flex justify-end gap-md pt-sm border-t border-outline-variant dark:border-slate-800">
          <button @click="closeDeleteModal" class="px-md py-sm border border-outline dark:border-slate-700 rounded-lg text-sm hover:bg-surface-container-high dark:hover:bg-slate-800 transition-colors">
            Cancelar
          </button>
          <button
            @click="confirmDeleteNamespace"
            :disabled="deleting || deleteConfirmation !== namespaceToDelete?.id"
            class="px-md py-sm bg-error text-on-error hover:opacity-90 rounded-lg text-sm transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Eliminar Namespace
          </button>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { ref, reactive, watch, onMounted } from 'vue'
import { useToastStore, extractErrorMessage } from 'shell/toastStore'
import {
  listNamespaces,
  createNamespace,
  updateNamespace,
  deleteNamespace,
  type Namespace,
  type NamespacePayload,
} from '../../services/labels'
import { useLabelingState } from '../../composables/useLabelingState'

const state = useLabelingState()
const toast = useToastStore()

const namespaces = ref<Namespace[]>([])
const loading = ref(false)
const showNamespaceModal = ref(false)
const modalMode = ref<'create' | 'edit'>('create')
const saving = ref(false)
const idError = ref('')
const editingNamespaceId = ref<string | null>(null)
const showDeleteModal = ref(false)
const deleting = ref(false)
const namespaceToDelete = ref<Namespace | null>(null)
const deleteConfirmation = ref('')

const namespaceForm = reactive<NamespacePayload>({
  id: '',
  tenant_id: null,
  company_id: null,
  product_id: null,
  strategy: 'lazy',
  description: '',
})

const NAMESPACE_ID_RE = /^[a-z0-9_]{1,100}$/

onMounted(fetchNamespaces)
watch(() => state.workspaceContext, fetchNamespaces, { deep: true })

async function fetchNamespaces() {
  loading.value = true
  try {
    namespaces.value = await listNamespaces()
    if (!state.activeNamespace && namespaces.value.length > 0) {
      const common = namespaces.value.find((ns) => ns.id === 'common')
      state.activeNamespace = (common ?? namespaces.value[0]).id
    }
  } catch (err: any) {
    toast.error(extractErrorMessage(err))
  } finally {
    loading.value = false
  }
}

function selectNamespace(id: string) {
  state.activeNamespace = id
  state.selectedKey = null
}

function openCreateModal() {
  modalMode.value = 'create'
  editingNamespaceId.value = null
  namespaceForm.id = ''
  namespaceForm.tenant_id = state.workspaceContext.tenantId || null
  namespaceForm.company_id = state.workspaceContext.companyId
  namespaceForm.product_id = state.workspaceContext.productId
  namespaceForm.strategy = 'lazy'
  namespaceForm.description = ''
  idError.value = ''
  showNamespaceModal.value = true
}

function openEditModal(ns: Namespace) {
  modalMode.value = 'edit'
  editingNamespaceId.value = ns.id
  namespaceForm.id = ns.id
  namespaceForm.tenant_id = ns.tenant_id
  namespaceForm.company_id = ns.company_id
  namespaceForm.product_id = ns.product_id
  namespaceForm.strategy = ns.strategy
  namespaceForm.description = ns.description ?? ''
  idError.value = ''
  showNamespaceModal.value = true
}

function closeNamespaceModal() {
  showNamespaceModal.value = false
}

async function saveNamespace() {
  idError.value = ''

  if (!namespaceForm.id) {
    idError.value = 'El identificador es requerido'
    return
  }
  if (!NAMESPACE_ID_RE.test(namespaceForm.id)) {
    idError.value = 'Solo minusculas, numeros y guion bajo (max. 100 caracteres)'
    return
  }

  saving.value = true
  try {
    const payload = {
      tenant_id: blankToNull(namespaceForm.tenant_id),
      company_id: blankToNull(namespaceForm.company_id),
      product_id: blankToNull(namespaceForm.product_id),
      strategy: namespaceForm.strategy,
      description: namespaceForm.description,
    }

    if (modalMode.value === 'create') {
      await createNamespace({ id: namespaceForm.id, ...payload })
      toast.success(`Namespace '${namespaceForm.id}' creado con exito.`)
      state.activeNamespace = namespaceForm.id
    } else if (editingNamespaceId.value) {
      await updateNamespace(editingNamespaceId.value, { id: namespaceForm.id, ...payload })
      toast.success(`Namespace '${editingNamespaceId.value}' actualizado.`)
      state.activeNamespace = namespaceForm.id
    }

    showNamespaceModal.value = false
    await fetchNamespaces()
  } catch (err: any) {
    if (err?.response?.status === 409) {
      idError.value = 'Namespace ID already exists'
    } else {
      toast.error(extractErrorMessage(err))
    }
  } finally {
    saving.value = false
  }
}

function openDeleteModal(ns: Namespace) {
  namespaceToDelete.value = ns
  deleteConfirmation.value = ''
  showDeleteModal.value = true
}

function closeDeleteModal() {
  showDeleteModal.value = false
  namespaceToDelete.value = null
  deleteConfirmation.value = ''
}

async function confirmDeleteNamespace() {
  if (!namespaceToDelete.value || deleteConfirmation.value !== namespaceToDelete.value.id) return
  deleting.value = true
  try {
    const deletedId = namespaceToDelete.value.id
    await deleteNamespace(deletedId)
    toast.success(`Namespace '${deletedId}' eliminado.`)
    if (state.activeNamespace === deletedId) {
      state.activeNamespace = null
      state.selectedKey = null
    }
    closeDeleteModal()
    await fetchNamespaces()
  } catch (err: any) {
    toast.error(extractErrorMessage(err))
  } finally {
    deleting.value = false
  }
}

function blankToNull(value: string | null | undefined): string | null {
  const trimmed = value?.trim() ?? ''
  return trimmed ? trimmed : null
}

function scopeLabel(ns: Namespace): string {
  const tenant = ns.tenant_id || 'global'
  const company = ns.company_id || 'global'
  const product = ns.product_id || 'global'
  return `T:${tenant} / C:${company} / P:${product}`
}
</script>
