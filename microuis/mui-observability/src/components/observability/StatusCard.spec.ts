import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import StatusCard from './StatusCard.vue'

describe('StatusCard.vue', () => {
  it('renders UP status and latency correctly', () => {
    const wrapper = mount(StatusCard, {
      props: {
        name: 'FastAPI Core',
        status: 'UP',
        latencyMs: 42.5
      }
    })
    expect(wrapper.text()).toContain('FastAPI Core')
    expect(wrapper.text()).toContain('UP')
    expect(wrapper.text()).toContain('42.5 ms')
    expect(wrapper.find('.status-chip').classes()).toContain('status-up')
  })

  it('renders DEGRADED status correctly with custom text styling', () => {
    const wrapper = mount(StatusCard, {
      props: {
        name: 'MySQL',
        status: 'DEGRADED',
        latencyMs: 150.0
      }
    })
    expect(wrapper.text()).toContain('DEGRADED')
    expect(wrapper.text()).toContain('150.0 ms')
    expect(wrapper.find('.status-chip').classes()).toContain('status-degraded')
  })

  it('renders DOWN status with border error and unreachable details', () => {
    const wrapper = mount(StatusCard, {
      props: {
        name: 'BFF',
        status: 'DOWN',
        latencyMs: null
      }
    })
    expect(wrapper.text()).toContain('DOWN')
    expect(wrapper.text()).toContain('—')
    expect(wrapper.text()).toContain('unreachable')
    expect(wrapper.find('.status-chip').classes()).toContain('status-down')
    expect(wrapper.classes()).toContain('border-error/45')
  })
})
