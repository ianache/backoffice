<script setup lang="ts">
import { computed } from 'vue'
import {
  Chart as ChartJS,
  Title,
  Tooltip,
  Legend,
  LineElement,
  LinearScale,
  CategoryScale,
  PointElement
} from 'chart.js'
import { Line } from 'vue-chartjs'

ChartJS.register(
  Title,
  Tooltip,
  Legend,
  LineElement,
  LinearScale,
  CategoryScale,
  PointElement
)

const props = defineProps<{
  labels: string[]
  datasets: Array<{
    label: string
    data: Array<number | null>
    borderColor: string
  }>
}>()

const chartData = computed(() => {
  // Add SLO threshold line as a dashed red line across all labels
  const sloData = new Array(props.labels.length).fill(100)
  
  return {
    labels: props.labels,
    datasets: [
      ...props.datasets.map(d => ({
        ...d,
        tension: 0.1,
        spanGaps: false,
        pointRadius: 2,
        pointHoverRadius: 4,
      })),
      {
        label: 'SLO Threshold (100ms)',
        data: sloData,
        borderColor: 'rgba(186, 26, 26, 0.5)',
        borderDash: [5, 5],
        pointRadius: 0,
        fill: false,
        spanGaps: true
      }
    ]
  }
})

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      position: 'top' as const,
      labels: {
        color: 'var(--on-surface)'
      }
    },
    tooltip: {
      callbacks: {
        label: (context: any) => {
          const val = context.raw
          return `${context.dataset.label}: ${val !== null ? `${val} ms` : 'N/A'}`
        }
      }
    }
  },
  scales: {
    x: {
      grid: {
        color: 'rgba(0, 0, 0, 0.05)'
      },
      ticks: {
        color: 'var(--on-surface-variant)'
      }
    },
    y: {
      title: {
        display: true,
        text: 'Latency (ms)',
        color: 'var(--on-surface-variant)'
      },
      grid: {
        color: 'rgba(0, 0, 0, 0.05)'
      },
      ticks: {
        color: 'var(--on-surface-variant)'
      },
      min: 0
    }
  }
}
</script>

<template>
  <div class="min-h-[280px] w-full">
    <Line :data="chartData" :options="chartOptions" />
  </div>
</template>
