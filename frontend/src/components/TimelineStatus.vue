<template>
  <div class="animate-fade-in">
    <div v-if="loading" class="flex items-center justify-center py-8">
      <component :is="LoaderIcon" :size="24" class="animate-spin text-gov-blue" />
      <span class="ml-2 text-gray-600">Carregando...</span>
    </div>

    <div v-else-if="error" class="bg-red-50 border border-red-200 rounded-lg p-4 mb-4">
      <p class="text-red-800 text-sm">{{ error }}</p>
    </div>

    <div v-else-if="manifestation" class="space-y-6">
      <!-- Header com Protocolo -->
      <div class="bg-white rounded-xl p-6 shadow-sm border-2 border-blue-200">
        <div class="flex items-center justify-between mb-4">
          <div>
            <p class="text-xs text-gray-500 uppercase mb-1">Protocolo</p>
            <p class="text-2xl font-mono font-bold text-gov-blue">{{ manifestation.protocol }}</p>
          </div>
          <div class="text-right">
            <span 
              class="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold"
              :class="getStatusBadgeClass(manifestation.status)"
            >
              {{ manifestation.status_display }}
            </span>
          </div>
        </div>

        <!-- Categoria e Resumo -->
        <div v-if="manifestation.category_detail" class="mt-4 pt-4 border-t border-gray-200">
          <p class="text-sm text-gray-600 mb-2">
            <strong>Categoria:</strong> {{ manifestation.category_detail.name }}
          </p>
          <p v-if="manifestation.nlp_summary" class="text-sm text-gray-700 italic">
            "{{ manifestation.nlp_summary }}"
          </p>
        </div>

        <!-- SLA Info -->
        <div v-if="manifestation.sla_info" class="mt-4 pt-4 border-t border-gray-200">
          <div class="flex items-center gap-2 text-sm">
            <component :is="ClockIcon" :size="16" class="text-orange-500" />
            <span class="text-gray-600">
              Prazo estimado: <strong>{{ formatSLA(manifestation.sla_info.sla_hours) }}</strong>
            </span>
            <span v-if="manifestation.sla_info.is_overdue" class="ml-2 text-red-600 font-semibold">
              (Atrasado)
            </span>
          </div>
        </div>
      </div>

      <!-- Timeline Visual -->
      <div class="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
        <h3 class="text-lg font-semibold text-gray-900 mb-6">Acompanhamento</h3>
        
        <div class="relative">
          <!-- Linha vertical -->
          <div class="absolute left-6 top-0 bottom-0 w-0.5 bg-gray-200"></div>

          <!-- Etapa 1: Recebido -->
          <div class="relative flex items-start gap-4 mb-6">
            <div class="relative z-10 flex-shrink-0 w-12 h-12 bg-green-500 rounded-full flex items-center justify-center shadow-md">
              <component :is="CheckCircleIcon" :size="20" class="text-white" />
            </div>
            <div class="flex-1 pt-2">
              <p class="text-sm font-semibold text-gray-900">1. Recebido</p>
              <p class="text-xs text-gray-500 mt-1">Sua manifestação foi registrada</p>
              <p class="text-xs text-gray-400 mt-1">{{ formatDate(manifestation.created_at) }}</p>
            </div>
          </div>

          <!-- Etapa 2: Em Análise -->
          <div class="relative flex items-start gap-4 mb-6">
            <div 
              class="relative z-10 flex-shrink-0 w-12 h-12 rounded-full flex items-center justify-center shadow-md"
              :class="getStepClass('in_analysis')"
            >
              <component 
                :is="manifestation.status === 'in_analysis' ? LoaderIcon : CheckCircleIcon" 
                :size="20" 
                :class="manifestation.status === 'in_analysis' ? 'text-blue-500 animate-spin' : 'text-white'"
              />
            </div>
            <div class="flex-1 pt-2">
              <p class="text-sm font-semibold" :class="getStepTextClass('in_analysis')">
                2. Em Análise Técnica
              </p>
              <p v-if="manifestation.nlp_summary" class="text-xs text-gray-600 mt-1">
                {{ manifestation.nlp_summary }}
              </p>
              <p v-else class="text-xs text-gray-500 mt-1">
                Analisando sua solicitação...
              </p>
            </div>
          </div>

          <!-- Etapa 3: Em Execução -->
          <div class="relative flex items-start gap-4 mb-6">
            <div 
              class="relative z-10 flex-shrink-0 w-12 h-12 rounded-full flex items-center justify-center shadow-md"
              :class="getStepClass('forwarded')"
            >
              <component 
                :is="manifestation.status === 'forwarded' ? LoaderIcon : (isStepCompleted('forwarded') ? CheckCircleIcon : WrenchIcon)" 
                :size="20" 
                :class="manifestation.status === 'forwarded' ? 'text-orange-500 animate-spin' : (isStepCompleted('forwarded') ? 'text-white' : 'text-gray-400')"
              />
            </div>
            <div class="flex-1 pt-2">
              <p class="text-sm font-semibold" :class="getStepTextClass('forwarded')">
                3. Em Execução
              </p>
              <p class="text-xs text-gray-500 mt-1">
                <span v-if="manifestation.sla_info">
                  Previsão: {{ formatSLA(manifestation.sla_info.sla_hours) }}
                </span>
                <span v-else>Aguardando execução...</span>
              </p>
            </div>
          </div>

          <!-- Etapa 4: Concluído -->
          <div class="relative flex items-start gap-4">
            <div 
              class="relative z-10 flex-shrink-0 w-12 h-12 rounded-full flex items-center justify-center shadow-md"
              :class="getStepClass('resolved')"
            >
              <component 
                :is="isStepCompleted('resolved') ? CheckCircleIcon : CircleIcon" 
                :size="20" 
                :class="isStepCompleted('resolved') ? 'text-white' : 'text-gray-300'"
              />
            </div>
            <div class="flex-1 pt-2">
              <p class="text-sm font-semibold" :class="getStepTextClass('resolved')">
                4. Concluído
              </p>
              <p v-if="manifestation.resolved_at" class="text-xs text-gray-500 mt-1">
                Resolvido em {{ formatDate(manifestation.resolved_at) }}
              </p>
              <p v-else class="text-xs text-gray-400 mt-1">
                Aguardando conclusão
              </p>
            </div>
          </div>
        </div>
      </div>

      <!-- Andamentos (Updates) -->
      <div v-if="manifestation.updates && manifestation.updates.length > 0" class="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
        <h3 class="text-lg font-semibold text-gray-900 mb-4">Histórico de Andamentos</h3>
        <div class="space-y-4">
          <div 
            v-for="update in manifestation.updates" 
            :key="update.id"
            class="border-l-4 border-blue-500 pl-4 py-2 bg-blue-50 rounded-r"
          >
            <div class="flex items-start justify-between mb-1">
              <span class="text-xs font-semibold text-blue-900">
                {{ update.new_status_display }}
              </span>
              <span class="text-xs text-gray-500">
                {{ formatDate(update.created_at) }}
              </span>
            </div>
            <p v-if="update.public_note" class="text-sm text-gray-700 mt-2">
              {{ update.public_note }}
            </p>
          </div>
        </div>
      </div>

      <!-- Anexos (Evidências) -->
      <div v-if="manifestation.attachments_preview && manifestation.attachments_preview.length > 0" class="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
        <h3 class="text-lg font-semibold text-gray-900 mb-4">Evidências Anexadas</h3>
        <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
          <a
            v-for="attachment in manifestation.attachments_preview"
            :key="attachment.id"
            :href="getMediaUrl(attachment.file_url)"
            target="_blank"
            class="block hover:opacity-80 transition-opacity"
          >
            <img
              :src="getMediaUrl(attachment.file_url)"
              :alt="attachment.filename"
              class="w-full h-24 object-cover rounded-lg border border-gray-200"
            />
            <p class="text-xs text-gray-600 mt-1 truncate">{{ attachment.filename }}</p>
          </a>
        </div>
      </div>

      <!-- Avaliação de Satisfação (quando resolvido e ainda não avaliado) -->
      <div
        v-if="manifestation.status === 'resolved' && canShowRatingForm"
        class="bg-white rounded-xl p-6 shadow-sm border-2 border-green-200"
      >
        <h3 class="text-lg font-semibold text-gray-900 mb-2">Como foi o atendimento?</h3>
        <p class="text-sm text-gray-600 mb-4">Sua opinião nos ajuda a melhorar o serviço.</p>

        <div v-if="rateSuccess" class="bg-green-50 border border-green-200 rounded-lg p-4 text-center">
          <component :is="CheckCircleIcon" :size="32" class="mx-auto text-green-600 mb-2" />
          <p class="text-green-800 font-medium">Obrigado por avaliar!</p>
        </div>

        <form v-else @submit.prevent="submitRating" class="space-y-4">
          <div>
            <p class="text-sm font-medium text-gray-700 mb-2">Nota (1 a 5)</p>
            <div class="flex gap-2">
              <button
                v-for="n in 5"
                :key="n"
                type="button"
                @click="rating = n"
                class="w-10 h-10 rounded-full border-2 flex items-center justify-center text-lg transition-colors"
                :class="rating === n
                  ? 'border-yellow-500 bg-yellow-100 text-yellow-700'
                  : 'border-gray-300 bg-white text-gray-400 hover:border-yellow-400'"
              >
                ★
              </button>
            </div>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Deseja adicionar algo? (opcional)</label>
            <textarea
              v-model="ratingComment"
              rows="3"
              class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:border-gov-blue focus:outline-none"
              placeholder="Comentário opcional..."
            />
          </div>
          <p v-if="rateError" class="text-sm text-red-600">{{ rateError }}</p>
          <button
            type="submit"
            :disabled="rating === 0 || rateSubmitting"
            class="w-full py-3 bg-gov-blue text-white font-semibold rounded-xl hover:bg-gov-dark transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            <component v-if="rateSubmitting" :is="LoaderIcon" :size="20" class="animate-spin" />
            <span>{{ rateSubmitting ? 'Enviando...' : 'Enviar avaliação' }}</span>
          </button>
        </form>
      </div>

      <!-- Já avaliado -->
      <div
        v-else-if="manifestation.status === 'resolved' && (manifestation.already_rated || rateSuccess)"
        class="bg-green-50 rounded-xl p-6 border border-green-200 text-center"
      >
        <component :is="CheckCircleIcon" :size="32" class="mx-auto text-green-600 mb-2" />
        <p class="text-green-800 font-medium">Obrigado por avaliar esta manifestação.</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { CheckCircle, Clock, Loader, Wrench, Circle } from 'lucide-vue-next'
import apiService from '@/services/api'

const props = defineProps<{
  protocol: string
}>()

const manifestation = ref<any>(null)
const loading = ref(true)
const error = ref<string | null>(null)

const rating = ref(0)
const ratingComment = ref('')
const rateSubmitting = ref(false)
const rateError = ref<string | null>(null)
const rateSuccess = ref(false)

const canShowRatingForm = computed(() => {
  if (!manifestation.value) return false
  return !manifestation.value.already_rated && !rateSuccess.value
})

const CheckCircleIcon = CheckCircle
const ClockIcon = Clock
const LoaderIcon = Loader
const WrenchIcon = Wrench
const CircleIcon = Circle

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

function getStatusBadgeClass(status: string): string {
  const classes: Record<string, string> = {
    'waiting_triage': 'bg-gray-100 text-gray-800',
    'in_analysis': 'bg-blue-100 text-blue-800',
    'forwarded': 'bg-orange-100 text-orange-800',
    'resolved': 'bg-green-100 text-green-800',
    'closed': 'bg-gray-100 text-gray-800',
  }
  return classes[status] || classes['waiting_triage']
}

function getStepClass(status: string): string {
  if (manifestation.value?.status === status) {
    return 'bg-orange-500'
  }
  if (isStepCompleted(status)) {
    return 'bg-blue-500'
  }
  return 'bg-gray-200'
}

function getStepTextClass(status: string): string {
  if (manifestation.value?.status === status || isStepCompleted(status)) {
    return 'text-gray-900'
  }
  return 'text-gray-400'
}

function isStepCompleted(status: string): boolean {
  const order = ['waiting_triage', 'in_analysis', 'forwarded', 'resolved', 'closed']
  const currentIndex = order.indexOf(manifestation.value?.status || '')
  const targetIndex = order.indexOf(status)
  return currentIndex > targetIndex || manifestation.value?.status === 'resolved' || manifestation.value?.status === 'closed'
}

function formatDate(dateString: string): string {
  if (!dateString) return ''
  const date = new Date(dateString)
  return date.toLocaleString('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function formatSLA(hours: number): string {
  if (hours < 24) {
    return `${hours} horas`
  } else if (hours < 48) {
    return `${Math.floor(hours / 24)} dia`
  } else {
    return `${Math.floor(hours / 24)} dias`
  }
}

async function loadManifestation() {
  loading.value = true
  error.value = null
  try {
    const response = await apiService.get(`/reports/manifestations/track/${props.protocol}/`)
    manifestation.value = response.data
  } catch (err: any) {
    error.value = err.response?.data?.error || 'Erro ao carregar manifestação. Verifique o protocolo.'
  } finally {
    loading.value = false
  }
}

async function submitRating() {
  if (rating.value < 1 || rating.value > 5) return
  rateError.value = null
  rateSubmitting.value = true
  try {
    await apiService.post(`/reports/manifestations/rate/${props.protocol}/`, {
      rating: rating.value,
      comment: ratingComment.value.trim() || undefined,
    })
    rateSuccess.value = true
  } catch (err: any) {
    rateError.value = err.response?.data?.error || 'Não foi possível enviar a avaliação. Tente novamente.'
  } finally {
    rateSubmitting.value = false
  }
}

// Carregar ao montar
loadManifestation()
</script>
