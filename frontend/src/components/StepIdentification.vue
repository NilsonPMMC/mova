<template>
  <div class="animate-slide-up">
    <ChatBubble is-bot>
      {{ message }}
    </ChatBubble>
    
    <div class="ml-13 mt-2 space-y-4">
      <!-- CPF (obrigatório para validação jurídica) -->
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-2">
          CPF <span class="text-red-500">*</span>
        </label>
        <CpfInput
          :model-value="localCpf"
          @update:model-value="onCpfUpdate"
        />
        <p class="text-xs text-gray-500 mt-1">
          Exigido pelo Ouvidor Geral para validação jurídica da manifestação.
        </p>
      </div>

      <!-- Nome (obrigatório) -->
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-2">
          Nome completo <span class="text-red-500">*</span>
        </label>
        <input
          v-model="localName"
          type="text"
          placeholder="Seu nome completo"
          class="w-full px-4 py-3 rounded-xl border-2 border-gray-200 focus:border-gov-blue focus:outline-none transition-colors text-gray-800 placeholder-gray-400"
          @input="syncStore"
        />
      </div>

      <!-- Celular (obrigatório) -->
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-2">
          Celular <span class="text-red-500">*</span>
        </label>
        <input
          :value="localPhone"
          type="tel"
          inputmode="numeric"
          placeholder="(11) 99999-9999"
          class="w-full px-4 py-3 rounded-xl border-2 border-gray-200 focus:border-gov-blue focus:outline-none transition-colors text-gray-800 placeholder-gray-400"
          @input="onPhoneInput"
        />
        <p class="text-xs text-gray-500 mt-1">
          Para contato e atualizações (ex.: WhatsApp). Mínimo 10 dígitos.
        </p>
      </div>

      <!-- Botão Continuar -->
      <div v-if="canContinue" class="pt-2">
        <button
          @click="handleContinue"
          class="w-full px-6 py-3 bg-gov-blue text-white font-medium rounded-xl hover:bg-gov-dark transition-colors"
        >
          Continuar
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import ChatBubble from './ChatBubble.vue'
import CpfInput from './CpfInput.vue'
import { useManifestationStore } from '@/stores/manifestation'
import { formatCpf, cpfDigits } from '@/utils/cpf'

const STORAGE_KEY_CPF = 'ouvidoria_cpf'

defineProps<{
  message: string
}>()

const emit = defineEmits<{
  continue: []
}>()

const store = useManifestationStore()

// Valores locais: CPF formatado para exibição, nome e celular
const localCpf = ref('')
const localName = ref(store.citizenName || '')
const localPhone = ref(store.citizenPhone ? formatPhone(store.citizenPhone) : '')

function loadCpfFromStorage() {
  try {
    const saved = localStorage.getItem(STORAGE_KEY_CPF)
    if (saved && saved.replace(/\D/g, '').length === 11) {
      localCpf.value = formatCpf(saved)
      store.setCitizenData(store.citizenName, store.citizenEmail, cpfDigits(saved), store.citizenPhone)
    }
  } catch {
    // ignore
  }
}

onMounted(() => {
  if (store.citizenCpf) {
    localCpf.value = formatCpf(store.citizenCpf)
  } else {
    loadCpfFromStorage()
  }
  localName.value = store.citizenName || ''
  localPhone.value = store.citizenPhone ? formatPhone(store.citizenPhone) : ''
})

watch(() => store.citizenName, (v) => { if (v) localName.value = v })
watch(() => store.citizenPhone, (v) => { if (v) localPhone.value = formatPhone(v) })

const canContinue = computed(() => {
  const nameOk = (store.citizenName || '').trim().length >= 2
  const cpfOk = store.citizenCpf.length === 11
  const phoneDigitsOnly = (store.citizenPhone || '').replace(/\D/g, '')
  const phoneOk = phoneDigitsOnly.length >= 10
  return cpfOk && nameOk && phoneOk
})

function onCpfUpdate(digits: string) {
  store.setCitizenData(localName.value, '', digits, localPhone.value)
  localCpf.value = formatCpf(digits)
}

function phoneDigits(value: string): string {
  return value.replace(/\D/g, '').slice(0, 11)
}

function formatPhone(value: string): string {
  const digits = phoneDigits(value)
  if (!digits) return ''
  if (digits.length <= 2) return `(${digits}`
  if (digits.length <= 6) return `(${digits.slice(0, 2)}) ${digits.slice(2)}`
  if (digits.length <= 10) {
    return `(${digits.slice(0, 2)}) ${digits.slice(2, 6)}-${digits.slice(6)}`
  }
  return `(${digits.slice(0, 2)}) ${digits.slice(2, 7)}-${digits.slice(7)}`
}

function onPhoneInput(e: Event) {
  const target = e.target as HTMLInputElement
  const digits = phoneDigits(target.value)
  localPhone.value = formatPhone(digits)
  syncStore()
}

function syncStore() {
  store.setCitizenData(localName.value, '', store.citizenCpf, phoneDigits(localPhone.value))
}

function handleContinue() {
  // Persistir CPF para próxima visita
  if (store.citizenCpf) {
    try {
      localStorage.setItem(STORAGE_KEY_CPF, store.citizenCpf)
    } catch {
      // ignore
    }
  }
  emit('continue')
}
</script>
