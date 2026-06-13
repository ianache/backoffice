import { ref, readonly } from 'vue'
import { LabelClient, createLabelPlugin } from '@backoffice/sdk-js'

export type Locale = 'es_PE' | 'en_US'

export const CATALOG_FALLBACK: Record<Locale, Record<string, string>> = {
  es_PE: {
    brand_tagline: "Centro de Control y Administracion Multi-tenant",
    welcome_title: "Bienvenido nuevamente",
    welcome_body: "Accede a tu panel administrativo usando credenciales empresariales.",
    sso_action: "Iniciar sesion con Keycloak",
    sso_connecting: "Conectando...",
    divider_or: "o",
    local_action: "Acceso de administrador local",
    email_label: "Correo electronico",
    password_label: "Contrasena",
    submit_action: "Iniciar sesion",
    submit_loading: "Iniciando sesion...",
    help_prompt: "Problemas para iniciar sesion?",
    help_action: "Contactar soporte",
    error_invalid_credentials: "Correo o contrasena invalidos.",
    error_authentication_failed: "No se pudo completar la autenticacion. Intenta nuevamente.",
    error_generic: "El inicio de sesion fallo. Intenta nuevamente o contacta a soporte.",
  },
  en_US: {
    brand_tagline: "Control Center & Multi-tenant Administration",
    welcome_title: "Welcome back",
    welcome_body: "Access your administrative dashboard using enterprise credentials.",
    sso_action: "Sign in with Keycloak",
    sso_connecting: "Connecting...",
    divider_or: "or",
    local_action: "Local Admin Login",
    email_label: "Email",
    password_label: "Password",
    submit_action: "Sign In",
    submit_loading: "Signing in...",
    help_prompt: "Trouble signing in?",
    help_action: "Contact Support",
    error_invalid_credentials: "Invalid email or password.",
    error_authentication_failed: "Authentication could not be completed. Please try again.",
    error_generic: "Sign-in failed. Please try again or contact support.",
  }
}

export function detectLoginLocale(language?: string): Locale {
  if (!language) return 'en_US'
  const lang = language.toLowerCase()
  if (lang === 'es' || lang.startsWith('es-')) {
    return 'es_PE'
  }
  return 'en_US'
}

// Module-scoped singleton state
const initialized = ref(false)
const localeRef = ref<Locale>('en_US')

let client: LabelClient | null = null
let plugin: ReturnType<typeof createLabelPlugin> | null = null
let initPromise: Promise<void> | null = null

// detect on module load
localeRef.value = detectLoginLocale(typeof navigator !== 'undefined' ? navigator.language : undefined)

function fallbackResolver(path: string, variables?: Record<string, unknown>, translated?: string): string {
  if (translated && translated.startsWith('[sys.')) {
    const [ns, key] = path.split('.')
    if (ns === 'login' && CATALOG_FALLBACK[localeRef.value]?.[key]) {
      const fallbackTemplate = CATALOG_FALLBACK[localeRef.value][key]
      if (!variables) return fallbackTemplate
      return Object.entries(variables).reduce(
        (acc, [k, v]) => acc.replace(new RegExp(`\\{${k}\\}`, 'g'), String(v)),
        fallbackTemplate,
      )
    }
  }
  return translated || ''
}

export function useLoginLabels() {
  function getClient() {
    if (!client) {
      client = new LabelClient({
        tenantId: import.meta.env.VITE_BO_TENANT_ID ?? 'platform',
        productId: 'backoffice',
        locale: localeRef.value,
        apiBaseUrl: import.meta.env.VITE_BFF_URL ?? 'http://localhost:3000',
        sdkKey: import.meta.env.VITE_BO_SDK_KEY ?? 'dev-sdk-secret-change-in-prod',
      })
    }
    return client
  }

  function getPlugin() {
    if (!plugin) {
      plugin = createLabelPlugin(getClient(), fallbackResolver)
    }
    return plugin
  }

  function initialize(): Promise<void> {
    if (initialized.value) return Promise.resolve()
    if (initPromise) return initPromise

    const c = getClient()
    initPromise = (async () => {
      try {
        await c.initialize()
        initialized.value = true
      } catch (e) {
        console.warn('[login-labels] SDK init failed, using fallbacks', e)
        // fail-open
      }
    })()

    return initPromise
  }

  async function waitForInitialLabels(timeoutMs = 1000): Promise<void> {
    if (!initPromise) {
      // If not yet started, initialize now
      void initialize()
    }
    await Promise.race([
      initPromise,
      new Promise<void>((resolve) => setTimeout(resolve, timeoutMs))
    ])
  }

  function t(path: string, variables?: Record<string, unknown>): string {
    const c = getClient()
    const translated = c.translate(path, variables)
    return fallbackResolver(path, variables, translated)
  }

  function _reset(): void {
    initialized.value = false
    localeRef.value = detectLoginLocale(typeof navigator !== 'undefined' ? navigator.language : undefined)
    client?.destroy()
    client = null
    plugin = null
    initPromise = null
  }

  function destroy(): void {
    client?.destroy()
    client = null
    plugin = null
    initialized.value = false
    initPromise = null
  }

  return {
    initialized: readonly(initialized),
    locale: readonly(localeRef),
    initialize,
    waitForInitialLabels,
    t,
    get plugin() { return getPlugin() },
    get client() { return getClient() },
    destroy,
    _reset,
  }
}
