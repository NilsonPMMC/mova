<template>
  <div class="relative">
    <input
      ref="inputRef"
      :value="displayValue"
      type="tel"
      inputmode="numeric"
      autocomplete="off"
      placeholder="000.000.000-00"
      :class="inputClass"
      maxlength="14"
      @input="onInput"
      @blur="onBlur"
    />
    <span
      v-if="showStatus && digits.length === 11"
      class="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none"
      :class="isValid ? 'text-green-600' : 'text-red-500'"
    >
      <component :is="isValid ? CheckIcon : XIcon" :size="20" />
    </span>
    <p
      v-if="showError"
      class="mt-1 text-sm text-red-600"
    >
      CPF incorreto
    </p>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { Check, X } from 'lucide-vue-next'
import { formatCpf, isValidCpf, cpfDigits } from '@/utils/cpf'

const props = withDefaults(
  defineProps<{
    modelValue?: string
    /** Mostrar borda/ícone de status (válido/inválido) */
    showStatus?: boolean
  }>(),
  { modelValue: '', showStatus: true }
)

const emit = defineEmits<{
  'update:modelValue': [value: string]
}>()

const inputRef = ref<HTMLInputElement | null>(null)
const digits = ref(cpfDigits(props.modelValue))
const touched = ref(false)

const CheckIcon = Check
const XIcon = X

const displayValue = computed(() => formatCpf(digits.value))

const isValid = computed(() => digits.value.length === 11 && isValidCpf(digits.value))

const showError = computed(
  () => touched.value && digits.value.length === 11 && !isValid.value
)

const inputClass = computed(() => {
  const base =
    'w-full px-4 py-3 rounded-xl border-2 focus:outline-none transition-colors text-gray-800 placeholder-gray-400'
  if (digits.value.length < 11) {
    return `${base} border-gray-200 focus:border-gov-blue`
  }
  if (isValid.value) {
    return `${base} border-green-500 focus:border-green-600`
  }
  return `${base} border-red-500 focus:border-red-600`
})

function onInput(e: Event) {
  const target = e.target as HTMLInputElement
  const raw = target.value.replace(/\D/g, '').slice(0, 11)
  digits.value = raw
  touched.value = true
  if (raw.length === 11 && isValidCpf(raw)) {
    emit('update:modelValue', raw)
  } else {
    emit('update:modelValue', '')
  }
}

function onBlur() {
  touched.value = true
}

watch(
  () => props.modelValue,
  (v) => {
    const d = cpfDigits(v || '')
    if (d !== digits.value) digits.value = d
  },
  { immediate: true }
)
</script>
