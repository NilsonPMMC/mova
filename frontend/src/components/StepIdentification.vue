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

      <!-- Nome (opcional) -->
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-2">
          Nome completo (opcional)
        </label>
        <input
          v-model="localName"
          type="text"
          placeholder="Seu nome completo"
          class="w-full px-4 py-3 rounded-xl border-2 border-gray-200 focus:border-gov-blue focus:outline-none transition-colors text-gray-800 placeholder-gray-400"
          @input="syncStore"
        />
      </div>

      <!-- Celular (opcional, WhatsApp) -->
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-2">
          Celular (opcional)
        </label>
        <input
          v-model="localPhone"
          type="tel"
          inputmode="numeric"
          placeholder="(11) 99999-9999"
          class="w-full px-4 py-3 rounded-xl border-2 border-gray-200 focus:border-gov-blue focus:outline-none transition-colors text-gray-800 placeholder-gray-400"
          @input="syncStore"
        />
        <p class="text-xs text-gray-500 mt-1">
          Para receber atualizações por WhatsApp
        </p>
      </div>

      <!-- Botão Anônimo -->
      <button
        @click="handleAnonymous"
        class="w-full text-sm text-gray-600 hover:text-gray-800 underline py-2"
      >
        Prefiro continuar anônimo
      </button>

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
const localPhone = ref(store.citizenPhone || '')

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
  localPhone.value = store.citizenPhone || ''
})

watch(() => store.citizenName, (v) => { if (v) localName.value = v })
watch(() => store.citizenPhone, (v) => { if (v) localPhone.value = v })

const canContinue = computed(() => store.citizenCpf.length === 11)

function onCpfUpdate(digits: string) {
  store.setCitizenData(localName.value, '', digits, localPhone.value)
  localCpf.value = formatCpf(digits)
}

function syncStore() {
  store.setCitizenData(localName.value, '', store.citizenCpf, localPhone.value)
}

function handleContinue() {
  // Garantir que se há CPF válido, não é anônimo
  if (store.citizenCpf && store.citizenCpf.length === 11) {
    store.setAnonymous(false)
  }
  
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

function handleAnonymous() {
  store.setAnonymous(true)
  store.setCitizenData('', '', '', '')
  localName.value = ''
  localPhone.value = ''
  localCpf.value = ''
  emit('continue')
}
</script>
