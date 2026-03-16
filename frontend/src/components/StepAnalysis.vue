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

        <!-- Erro de elegibilidade (ex: castração reprovada) -->
        <div v-if="analysisResult?.service_data?.eligibility_error" class="bg-red-50 border border-red-200 rounded-lg p-5 mb-6 text-center">
          <div class="flex justify-center mb-3">
            <AlertTriangle :size="32" class="text-red-500 stroke-current" />
          </div>
          <h3 class="text-lg font-bold text-red-700 mb-2">Atendimento não disponível</h3>
          <p class="text-sm text-red-600 mb-4">{{ analysisResult.service_data.eligibility_error }}</p>
          <button
            @click="$emit('back')"
            type="button"
            class="px-4 py-2 bg-red-600 text-white rounded-md text-sm font-medium hover:bg-red-700 transition-colors"
          >
            Voltar e editar relato
          </button>
        </div>

        <!-- Triagem pré-aprovada (castração elegível) -->
        <div v-else-if="analysisResult?.intent === 'SERVICE_CASTRATION'" class="bg-emerald-50 border border-emerald-200 rounded-lg p-5 mb-6 text-center">
          <div class="flex justify-center mb-3">
            <CheckCircle2 :size="32" class="text-emerald-500 stroke-current" />
          </div>
          <h3 class="text-lg font-bold text-emerald-700 mb-2">Triagem Pré-aprovada!</h3>
          <p class="text-sm text-emerald-600 mb-4">Seu animal atende aos critérios iniciais do Programa de Castração.</p>
          <p class="text-xs text-emerald-500 mb-4">No próximo passo, solicitaremos os documentos obrigatórios (RG e Comprovante de Residência).</p>

          <!-- Formulário para preencher lacunas da IA -->
          <div v-if="isCastrationApproved" class="mt-6 text-left border-t border-emerald-200 pt-4">
            <p class="text-sm text-emerald-800 font-medium mb-3">Para encontrarmos a clínica ideal, confirme os dados abaixo:</p>
            <div class="grid grid-cols-2 gap-4 mb-4">
              <div>
                <label class="block text-xs font-semibold text-emerald-700 mb-1">Espécie *</label>
                <select v-model="formAnimalType" class="w-full text-sm rounded-md border border-emerald-300 focus:ring-emerald-500 focus:border-emerald-500">
                  <option value="" disabled>Selecione</option>
                  <option value="Cão">Cão / Cachorro</option>
                  <option value="Gato">Gato</option>
                </select>
              </div>
              <div>
                <label class="block text-xs font-semibold text-emerald-700 mb-1">Sexo *</label>
                <select v-model="formAnimalGender" class="w-full text-sm rounded-md border border-emerald-300 focus:ring-emerald-500 focus:border-emerald-500">
                  <option value="" disabled>Selecione</option>
                  <option value="Macho">Macho</option>
                  <option value="Fêmea">Fêmea</option>
                </select>
              </div>
            </div>
            <div class="bg-white p-3 rounded border border-emerald-100 mb-2">
              <label class="flex items-start gap-2 text-sm text-emerald-800 cursor-pointer">
                <input type="checkbox" v-model="isHealthy" class="mt-1 rounded border-emerald-400 text-emerald-600 focus:ring-emerald-500">
                <span class="text-xs leading-tight">Declaro que o animal pesa mais de 2kg e está em boas condições de saúde (não possui restrições veterinárias, e se fêmea, não está prenha ou no cio).</span>
              </label>
            </div>
          </div>
        </div>

        <!-- Resumo da Análise (com lista de problemas quando houver múltiplas demandas) -->
        <div v-else class="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
          <h3 class="font-semibold text-blue-900 mb-2">📋 Identificamos os seguintes relatos:</h3>

          <div v-if="demandsToShow.length > 0" class="space-y-3">
            <p class="text-xs text-blue-700">
              O <strong>primeiro</strong> item será registrado agora. Os demais ficarão disponíveis para você registrar em seguida, sem precisar redigitar.
            </p>
            <div
              v-for="(d, idx) in demandsToShow"
              :key="idx"
              class="bg-white border border-blue-100 rounded-lg p-3"
            >
              <div class="flex items-start justify-between gap-3">
                <div class="min-w-0">
                  <div class="flex items-start gap-2">
                    <span
                      v-if="idx === 0"
                      class="mt-0.5 inline-flex items-center rounded-full bg-emerald-100 px-2 py-0.5 text-[11px] font-semibold text-emerald-800"
                    >
                      Principal (agora)
                    </span>
                    <span
                      v-else
                      class="mt-0.5 inline-flex items-center rounded-full bg-blue-100 px-2 py-0.5 text-[11px] font-semibold text-blue-800"
                    >
                      Pendente (depois)
                    </span>

                    <p class="text-sm font-semibold text-slate-800">
                      {{ d.category_detail || 'Não especificado' }}
                      <span v-if="d.macro_category" class="text-xs font-medium text-slate-500">
                        ({{ d.macro_category }})
                      </span>
                    </p>
                  </div>
                  <p v-if="d.specific_text" class="text-xs text-slate-500 italic mt-1 line-clamp-2">
                    "{{ d.specific_text }}"
                  </p>
                </div>
                <div class="shrink-0 text-right text-xs text-blue-700">
                  <div>
                    <span class="font-semibold">Urgência:</span>
                    {{ formatUrgencyLabel(d.urgency_level) }}
                  </div>
                  <div v-if="d.sla_hours">
                    <span class="font-semibold">Prazo:</span>
                    {{ formatSLA(d.sla_hours) }}
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div v-else>
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
        </div>

        <p v-if="!analysisResult?.service_data?.eligibility_error" class="text-sm text-gray-600 mt-2">
          Está correto? Se não, você pode adicionar uma observação abaixo.
        </p>
      </div>
    </ChatBubble>

    <!-- Campo de Correção e Botões (ocultos quando há erro de elegibilidade) -->
    <div v-if="analysisResult && !isAnalyzing && !analysisError && !analysisResult?.service_data?.eligibility_error" class="ml-13 mt-4">
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
          @click="handleConfirm"
          :disabled="isSubmitting || (isCastrationApproved && !isFormValid)"
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
import { ref, watch, computed, onMounted } from 'vue'
import { Loader, AlertCircle } from 'lucide-vue-next'
import { AlertTriangle, CheckCircle2 } from '@/utils/icons'
import ChatBubble from './ChatBubble.vue'
import apiService from '@/services/api'
import { useManifestationStore } from '@/stores/manifestation'

const props = defineProps<{
  description: string
  isSubmitting?: boolean
}>()

const emit = defineEmits<{
  confirm: []
  'continue-anyway': []
  back: []
}>()

const store = useManifestationStore()
const isAnalyzing = ref(true)
const analysisResult = ref<any>(null)

// Variáveis do Formulário de Castração
const formAnimalType = ref('')
const formAnimalGender = ref('')
const isHealthy = ref(false)

watch(
  () => analysisResult.value,
  (newVal) => {
    if (newVal?.intent === 'SERVICE_CASTRATION' && newVal?.service_data) {
      const type = (newVal.service_data.animal_type || '').toLowerCase()
      if (type?.includes('cão') || type?.includes('cachorro')) formAnimalType.value = 'Cão'
      else if (type?.includes('gato')) formAnimalType.value = 'Gato'

      const gender = (newVal.service_data.animal_gender || '').toLowerCase()
      if (gender?.includes('fêmea') || gender?.includes('femea')) formAnimalGender.value = 'Fêmea'
      else if (gender?.includes('macho')) formAnimalGender.value = 'Macho'
    }
  },
  { immediate: true }
)

const isCastrationApproved = computed(
  () =>
    analysisResult.value?.intent === 'SERVICE_CASTRATION' &&
    !analysisResult.value?.service_data?.eligibility_error
)

const isFormValid = computed(() => {
  if (!isCastrationApproved.value) return true
  return formAnimalType.value && formAnimalGender.value && isHealthy.value
})
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

function formatUrgencyLabel(level: number): string {
  const labels: Record<number, string> = {
    1: 'Muito Baixa',
    2: 'Baixa',
    3: 'Média',
    4: 'Alta',
    5: 'Crítica',
  }
  return labels[level] || 'Média'
}

const demandsToShow = computed(() => {
  const enriched = analysisResult.value?.all_demands_enriched
  if (Array.isArray(enriched) && enriched.length > 0) return enriched
  const all = analysisResult.value?.all_demands
  if (Array.isArray(all) && all.length > 0) return all
  return []
})

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
    store.setDraftAnalysis(response.data)
  } catch (error: any) {
    console.error('Erro ao analisar rascunho:', error)
    analysisError.value = error.response?.data?.error || 'Erro ao analisar. Tente novamente.'
  } finally {
    isAnalyzing.value = false
  }
}

function handleConfirm() {
  if (isCastrationApproved.value) {
    if (!isFormValid.value) {
      alert('Por favor, preencha a espécie, o sexo e confirme as condições de saúde do animal para avançar.')
      return
    }
    store.updateServiceData({
      animal_type: formAnimalType.value,
      animal_gender: formAnimalGender.value,
      is_healthy_confirmed: true,
    })
  }
  emit('confirm')
}

onMounted(() => {
  analyzeDraft()
})

// Expor correção para o componente pai
defineExpose({
  getCorrection: () => correctionText.value.trim() || null
})
</script>
