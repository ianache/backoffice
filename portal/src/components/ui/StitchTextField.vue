<script setup lang="ts">
import { computed } from 'vue';

interface Props {
  modelValue?: string | number;
  label?: string;
  type?: string;
  placeholder?: string;
  disabled?: boolean;
  required?: boolean;
  error?: boolean;
  errorText?: string;
  supportingText?: string;
  prefixText?: string;
  suffixText?: string;
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: '',
  label: '',
  type: 'text',
  placeholder: '',
  disabled: false,
  required: false,
  error: false,
  errorText: '',
  supportingText: '',
  prefixText: '',
  suffixText: '',
});

const emit = defineEmits(['update:modelValue', 'change', 'input']);

const onInput = (event: Event) => {
  const target = event.target as any;
  emit('update:modelValue', target.value);
  emit('input', event);
};

const onChange = (event: Event) => {
  emit('change', event);
};
</script>

<template>
  <md-outlined-text-field
    class="stitch-text-field"
    :label="label"
    :type="type"
    :placeholder="placeholder"
    :disabled="disabled"
    :required="required"
    :error="error"
    :error-text="errorText"
    :supporting-text="supportingText"
    :prefix-text="prefixText"
    :suffix-text="suffixText"
    :value="modelValue"
    @input="onInput"
    @change="onChange"
  >
    <slot name="leading-icon" slot="leading-icon" />
    <slot name="trailing-icon" slot="trailing-icon" />
  </md-outlined-text-field>
</template>

<style scoped>
.stitch-text-field {
  width: 100%;
  --md-outlined-text-field-container-shape: var(--rounded);
  font-family: var(--font-family-sans);
}
</style>
