import { reactive, type InjectionKey } from 'vue'
import type { LocalizedLabel } from '../services/labels'

export interface WorkspaceContext {
  tenantId: string
  companyId: string | null
  productId: string | null
}

export interface QuickCreatePrefill {
  namespace: string
  label_key: string
}

export interface LabelingState {
  activeNamespace: string | null
  workspaceContext: WorkspaceContext
  searchQuery: string
  selectedKey: LocalizedLabel | null
  showAddKeyModal: boolean
  showImportExport: boolean
  showDiagnostics: boolean
  quickCreatePrefill: QuickCreatePrefill | null
  /** Bumped whenever keys are mutated elsewhere (Add/Diagnostics) so KeysMatrix can refetch. */
  refreshTrigger: number
}

export const LABELING_STATE_KEY: InjectionKey<LabelingState> = Symbol('labelingState')

// Singleton reactive state shared across LabelingView and its descendants
// (NamespaceSidebar, KeysMatrix, WorkspaceContextSelector, and 20-08's
// TranslationDrawer). Provided via provide/inject so children can read/write
// without prop-drilling.
const state: LabelingState = reactive({
  activeNamespace: null,
  workspaceContext: {
    tenantId: '',
    companyId: null,
    productId: null,
  },
  searchQuery: '',
  selectedKey: null,
  showAddKeyModal: false,
  showImportExport: false,
  showDiagnostics: false,
  quickCreatePrefill: null,
  refreshTrigger: 0,
})

export function useLabelingState(): LabelingState {
  return state
}
