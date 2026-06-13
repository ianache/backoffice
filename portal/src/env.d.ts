/// <reference types="vite/client" />
/// <reference types="pinia-plugin-persistedstate" />

interface ImportMetaEnv {
  readonly VITE_BFF_URL?: string
  readonly VITE_BO_TENANT_ID?: string
  readonly VITE_BO_PRODUCT_ID?: string
  readonly VITE_BO_SDK_KEY?: string
  readonly VITE_BO_ENVIRONMENT?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
