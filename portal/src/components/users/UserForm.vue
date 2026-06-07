<script setup lang="ts">
import { computed } from 'vue'
import type { UserPayload } from '../../services/users'
import StitchTextField from '../ui/StitchTextField.vue'

const props = defineProps<{
  modelValue: Partial<UserPayload>
}>()

const emit = defineEmits<{
  'update:modelValue': [value: Partial<UserPayload>]
}>()

const form = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val),
})

const updateField = (field: keyof UserPayload, value: string) => {
  emit('update:modelValue', { ...props.modelValue, [field]: value })
}
</script>

<template>
  <div class="flex flex-col gap-lg">
    <StitchTextField
      label="Email address"
      type="email"
      :required="true"
      :modelValue="form.email ?? ''"
      @update:modelValue="updateField('email', $event as string)"
    />
    <StitchTextField
      label="First name"
      :required="true"
      :modelValue="form.firstName ?? ''"
      @update:modelValue="updateField('firstName', $event as string)"
    />
    <StitchTextField
      label="Last name"
      :required="true"
      :modelValue="form.lastName ?? ''"
      @update:modelValue="updateField('lastName', $event as string)"
    />
  </div>
</template>
