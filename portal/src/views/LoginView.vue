<template>
  <main class="flex h-full w-full">
    <!-- Left Panel: Branding & Auth (30%) -->
    <section class="w-[30%] min-w-[400px] h-full flex flex-col justify-between p-xl bg-surface-container-lowest border-r border-outline-variant relative overflow-hidden">
      <!-- Decorative background -->
      <div class="absolute -top-24 -left-24 w-64 h-64 bg-primary/5 rounded-full blur-3xl pointer-events-none"></div>

      <!-- Branding -->
      <div class="z-10">
        <div class="flex items-center gap-sm">
          <div class="bg-primary p-xs rounded flex items-center justify-center">
            <md-icon class="text-on-primary" style="font-size:32px">hub</md-icon>
          </div>
          <h1 class="text-[28px] font-semibold tracking-tight text-primary leading-none">BackOffice CC</h1>
        </div>
        <p class="text-sm text-on-surface-variant mt-sm">Control Center &amp; Multi-tenant Administration</p>
      </div>

      <!-- Auth Section -->
      <div class="z-10 flex flex-col gap-lg max-w-sm">
        <div class="space-y-sm">
          <h2 class="text-[22px] font-semibold leading-7 text-on-surface">Welcome back</h2>
          <p class="text-sm text-on-surface-variant">Access your administrative dashboard using enterprise credentials.</p>
        </div>

        <!-- Primary: Keycloak SSO -->
        <button
          type="button"
          :disabled="keycloakLoading"
          class="group flex items-center justify-center gap-md w-full py-md px-lg bg-primary text-on-primary rounded-lg font-medium text-base hover:bg-primary-container transition-all shadow-md active:scale-[0.98] disabled:opacity-70 disabled:cursor-not-allowed"
          @click="loginWithKeycloak"
        >
          <md-icon v-if="!keycloakLoading">key</md-icon>
          <md-circular-progress v-else indeterminate style="--md-circular-progress-size:20px;--md-circular-progress-active-indicator-width:14;--md-circular-progress-active-indicator-color:#fff"></md-circular-progress>
          <span>{{ keycloakLoading ? 'Connecting...' : 'Sign in with Keycloak' }}</span>
        </button>

        <!-- OR divider -->
        <div class="flex items-center gap-sm">
          <div class="h-px flex-1 bg-outline-variant"></div>
          <span class="text-[11px] font-semibold tracking-widest text-outline uppercase">or</span>
          <div class="h-px flex-1 bg-outline-variant"></div>
        </div>

        <!-- Secondary: Local Admin Login -->
        <div class="flex flex-col gap-sm">
          <button
            type="button"
            class="flex items-center justify-center gap-sm py-sm border border-outline rounded-lg text-on-surface hover:bg-surface-container-low transition-colors font-medium text-base"
            @click="toggleLocalForm"
          >
            Local Admin Login
          </button>

          <!-- Collapsible credentials form -->
          <div v-if="showLocalForm" class="flex flex-col gap-sm pt-xs">
            <StitchTextField
              v-model="email"
              label="Email"
              type="email"
              required
              placeholder="admin@backoffice.dev"
              :disabled="isLoading"
            >
              <template #leading-icon><md-icon>mail</md-icon></template>
            </StitchTextField>

            <StitchTextField
              v-model="password"
              label="Password"
              type="password"
              required
              :disabled="isLoading"
            >
              <template #leading-icon><md-icon>lock</md-icon></template>
            </StitchTextField>

            <div
              v-if="error"
              class="p-sm rounded-lg bg-error-container text-on-error-container text-sm flex items-start gap-sm"
            >
              <md-icon class="text-base mt-0.5 shrink-0">error</md-icon>
              <span>{{ error }}</span>
            </div>

            <button
              type="button"
              :disabled="isLoading"
              class="flex items-center justify-center gap-sm w-full py-sm bg-primary text-on-primary rounded-lg font-medium text-base hover:bg-primary-container transition-all disabled:opacity-70 disabled:cursor-not-allowed"
              @click="handleLocalLogin"
            >
              <md-circular-progress v-if="isLoading" indeterminate style="--md-circular-progress-size:18px;--md-circular-progress-active-indicator-width:14;--md-circular-progress-active-indicator-color:#fff"></md-circular-progress>
              <span>{{ isLoading ? 'Signing in...' : 'Sign In' }}</span>
            </button>
          </div>

          <p class="text-[11px] font-medium text-on-surface-variant text-center">
            Trouble signing in?
            <a href="#" class="text-primary font-bold hover:underline">Contact Support</a>
          </p>
        </div>
      </div>

      <!-- Footer -->
      <div class="z-10 flex flex-col gap-xs">
        <div class="h-px w-full bg-outline-variant mb-sm"></div>
        <div class="flex justify-between items-center text-on-surface-variant">
          <span class="text-xs font-semibold tracking-wide">v2.4.12-stable</span>
          <div class="flex gap-md">
            <md-icon class="text-sm cursor-pointer hover:text-primary transition-colors">security</md-icon>
            <md-icon class="text-sm cursor-pointer hover:text-primary transition-colors">help_outline</md-icon>
          </div>
        </div>
      </div>
    </section>

    <!-- Right Panel: Dashboard Preview (70%) -->
    <section class="w-[70%] h-full p-xl overflow-y-auto bg-background">
      <div class="max-w-[1200px] mx-auto space-y-xl">

        <!-- Metric Cards -->
        <div class="grid grid-cols-4 gap-lg">
          <div
            v-for="metric in metrics"
            :key="metric.label"
            class="glass-panel p-md rounded-xl shadow-sm border border-outline-variant hover:shadow-md transition-all hover:scale-[1.02]"
          >
            <div class="flex items-start justify-between mb-sm">
              <span :class="`material-symbols-outlined bg-${metric.color}/10 text-${metric.color} p-xs rounded`">{{ metric.icon }}</span>
              <span v-if="metric.badge" class="text-on-secondary-container text-[10px] font-semibold uppercase tracking-wide">{{ metric.badge }}</span>
              <span v-if="metric.live" class="relative flex h-2 w-2 mt-1">
                <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                <span class="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
              </span>
            </div>
            <h3 class="text-[10px] font-semibold uppercase tracking-wider text-on-surface-variant">{{ metric.label }}</h3>
            <div class="mt-xs flex items-baseline gap-xs">
              <span class="text-[28px] font-semibold leading-9 text-on-surface">{{ metric.value }}</span>
              <span v-if="metric.delta" class="text-green-600 text-[11px] font-medium flex items-center gap-0.5">
                <span class="material-symbols-outlined text-xs">arrow_upward</span>{{ metric.delta }}
              </span>
            </div>
          </div>
        </div>

        <!-- Announcements -->
        <div class="bg-surface-container-lowest rounded-xl border border-outline-variant shadow-sm overflow-hidden">
          <div class="p-lg border-b border-outline-variant flex justify-between items-center bg-surface-container-low/50">
            <div class="flex items-center gap-sm">
              <span class="material-symbols-outlined text-on-surface">campaign</span>
              <h2 class="text-lg font-medium text-on-surface">Avisos, Alertas o Noticias</h2>
            </div>
            <div class="flex gap-sm">
              <button class="px-md py-xs bg-surface-container-lowest border border-outline-variant rounded-full text-xs font-semibold hover:bg-surface-container-low transition-colors">Ver Todo</button>
            </div>
          </div>
          <div class="divide-y divide-outline-variant">
            <div
              v-for="item in announcements"
              :key="item.title"
              class="p-lg hover:bg-surface-container-lowest transition-colors flex gap-lg group cursor-default"
            >
              <div class="flex flex-col items-center min-w-[56px]">
                <span class="text-[22px] font-semibold leading-7 text-on-surface">{{ item.day }}</span>
                <span class="text-[10px] font-semibold uppercase tracking-wide text-on-surface-variant">{{ item.month }}</span>
              </div>
              <div class="flex-1 space-y-xs">
                <div class="flex items-center gap-md">
                  <h4 class="text-base font-medium text-on-surface group-hover:text-primary transition-colors">{{ item.title }}</h4>
                  <span :class="`px-sm py-0.5 rounded-full text-[10px] font-semibold uppercase ${item.badgeClass}`">{{ item.tag }}</span>
                </div>
                <p class="text-sm text-on-surface-variant max-w-3xl">{{ item.body }}</p>
              </div>
              <span class="material-symbols-outlined self-center opacity-0 group-hover:opacity-100 transition-opacity text-primary">chevron_right</span>
            </div>
          </div>
        </div>

        <!-- Hero Image -->
        <div class="relative h-[240px] rounded-2xl overflow-hidden shadow-lg border border-outline-variant">
          <img
            src="https://lh3.googleusercontent.com/aida-public/AB6AXuBNbW0mwWAfbQ7thb-2BShwwdUhlfWAqUSLcNU_z5heZ8O457I5MmbMRqpuwxyI2t8xiAPmLIZd0ophk0bLOOJwiPpqnq13BPgENBz4rWf2k9UsHn3c-U1jfaUAtCVHLIGLbER-wRjxFSIdAWmK7zZ0HkiApxyvFud-9_Dr3A1wOOSHtUq16MS__p-dtcC7TJyIKGG-ujVFDsvHjBULa94WqGWIL8wEFZCrzWgNpo-513fP3buZiSnU-reTriXHQBIUYTX6kGsL9ck"
            alt="Enterprise infrastructure dashboard"
            class="absolute inset-0 w-full h-full object-cover"
          />
          <div class="absolute inset-0 bg-gradient-to-r from-primary/80 to-transparent flex items-center p-xl">
            <div class="max-w-md text-white">
              <h3 class="text-[28px] font-semibold leading-9 mb-xs">Monitorización en Tiempo Real</h3>
              <p class="text-base opacity-90">Visualiza el estado de todos tus servicios y despliegues desde un único punto de control.</p>
            </div>
          </div>
        </div>

      </div>
    </section>
  </main>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import StitchTextField from '../components/ui/StitchTextField.vue'

const authStore = useAuthStore()
const router = useRouter()
const route = useRoute()

const email = ref('')
const password = ref('')
const isLoading = ref(false)
const keycloakLoading = ref(false)
const error = ref('')
const showLocalForm = ref(false)

function loginWithKeycloak() {
  keycloakLoading.value = true
  authStore.login()
}

function toggleLocalForm() {
  showLocalForm.value = !showLocalForm.value
  error.value = ''
}

async function handleLocalLogin() {
  if (isLoading.value) return
  isLoading.value = true
  error.value = ''
  try {
    await authStore.loginWithCredentials(email.value, password.value)
    const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : '/dashboard'
    router.push(redirect)
  } catch (e: any) {
    error.value = e.message || 'Failed to sign in. Please check your credentials.'
  } finally {
    isLoading.value = false
  }
}

const metrics = [
  { label: '# de Tenants', value: '1,284', icon: 'domain', color: 'primary', badge: 'GLOBAL', delta: '12' },
  { label: '# Usuarios Conectados', value: '42', icon: 'group', color: 'tertiary', live: true },
  { label: '# de Productos', value: '12', icon: 'inventory_2', color: 'secondary' },
  { label: '# Feature Flags', value: '856', icon: 'toggle_on', color: 'primary' },
]

const announcements = [
  {
    day: '24', month: 'OCT',
    title: 'Actualización de Infraestructura Programada',
    tag: 'Aviso', badgeClass: 'bg-blue-100 text-blue-700',
    body: 'Se llevará a cabo un mantenimiento preventivo en el clúster de producción de la Región Este el próximo domingo de 02:00 a 04:00 AM UTC.',
  },
  {
    day: '22', month: 'OCT',
    title: 'Vulnerabilidad de Seguridad Detectada (CVE-2023-X)',
    tag: 'Alerta', badgeClass: 'bg-orange-100 text-orange-700',
    body: 'Se ha identificado una posible vulnerabilidad en el SDK de autenticación para integraciones legacy. Se recomienda actualizar a v4.2.1 inmediatamente.',
  },
  {
    day: '19', month: 'OCT',
    title: 'Nuevo Módulo: Analytics Pro',
    tag: 'New', badgeClass: 'bg-green-100 text-green-700',
    body: 'Ya está disponible el nuevo módulo de analíticas avanzadas para todos los tenants Enterprise. Incluye exportación a S3 y dashboards en tiempo real.',
  },
]
</script>

<style scoped>
.glass-panel {
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(8px);
  border: 1px solid rgba(193, 198, 214, 0.5);
}

md-icon {
  font-family: 'Material Symbols Outlined';
  font-weight: normal;
  font-style: normal;
  font-size: 24px;
  line-height: 1;
  letter-spacing: normal;
  text-transform: none;
  display: inline-block;
  white-space: nowrap;
  word-wrap: normal;
  direction: ltr;
  -webkit-font-feature-settings: 'liga';
  -webkit-font-smoothing: antialiased;
}
</style>
