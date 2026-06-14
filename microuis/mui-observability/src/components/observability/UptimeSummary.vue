<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  name: string
  uptimePct: number
  errorRatePct: number
  p95LatencyMs: number | null
  p99LatencyMs: number | null
}>()

const uptimeColorClass = computed(() => {
  if (props.uptimePct >= 99.9) {
    return 'text-[#166534] dark:text-[#86efac]'
  } else if (props.uptimePct >= 99.0) {
    return 'text-[#92400e] dark:text-[#fcd34d]'
  } else {
    return 'text-[#991b1b] dark:text-[#fca5a5]'
  }
})

const isSloBreach = computed(() => {
  return props.p95LatencyMs !== null && props.p95LatencyMs > 100
})
</script>

<template>
  <div class="bg-surface-container-lowest border border-outline-variant rounded-xl p-md shadow-sm flex flex-col gap-md">
    <div class="flex items-center justify-between gap-sm">
      <h3 class="text-title-md font-bold text-on-surface">
        {{ name }}
      </h3>
    </div>
    
    <div class="flex flex-col">
      <span :class="['text-headline-lg font-mono font-bold tabular-nums leading-none', uptimeColorClass]">
        {{ uptimePct.toFixed(1) }}%
      </span>
      <span class="text-label-sm text-on-surface-variant uppercase font-bold mt-1">
        uptime
      </span>
    </div>

    <hr class="border-t border-outline-variant" />

    <div class="grid grid-cols-2 gap-sm text-[13px] font-mono text-on-surface-variant leading-relaxed">
      <div class="flex flex-col gap-xs">
        <div>
          <span>p95: </span>
          <span class="font-bold text-on-surface">
            {{ p95LatencyMs !== null ? `${p95LatencyMs.toFixed(0)}ms` : '—' }}
          </span>
          <span
            v-if="isSloBreach"
            class="material-symbols-outlined text-error text-[16px] align-middle ml-1 cursor-help"
            title="p95 latency exceeded the 100ms SLO threshold for this period."
          >
            warning
          </span>
        </div>
        <div>
          <span>p99: </span>
          <span class="font-bold text-on-surface">
            {{ p99LatencyMs !== null ? `${p99LatencyMs.toFixed(0)}ms` : '—' }}
          </span>
        </div>
      </div>
      <div class="flex flex-col justify-end">
        <div>
          <span>error rate: </span>
          <span class="font-bold text-on-surface">
            {{ errorRatePct.toFixed(1) }}%
          </span>
        </div>
      </div>
    </div>
  </div>
</template>
