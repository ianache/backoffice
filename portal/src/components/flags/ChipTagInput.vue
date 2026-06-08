<template>
  <div
    class="chip-input flex flex-wrap gap-1 p-2 rounded-lg border border-outline-variant bg-surface-container-lowest min-h-[42px] items-center cursor-text"
    @click="($el as HTMLElement).querySelector('input')?.focus()"
  >
    <span
      v-for="(chip, i) in modelValue"
      :key="i"
      class="chip flex items-center gap-0.5 bg-primary-container text-on-primary-container text-xs font-medium px-2 py-0.5 rounded-full"
    >
      {{ chip }}
      <button
        type="button"
        class="text-[12px] leading-none material-symbols-outlined"
        @click.stop="removeChip(i)"
      >close</button>
    </span>

    <input
      v-model="inputText"
      type="text"
      placeholder="Type + Enter"
      class="bg-transparent outline-none text-sm flex-1 min-w-[80px] text-on-surface placeholder:text-on-surface-variant"
      @keydown.enter.prevent="addChip"
      @keydown.comma.prevent="addChip"
    />
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const props = defineProps<{
  modelValue: string[]
}>()

const emit = defineEmits<{
  'update:modelValue': [v: string[]]
}>()

const inputText = ref('')

function addChip(): void {
  const val = inputText.value.trim()
  if (val && !props.modelValue.includes(val)) {
    emit('update:modelValue', [...props.modelValue, val])
  }
  inputText.value = ''
}

function removeChip(index: number): void {
  emit('update:modelValue', props.modelValue.filter((_, i) => i !== index))
}
</script>
