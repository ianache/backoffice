<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  name: string
  status: 'UP' | 'DEGRADED' | 'DOWN'
  latencyMs: number | null
}>()

const isDown = computed(() => props.status === 'DOWN')
const isDegraded = computed(() => props.status === 'DEGRADED')

const formattedLatency = computed(() => {
  if (isDown.value || props.latencyMs === null) {
    return '—'
  }
  return `${props.latencyMs.toFixed(1)} ms`
})
</script>

<template>
  <div
    :class="[
      'bg-surface-container-lowest border rounded-xl p-md shadow-sm flex flex-col gap-md transition-all',
      isDown ? 'border-error/45' : 'border-outline-variant'
    ]"
  >
    <div class="flex items-center justify-between gap-sm">
      <h3 class="text-title-md font-bold text-on-surface">
        {{ name }}
      </h3>
      <span
        :class="[
          'status-chip',
          status === 'UP' ? 'status-up' : (status === 'DEGRADED' ? 'status-degraded' : 'status-down')
        ]"
      >
        <span class="status-dot"></span>
        {{ status }}
      </span>
    </div>
    
    <div class="flex flex-col">
      <span
        :class="[
          'text-headline-lg font-mono font-bold tabular-nums leading-none',
          isDown || latencyMs === null
            ? 'text-on-surface/40'
            : (isDegraded ? 'text-[#92400e] dark:text-[#fcd34d]' : 'text-on-surface')
        ]"
      >
        {{ formattedLatency }}
      </span>
      <span class="text-label-sm text-on-surface-variant uppercase font-bold mt-1">
        {{ isDown || latencyMs === null ? 'unreachable' : 'current latency' }}
      </span>
    </div>
  </div>
</template>

<style scoped>
.status-chip {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 10px;
  border-radius: 9999px;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.04em;
}

.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  display: inline-block;
}

.status-up {
  background-color: #dcfce7;
  color: #166534;
}
.status-up .status-dot {
  background-color: #166534;
}

.status-degraded {
  background-color: #fef3c7;
  color: #92400e;
}
.status-degraded .status-dot {
  background-color: #f59e0b;
}

.status-down {
  background-color: #fee2e2;
  color: #991b1b;
}
.status-down .status-dot {
  background-color: #991b1b;
}

:global([data-theme='dark']) .status-up {
  background-color: rgba(52, 168, 83, 0.15);
  color: #86efac;
}
:global([data-theme='dark']) .status-up .status-dot {
  background-color: #86efac;
}

:global([data-theme='dark']) .status-degraded {
  background-color: rgba(245, 158, 11, 0.15);
  color: #fcd34d;
}
:global([data-theme='dark']) .status-degraded .status-dot {
  background-color: #fcd34d;
}

:global([data-theme='dark']) .status-down {
  background-color: rgba(239, 68, 68, 0.15);
  color: #fca5a5;
}
:global([data-theme='dark']) .status-down .status-dot {
  background-color: #fca5a5;
}
</style>
