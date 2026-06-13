import { reactive, type InjectionKey } from 'vue'
import type { LocalizedLabel } from '../services/labels'

export interface WorkspaceContext {
  tenantId: string
  companyId: string | null
  productId: string | null
}

export interface LabelingState {
  activeNamespace: string | null
  workspaceContext: WorkspaceContext
  searchQuery: string
  selectedKey: LocalizedLabel | null
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
})

export function useLabelingState(): LabelingState {
  return state
}
