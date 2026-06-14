import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import RangeSelector from './RangeSelector.vue'

describe('RangeSelector.vue', () => {
  it('renders active range segment correctly', () => {
    const wrapper = mount(RangeSelector, {
      props: {
        modelValue: '24h'
      }
    })
    const buttons = wrapper.findAll('button')
    expect(buttons.length).toBe(3)
    expect(buttons[0].text()).toBe('24h')
    expect(buttons[0].classes()).toContain('bg-primary')
    expect(buttons[1].classes()).not.toContain('bg-primary')
  })

  it('emits update:modelValue on click', async () => {
    const wrapper = mount(RangeSelector, {
      props: {
        modelValue: '24h'
      }
    })
    const buttons = wrapper.findAll('button')
    await buttons[1].trigger('click')
    expect(wrapper.emitted('update:modelValue')?.[0]).toEqual(['7d'])
  })
})
