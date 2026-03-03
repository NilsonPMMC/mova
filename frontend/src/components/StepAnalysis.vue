<template>
  <div class="animate-fade-in">
    <!-- Mensagem do Bot -->
    <ChatBubble is-bot>
      <div v-if="isAnalyzing" class="flex items-center gap-2">
        <component :is="LoaderIcon" :size="20" class="animate-spin" />
        <span>Analisando sua manifestação...</span>
      </div>
      <div v-else-if="analysisError">
        <div class="inline-flex items-center gap-2 text-red-600 mb-2">
          <AlertCircle :size="16" class="stroke-current" />
          <span>Erro ao analisar</span>
        </div>
        <p class="text-sm">{{ analysisError }}</p>
      </div>
      <div v-else-if="analysisResult">
        <!-- Alerta para dúvidas -->
        <div v-if="analysisResult.intent === 'INFORMATION'" class="bg-yellow-50 border-l-4 border-yellow-400 p-4 mb-4 rounded">
          <div class="flex items-start">
            <component :is="AlertCircleIcon" :size="20" class="text-yellow-600 mt-0.5 mr-2 flex-shrink-0" />
            <div>
              <h3 class="font-semibold text-yellow-800 mb-1">Parece que você tem uma dúvida</h3>
              <p class="text-sm text-yellow-700 mb-3">
                Para dúvidas e informações rápidas, o canal mais eficiente é o <strong>156</strong> (atendimento telefônico).
                A Ouvidoria tem prazo maior de resposta, mas você pode registrar mesmo assim se preferir.
              </p>
            </div>
          </div>
        </div>

        <!-- Resumo da Análise -->
        <div class="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
          <h3 class="font-semibold text-blue-900 mb-2">📋 Entendemos que é:</h3>
          <p class="text-blue-800 mb-3">
            <strong>{{ analysisResult.suggested_category_name || 'Categoria não identificada' }}</strong>
          </p>
          
          <div v-if="analysisResult.summary" class="text-sm text-blue-700 mb-3">
            <p class="font-medium mb-1">Resumo:</p>
            <p class="italic">"{{ analysisResult.summary }}"</p>
          </div>

          <div class="flex gap-4 text-xs text-blue-600">
            <span>Urgência: {{ analysisResult.urgency_label }}</span>
            <span>•</span>
            <span v-if="analysisResult.sla_hours">
              Prazo estimado: {{ formatSLA(analysisResult.sla_hours) }}
            </span>
          </div>
        </div>

        <p class="text-sm text-gray-600 mt-2">
          Está correto? Se não, você pode adicionar uma observação abaixo.
        </p>
      </div>
    </ChatBubble>

    <!-- Campo de Correção (se usuário discordar) -->
    <div v-if="analysisResult && !isAnalyzing && !analysisError" class="ml-13 mt-4">
      <div class="bg-white rounded-xl p-4 shadow-sm border border-gray-200 mb-4">
        <label class="block text-sm font-medium text-gray-700 mb-2">
          Adicionar observação (opcional)
        </label>
        <textarea
          v-model="correctionText"
          rows="3"
          placeholder="Se a análise não estiver correta, adicione informações adicionais aqui..."
          class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-gov-blue focus:border-transparent resize-none"
        />
      </div>

      <!-- Botões de Ação -->
      <div class="flex gap-3">
        <button
          @click="$emit('confirm')"
          :disabled="isSubmitting"
          class="flex-1 px-6 py-3 bg-gov-blue text-white font-medium rounded-xl hover:bg-gov-dark transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <span v-if="!isSubmitting">Sim, está correto. Enviar</span>
          <span v-else class="flex items-center justify-center gap-2">
            <component :is="LoaderIcon" :size="16" class="animate-spin" />
            Enviando...
          </span>
        </button>
        <button
          v-if="analysisResult?.intent === 'INFORMATION'"
          @click="$emit('continue-anyway')"
          :disabled="isSubmitting"
          class="flex-1 px-6 py-3 bg-yellow-500 text-white font-medium rounded-xl hover:bg-yellow-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Registrar mesmo assim
        </button>
        <button
          @click="$emit('back')"
          :disabled="isSubmitting"
          class="px-6 py-3 bg-gray-200 text-gray-700 font-medium rounded-xl hover:bg-gray-300 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Voltar
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Loader, AlertCircle } from 'lucide-vue-next'
import ChatBubble from './ChatBubble.vue'
import apiService from '@/services/api'

const props = defineProps<{
  description: string
  isSubmitting?: boolean
}>()

defineEmits<{
  confirm: []
  'continue-anyway': []
  back: []
}>()

const isAnalyzing = ref(true)
const analysisResult = ref<any>(null)
const analysisError = ref<string | null>(null)
const correctionText = ref('')

const LoaderIcon = Loader
const AlertCircleIcon = AlertCircle

function formatSLA(hours: number): string {
  if (hours < 24) {
    return `${hours} horas`
  } else if (hours < 48) {
    return '1 dia'
  } else {
    const days = Math.ceil(hours / 24)
    return `${days} dias`
  }
}

async function analyzeDraft() {
  if (!props.description.trim()) {
    analysisError.value = 'Descrição vazia'
    isAnalyzing.value = false
    return
  }

  isAnalyzing.value = true
  analysisError.value = null

  try {
    const response = await apiService.post('/reports/manifestations/analyze_draft/', {
      description: props.description.trim()
    })
    
    analysisResult.value = response.data
  } catch (error: any) {
    console.error('Erro ao analisar rascunho:', error)
    analysisError.value = error.response?.data?.error || 'Erro ao analisar. Tente novamente.'
  } finally {
    isAnalyzing.value = false
  }
}

onMounted(() => {
  analyzeDraft()
})

// Expor correção para o componente pai
defineExpose({
  getCorrection: () => correctionText.value.trim() || null
})
</script>
