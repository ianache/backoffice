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
