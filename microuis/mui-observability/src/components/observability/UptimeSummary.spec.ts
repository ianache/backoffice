import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import UptimeSummary from './UptimeSummary.vue'

describe('UptimeSummary.vue', () => {
  it('renders green tier uptime and secondary metrics correctly', () => {
    const wrapper = mount(UptimeSummary, {
      props: {
        name: 'FastAPI Core',
        uptimePct: 99.95,
        errorRatePct: 0.05,
        p95LatencyMs: 12.0,
        p99LatencyMs: 25.0
      }
    })
    expect(wrapper.text()).toContain('FastAPI Core')
    expect(wrapper.text()).toContain('100.0%') // 99.95 rounds to 100.0
    expect(wrapper.text()).toContain('p95: 12ms')
    expect(wrapper.text()).toContain('p99: 25ms')
    expect(wrapper.text()).toContain('error rate: 0.1%')
    
    // Check green color class
    const uptimeEl = wrapper.find('.text-headline-lg')
    expect(uptimeEl.classes()).toContain('text-[#166534]')
    
    // SLO breach should not be visible
    expect(wrapper.find('.material-symbols-outlined').exists()).toBe(false)
  })

  it('renders amber tier and alerts on SLO breach', () => {
    const wrapper = mount(UptimeSummary, {
      props: {
        name: 'BFF',
        uptimePct: 99.5,
        errorRatePct: 0.5,
        p95LatencyMs: 105.0, // SLO breach (>100)
        p99LatencyMs: 180.0
      }
    })
    expect(wrapper.text()).toContain('99.5%')
    
    // Check amber color class
    const uptimeEl = wrapper.find('.text-headline-lg')
    expect(uptimeEl.classes()).toContain('text-[#92400e]')
    
    // SLO breach should be visible
    const warning = wrapper.find('.material-symbols-outlined')
    expect(warning.exists()).toBe(true)
    expect(warning.text()).toBe('warning')
  })

  it('renders red tier for low uptime', () => {
    const wrapper = mount(UptimeSummary, {
      props: {
        name: 'Keycloak',
        uptimePct: 98.2,
        errorRatePct: 1.8,
        p95LatencyMs: null,
        p99LatencyMs: null
      }
    })
    expect(wrapper.text()).toContain('98.2%')
    
    // Check red color class
    const uptimeEl = wrapper.find('.text-headline-lg')
    expect(uptimeEl.classes()).toContain('text-[#991b1b]')
  })
})
