<template>
  <div class="font-body-md text-on-surface bg-background dark:bg-slate-950 dark:text-slate-200 min-h-screen flex flex-col overflow-y-auto pb-xl">
    <!-- Top App Bar -->
    <header class="w-full h-16 bg-surface-bright dark:bg-slate-900 border-b border-outline-variant dark:border-slate-800 shadow-sm z-40 flex items-center justify-between px-lg shrink-0">
      <div class="flex items-center gap-sm text-on-surface-variant dark:text-slate-400">
        <span class="font-label-md">Section:</span>
        <span class="font-title-md text-on-surface dark:text-slate-200 font-bold">Platform Status</span>
        <span class="material-symbols-outlined text-outline">chevron_right</span>
        <span class="font-title-md text-primary dark:text-primary-fixed-dim font-bold">Observability</span>
      </div>
      <div class="flex items-center gap-lg">
        <RangeSelector v-model="range" />
        <button
          @click="toggleDarkMode"
          class="material-symbols-outlined text-on-surface-variant dark:text-slate-400 hover:text-primary transition-colors cursor-pointer"
          title="Toggle Theme"
        >
          {{ isDark ? 'light_mode' : 'dark_mode' }}
        </button>
      </div>
    </header>

    <!-- Error Banner -->
    <div v-if="errorMsg" class="mx-lg mt-md p-md bg-error/10 border border-error/20 text-error rounded-xl flex items-center gap-sm">
      <span class="material-symbols-outlined">error</span>
      <span class="text-body-md">{{ errorMsg }}</span>
    </div>

    <!-- Main Content -->
    <div v-if="loading && !hasData" class="flex-1 flex flex-col items-center justify-center gap-sm p-xl">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      <p class="text-body-md text-on-surface-variant">Loading service health…</p>
    </div>

    <div v-else-if="isEmpty" class="flex-1 flex flex-col items-center justify-center text-center p-xl max-w-xl mx-auto gap-md">
      <span class="material-symbols-outlined text-outline text-[48px]">monitor_heart</span>
      <h2 class="text-headline-md font-bold text-on-surface">No health data yet</h2>
      <p class="text-body-md text-on-surface-variant">
        The health checker collects samples every 15 seconds. Check back shortly, or verify the backend health-checker task is running.
      </p>
    </div>

    <div v-else class="flex-grow flex flex-col gap-xl p-lg px-lg">
      <!-- Service Status Section -->
      <section class="flex flex-col gap-md">
        <h2 class="text-title-lg font-bold text-on-surface">
          Service Status
        </h2>
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-md">
          <StatusCard
            v-for="service in SERVICES"
            :key="service"
            :name="DISPLAY_NAME_MAP[service]"
            :status="statusMap[service]?.status ?? 'DOWN'"
            :latency-ms="statusMap[service]?.latency_ms ?? null"
          />
        </div>
      </section>

      <!-- Latency Trend Section -->
      <section class="flex flex-col gap-md bg-surface-container-lowest dark:bg-slate-900 border border-outline-variant dark:border-slate-800 rounded-xl p-md shadow-sm">
        <h2 class="text-title-lg font-bold text-on-surface">
          Latency Trend
        </h2>
        <div v-if="chartLabels.length === 0" class="flex items-center justify-center min-h-[280px]">
          <p class="text-body-md text-on-surface-variant">No latency trend data available for this range.</p>
        </div>
        <LatencyTrendChart
          v-else
          :labels="chartLabels"
          :datasets="chartDatasets"
        />
      </section>

      <!-- Uptime SLO Section -->
      <section class="flex flex-col gap-md">
        <h2 class="text-title-lg font-bold text-on-surface">
          Uptime (SLO)
        </h2>
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-md">
          <UptimeSummary
            v-for="service in SERVICES"
            :key="service"
            :name="DISPLAY_NAME_MAP[service]"
            :uptime-pct="metricsMap[service]?.uptime_pct ?? 0.0"
            :error-rate-pct="metricsMap[service]?.error_rate_pct ?? 0.0"
            :p-95-latency-ms="metricsMap[service]?.p95_latency_ms ?? null"
            :p-99-latency-ms="metricsMap[service]?.p99_latency_ms ?? null"
          />
        </div>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import RangeSelector from '../components/observability/RangeSelector.vue'
import StatusCard from '../components/observability/StatusCard.vue'
import UptimeSummary from '../components/observability/UptimeSummary.vue'
import LatencyTrendChart from '../components/observability/LatencyTrendChart.vue'
import {
  fetchServices,
  fetchMetrics,
  ServiceHealthSample,
  ServiceMetrics
} from '../services/observability'

const SERVICES = ['fastapi', 'mysql', 'bff', 'keycloak', 'ws_gateway'] as const

const DISPLAY_NAME_MAP: Record<string, string> = {
  fastapi: 'FastAPI Core',
  mysql: 'MySQL',
  bff: 'BFF',
  keycloak: 'Keycloak',
  ws_gateway: 'WebSocket Gateway'
}

const COLOR_MAP: Record<string, { light: string; dark: string }> = {
  fastapi: { light: '#a9000b', dark: '#abc7ff' },
  bff: { light: '#00529d', dark: '#67df70' },
  mysql: { light: '#16a34a', dark: '#4ade80' },
  keycloak: { light: '#f59e0b', dark: '#fcd34d' },
  ws_gateway: { light: '#5f5e5e', dark: '#a2c9ff' }
}

const range = ref<'24h' | '7d' | '30d'>('24h')
const loading = ref(false)
const errorMsg = ref<string | null>(null)

const statusMap = ref<Record<string, ServiceHealthSample>>({})
const metricsMap = ref<Record<string, ServiceMetrics>>({})

const hasData = computed(() => {
  return Object.keys(statusMap.value).length > 0 || Object.keys(metricsMap.value).length > 0
})

const isEmpty = computed(() => {
  return !loading.value && !errorMsg.value && !hasData.value
})

// Dark Mode Toggle
const isDark = ref(false)
const DARK_MODE_KEY = 'mui-observability-theme'

function toggleDarkMode() {
  isDark.value = !isDark.value
  localStorage.setItem(DARK_MODE_KEY, String(isDark.value))
  applyDarkMode()
}

function applyDarkMode() {
  document.documentElement.classList.toggle('dark', isDark.value)
}

// Format raw timestamps to pretty X-axis labels
const formatLabel = (ts: string) => {
  if (ts.includes(' ')) {
    const parts = ts.split(' ')
    if (range.value === '24h') {
      return parts[1].slice(0, 5) // HH:MM
    }
    // Return MM-DD
    const dateParts = parts[0].split('-')
    return `${dateParts[1]}-${dateParts[2]}`
  }
  return ts
}

const chartLabels = computed(() => {
  // Use first service's history buckets as the source of truth for labels
  const firstService = SERVICES.find(s => metricsMap.value[s]?.history?.length > 0)
  if (!firstService) return []
  return metricsMap.value[firstService].history.map(h => formatLabel(h.ts))
})

const chartDatasets = computed(() => {
  const datasets = []
  for (const service of SERVICES) {
    const metrics = metricsMap.value[service]
    if (!metrics || !metrics.history) continue
    
    datasets.push({
      label: DISPLAY_NAME_MAP[service],
      borderColor: isDark.value ? COLOR_MAP[service].dark : COLOR_MAP[service].light,
      data: metrics.history.map(h => h.avg_latency_ms)
    })
  }
  return datasets
})

async function loadHealthServices() {
  try {
    const data = await fetchServices()
    const newMap: Record<string, ServiceHealthSample> = {}
    for (const sample of data.items) {
      newMap[sample.service_name] = sample
    }
    statusMap.value = newMap
  } catch (err: any) {
    console.error('Failed to load health services:', err)
    errorMsg.value = 'Unable to load observability data. The dashboard will retry automatically — if this persists, contact your platform administrator.'
  }
}

async function loadMetrics() {
  loading.value = true
  try {
    const data = await fetchMetrics(range.value)
    const newMap: Record<string, ServiceMetrics> = {}
    for (const item of data.items) {
      newMap[item.service_name] = item
    }
    metricsMap.value = newMap
    errorMsg.value = null
  } catch (err: any) {
    console.error('Failed to load metrics:', err)
    errorMsg.value = 'Unable to load observability data. The dashboard will retry automatically — if this persists, contact your platform administrator.'
  } finally {
    loading.value = false
  }
}

let pollInterval: any = null

onMounted(() => {
  // Theme initialization
  const stored = localStorage.getItem(DARK_MODE_KEY)
  isDark.value = stored === 'true'
  applyDarkMode()

  // Load initial data
  loadHealthServices()
  loadMetrics()

  // Schedule auto-refresh (re-poll status pings every 15s)
  pollInterval = setInterval(() => {
    loadHealthServices()
  }, 15000)
})

onUnmounted(() => {
  if (pollInterval) {
    clearInterval(pollInterval)
  }
})

// Re-fetch metrics only when range selection changes
watch(range, () => {
  loadMetrics()
})
</script>
