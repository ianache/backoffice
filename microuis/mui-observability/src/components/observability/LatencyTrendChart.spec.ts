import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import LatencyTrendChart from './LatencyTrendChart.vue'

// Mock vue-chartjs Line component
vi.mock('vue-chartjs', () => ({
  Line: {
    name: 'LineChartStub',
    template: '<div class="line-chart-stub" :data-chart-data="JSON.stringify(data)"></div>',
    props: ['data', 'options']
  }
}))

describe('LatencyTrendChart.vue', () => {
  it('renders and passes correct data to Line component', () => {
    const labels = ['10:00', '11:00']
    const datasets = [
      {
        label: 'FastAPI Core',
        data: [12, 15],
        borderColor: '#a9000b'
      }
    ]
    const wrapper = mount(LatencyTrendChart, {
      props: {
        labels,
        datasets
      }
    })
    
    const stub = wrapper.find('.line-chart-stub')
    expect(stub.exists()).toBe(true)
    
    // Parse passed data
    const passedData = JSON.parse(stub.attributes('data-chart-data') || '{}')
    expect(passedData.labels).toEqual(labels)
    expect(passedData.datasets.length).toBe(2) // 1 user dataset + 1 SLO dataset
    expect(passedData.datasets[0].label).toBe('FastAPI Core')
    expect(passedData.datasets[0].data).toEqual([12, 15])
    expect(passedData.datasets[1].label).toBe('SLO Threshold (100ms)')
    expect(passedData.datasets[1].data).toEqual([100, 100])
    expect(passedData.datasets[1].borderDash).toEqual([5, 5])
  })
})
