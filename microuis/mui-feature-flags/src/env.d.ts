declare module 'shell/StitchButton' {
  import { DefineComponent } from 'vue'
  const component: DefineComponent<{}, {}, any>
  export default component
}
declare module 'shell/StitchTextField' {
  import { DefineComponent } from 'vue'
  const component: DefineComponent<{}, {}, any>
  export default component
}
declare module 'shell/toastStore' {
  export const useToastStore: any
  export const extractErrorMessage: any
}
declare module 'shell/api' {
  import { AxiosInstance } from 'axios'
  const api: AxiosInstance
  export default api
}
declare module 'shell/boFlags' {
  import { Ref } from 'vue'
  export function useBoFlags(): {
    boFeature: Readonly<Ref<boolean>>
    boFeatureCreate: Readonly<Ref<boolean>>
    boFeatureUpdate: Readonly<Ref<boolean>>
    initialized: Readonly<Ref<boolean>>
    init: (userContext: Record<string, unknown>) => Promise<void>
    destroy: () => void
  }
}
