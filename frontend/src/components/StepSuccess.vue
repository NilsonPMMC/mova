<template>
  <div class="animate-fade-in">
    <ChatBubble is-bot>
      <div class="inline-flex items-center gap-2">
        <CheckCircle2 :size="20" class="stroke-current text-emerald-600" />
        <span>Manifestação registrada com sucesso!</span>
      </div>
    </ChatBubble>
    
    <div class="ml-13 mt-4">
      <!-- Protocolo -->
      <div class="bg-white rounded-xl p-6 shadow-sm border-2 border-green-200 mb-4">
        <div class="text-center mb-6">
          <div class="inline-flex items-center justify-center w-16 h-16 bg-green-100 rounded-full mb-4">
            <component :is="CheckCircleIcon" :size="32" class="text-green-600" />
          </div>
          <h2 class="text-xl font-bold text-gray-900 mb-2">Protocolo Gerado</h2>
          <p class="text-2xl font-mono font-bold text-gov-blue mb-4">
            {{ protocol }}
          </p>
        </div>

        <!-- Timeline Visual -->
        <div v-if="manifestationData" class="border-t pt-6 mt-6">
          <h3 class="text-sm font-semibold text-gray-700 mb-4">Linha do Tempo de Resolução</h3>
          <div class="relative">
            <!-- Linha vertical -->
            <div class="absolute left-4 top-0 bottom-0 w-0.5 bg-gray-200"></div>
            
            <!-- Etapa 1: Recebido -->
            <div class="relative flex items-start gap-4 mb-6">
              <div class="relative z-10 flex-shrink-0 w-8 h-8 bg-green-500 rounded-full flex items-center justify-center">
                <component :is="CheckCircleIcon" :size="16" class="text-white" />
              </div>
              <div class="flex-1 pt-1">
                <p class="text-sm font-semibold text-gray-900">1. Recebido</p>
                <p class="text-xs text-gray-500 mt-1">Sua manifestação foi registrada com sucesso</p>
                <p class="text-xs text-gray-400 mt-1">{{ formatDate(manifestationData.created_at) }}</p>
              </div>
            </div>

            <!-- Etapa 2: Análise Técnica -->
            <div class="relative flex items-start gap-4 mb-6">
              <div class="relative z-10 flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center"
                   :class="manifestationData.nlp_analysis ? 'bg-blue-500' : 'bg-gray-300'">
                <component 
                  :is="manifestationData.nlp_analysis ? CheckCircleIcon : LoaderIcon" 
                  :size="16" 
                  :class="manifestationData.nlp_analysis ? 'text-white' : 'text-gray-500 animate-spin'" 
                />
              </div>
              <div class="flex-1 pt-1">
                <p class="text-sm font-semibold" :class="manifestationData.nlp_analysis ? 'text-gray-900' : 'text-gray-500'">
                  2. Análise Técnica
                </p>
                <p v-if="manifestationData.nlp_analysis" class="text-xs text-gray-500 mt-1">
                  Análise concluída pela IA
                </p>
                <p v-else class="text-xs text-gray-500 mt-1">
                  Em análise pela nossa equipe técnica...
                </p>
                <p v-if="manifestationData.category_detail?.sla_hours" class="text-xs text-orange-600 mt-1 font-medium">
                  Prazo estimado: {{ formatSLA(manifestationData.category_detail.sla_hours) }}
                </p>
              </div>
            </div>

            <!-- Etapa 3: Resolução Final -->
            <div class="relative flex items-start gap-4">
              <div class="relative z-10 flex-shrink-0 w-8 h-8 bg-gray-200 rounded-full flex items-center justify-center">
                <div class="w-2 h-2 bg-gray-400 rounded-full"></div>
              </div>
              <div class="flex-1 pt-1">
                <p class="text-sm font-semibold text-gray-400">3. Resolução Final</p>
                <p class="text-xs text-gray-400 mt-1">Aguardando processamento</p>
              </div>
            </div>
          </div>
        </div>

        <!-- Recibo de Compromisso -->
        <div v-if="manifestationData" class="border-t pt-4 space-y-4 mt-4">
          <!-- Categoria -->
          <div v-if="manifestationData.category_detail" class="flex items-start gap-3">
            <component :is="TagIcon" :size="20" class="text-gov-blue mt-0.5 flex-shrink-0" />
            <div class="flex-1">
              <p class="text-xs font-semibold text-gray-500 uppercase mb-1">O que entendemos</p>
              <p class="text-sm font-medium text-gray-800">
                Você registrou uma reclamação sobre <strong>{{ manifestationData.category_detail.name }}</strong>.
              </p>
            </div>
          </div>

          <!-- SLA/Prazo -->
          <div v-if="manifestationData.category_detail?.sla_hours" class="flex items-start gap-3">
            <component :is="ClockIcon" :size="20" class="text-orange-500 mt-0.5 flex-shrink-0" />
            <div class="flex-1">
              <p class="text-xs font-semibold text-gray-500 uppercase mb-1">Prazo Estimado</p>
              <p class="text-sm font-medium text-gray-800">
                O prazo estimado para este serviço é de 
                <strong class="text-orange-600">{{ formatSLA(manifestationData.category_detail.sla_hours) }}</strong>.
              </p>
            </div>
          </div>

          <!-- Status de Análise -->
          <div v-if="isAnalyzing" class="flex items-start gap-3 bg-blue-50 p-3 rounded-lg">
            <component :is="LoaderIcon" :size="20" class="text-blue-600 mt-0.5 flex-shrink-0 animate-spin" />
            <div class="flex-1">
              <p class="text-xs font-semibold text-blue-600 uppercase mb-1">Análise em Andamento</p>
              <p class="text-sm text-blue-800">
                Nossa IA está analisando sua manifestação para determinar a urgência e categoria correta...
              </p>
            </div>
          </div>

          <!-- Análise Completa -->
          <div v-if="manifestationData.nlp_analysis && !isAnalyzing" class="bg-gray-50 p-3 rounded-lg">
            <p class="text-xs font-semibold text-gray-500 uppercase mb-2">Análise Completa</p>
            <div class="space-y-2">
              <div class="flex justify-between text-sm">
                <span class="text-gray-600">Nível de Urgência:</span>
                <span class="font-semibold" :class="urgencyColorClass">
                  {{ urgencyLabel }}
                </span>
              </div>
              <div class="flex justify-between text-sm">
                <span class="text-gray-600">Sentimento:</span>
                <span class="font-semibold" :class="sentimentColorClass">
                  {{ sentimentLabel }}
                </span>
              </div>
            </div>
          </div>

          <!-- Anexos -->
          <div v-if="manifestationData.attachments && manifestationData.attachments.length > 0" class="border-t pt-4 mt-4">
            <p class="text-xs font-semibold text-gray-500 uppercase mb-2">Evidências Anexadas</p>
            <div class="grid grid-cols-2 gap-2">
              <div
                v-for="attachment in manifestationData.attachments"
                :key="attachment.id"
                class="bg-white border border-gray-200 rounded-lg p-2"
              >
                <a
                  v-if="getMediaUrl(attachment.file_url)"
                  :href="getMediaUrl(attachment.file_url)"
                  target="_blank"
                  class="block hover:opacity-80 transition-opacity"
                >
                  <img
                    v-if="attachment.file_type === 'IMAGE'"
                    :src="getMediaUrl(attachment.file_url)"
                    :alt="attachment.filename"
                    class="w-full h-20 object-cover rounded"
                  />
                  <div v-else class="w-full h-20 bg-red-100 rounded flex items-center justify-center">
                    <component :is="FileIcon" :size="24" class="text-red-600" />
                  </div>
                  <p class="text-xs text-gray-600 mt-1 truncate">{{ attachment.filename }}</p>
                </a>
              </div>
            </div>
          </div>
        </div>

        <!-- Mensagem Final -->
        <div class="mt-6 pt-4 border-t">
          <p class="text-sm text-gray-600 text-center">
            Sua manifestação está sendo analisada pela nossa equipe. 
            <span v-if="!store.isAnonymous && (store.citizenEmail || store.citizenCpf)">
              Você receberá atualizações em breve.
            </span>
            <span v-else>
              Acompanhe pelo protocolo acima.
            </span>
          </p>
        </div>
      </div>

      <!-- Fila de demandas pendentes (Cross-sell) -->
      <div v-if="store.pendingDemands && store.pendingDemands.length > 0" class="mt-8 border-t border-slate-200 pt-6 animate-fade-in text-left">
        <div class="bg-blue-50 border border-blue-200 rounded-lg p-5">
          <h3 class="text-lg font-bold text-blue-800 mb-2">💡 Notamos outros relatos no seu texto</h3>
          <p class="text-sm text-blue-700 mb-4">Para agilizar, já separamos as outras solicitações. Deseja registrá-las agora?</p>
          
          <div class="space-y-3">
            <div 
              v-for="(demand, index) in store.pendingDemands" 
              :key="index"
              class="bg-white border border-blue-100 p-4 rounded flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 shadow-sm"
            >
              <div>
                <p class="font-semibold text-slate-800 text-sm">{{ demand.category_detail }}</p>
                <p class="text-xs text-slate-500 italic mt-1 line-clamp-2">"{{ demand.specific_text }}"</p>
              </div>
              <button 
                @click="handleStartPending(index)"
                class="shrink-0 px-4 py-2 bg-blue-600 text-white rounded-md text-sm font-medium hover:bg-blue-700 transition-colors"
              >
                Registrar este
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Botões de Ação -->
      <div class="flex gap-3">
        <button
          @click="$emit('new')"
          class="flex-1 px-6 py-3 bg-gray-200 text-gray-700 font-medium rounded-xl hover:bg-gray-300 transition-colors"
        >
          Nova Manifestação
        </button>
        <button
          @click="$emit('home')"
          class="flex-1 px-6 py-3 bg-gov-blue text-white font-medium rounded-xl hover:bg-gov-dark transition-colors"
        >
          Voltar ao Início
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { CheckCircle2 } from '@/utils/icons'
import { CheckCircle, Clock, Tag, Loader, File } from 'lucide-vue-next'
import ChatBubble from './ChatBubble.vue'
import { useManifestationStore } from '@/stores/manifestation'
import apiService from '@/services/api'

const props = defineProps<{
  protocol: string
}>()

const emit = defineEmits<{
  new: []
  home: []
  'register-another-demand': []
  'start-next': []
}>()

const store = useManifestationStore()
const manifestationData = ref<any>(null)
const isAnalyzing = ref(true)
const pollingInterval = ref<number | null>(null)

const handleStartPending = (index: number) => {
  store.startNextPendingDemand(index)
  // Mantém compatibilidade com o evento antigo e emite também o novo fluxo
  emit('register-another-demand')
  emit('start-next')
}

const CheckCircleIcon = CheckCircle
const ClockIcon = Clock
const TagIcon = Tag
const LoaderIcon = Loader
const FileIcon = File

const apiOrigin = (() => {
  try {
    const base = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'
    return new URL(base).origin
  } catch {
    return 'http://localhost:8000'
  }
})()

function getMediaUrl(url: string | null | undefined): string {
  if (!url) return ''
  if (url.startsWith('http://') || url.startsWith('https://')) {
    try {
      const u = new URL(url)
      if (u.pathname.startsWith('/media/') && u.origin !== apiOrigin) {
        return `${apiOrigin}${u.pathname}`
      }
      return url
    } catch {
      return url
    }
  }
  return `${apiOrigin}${url.startsWith('/') ? url : `/${url}`}`
}

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

function formatDate(dateString: string): string {
  if (!dateString) return ''
  const date = new Date(dateString)
  return date.toLocaleDateString('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

async function fetchManifestation() {
  try {
    // Buscar por protocolo usando endpoint customizado
    const response = await apiService.get(`/reports/manifestations/by-protocol/${props.protocol}/`)
    manifestationData.value = response.data
    
    // Se já tem análise NLP, parar o polling
    if (response.data.nlp_analysis) {
      isAnalyzing.value = false
      if (pollingInterval.value) {
        clearInterval(pollingInterval.value)
        pollingInterval.value = null
      }
    }
  } catch (error: any) {
    // Se não encontrou, tentar busca normal
    if (error.response?.status === 404) {
      try {
        const searchResponse = await apiService.get(`/reports/manifestations/?search=${props.protocol}`)
        if (searchResponse.data.results && searchResponse.data.results.length > 0) {
          const manifestation = searchResponse.data.results.find((m: any) => m.protocol === props.protocol)
          if (manifestation) {
            const detailResponse = await apiService.get(`/reports/manifestations/${manifestation.id}/`)
            manifestationData.value = detailResponse.data
            
            if (detailResponse.data.nlp_analysis) {
              isAnalyzing.value = false
              if (pollingInterval.value) {
                clearInterval(pollingInterval.value)
                pollingInterval.value = null
              }
            }
          }
        }
      } catch (searchError) {
        console.error('Erro ao buscar manifestação:', searchError)
      }
    } else {
      console.error('Erro ao buscar manifestação:', error)
    }
  }
}

const urgencyLabel = computed(() => {
  if (!manifestationData.value?.nlp_analysis) return 'Aguardando análise'
  const level = manifestationData.value.nlp_analysis.urgency_level as 1 | 2 | 3 | 4 | 5
  const labels: Record<1 | 2 | 3 | 4 | 5, string> = {
    1: 'Muito Baixa',
    2: 'Baixa',
    3: 'Média',
    4: 'Alta',
    5: 'Crítica'
  }
  return labels[level] ?? 'Desconhecido'
})

const urgencyColorClass = computed(() => {
  if (!manifestationData.value?.nlp_analysis) return 'text-gray-600'
  const level = manifestationData.value.nlp_analysis.urgency_level
  if (level >= 4) return 'text-red-600'
  if (level >= 3) return 'text-orange-600'
  return 'text-green-600'
})

const sentimentLabel = computed(() => {
  if (!manifestationData.value?.nlp_analysis) return 'Aguardando análise'
  const score = manifestationData.value.nlp_analysis.sentiment_score
  if (score >= 0.3) return 'Positivo'
  if (score <= -0.3) return 'Negativo'
  return 'Neutro'
})

const sentimentColorClass = computed(() => {
  if (!manifestationData.value?.nlp_analysis) return 'text-gray-600'
  const score = manifestationData.value.nlp_analysis.sentiment_score
  if (score >= 0.3) return 'text-green-600'
  if (score <= -0.3) return 'text-red-600'
  return 'text-gray-600'
})

onMounted(() => {
  // Buscar imediatamente
  fetchManifestation()
  
  // Polling a cada 2 segundos (Circuit Breaker: máximo 15 tentativas = 30 segundos)
  let pollAttempts = 0
  const MAX_POLL_ATTEMPTS = 15
  
  pollingInterval.value = window.setInterval(() => {
    pollAttempts++
    
    // Trava de segurança: parar se status mudou (nlp já disponível) ou timeout
    if (pollAttempts > MAX_POLL_ATTEMPTS || !isAnalyzing.value) {
      if (pollingInterval.value) {
        clearInterval(pollingInterval.value)
        pollingInterval.value = null
      }
      if (pollAttempts > MAX_POLL_ATTEMPTS) {
        isAnalyzing.value = false
      }
      return
    }
    fetchManifestation()
  }, 2000)
})

onUnmounted(() => {
  if (pollingInterval.value) {
    clearInterval(pollingInterval.value)
  }
})
</script>
