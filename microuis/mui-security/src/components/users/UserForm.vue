<script setup lang="ts">
import { computed } from 'vue'
import type { UserPayload } from '../../services/users'
import StitchTextField from 'shell/StitchTextField'

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
      :modelValue="form.first_name ?? ''"
      @update:modelValue="updateField('first_name', $event as string)"
    />
    <StitchTextField
      label="Last name"
      :required="true"
      :modelValue="form.last_name ?? ''"
      @update:modelValue="updateField('last_name', $event as string)"
    />
  </div>
</template>
