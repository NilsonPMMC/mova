<template>
  <div class="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 py-8 px-4">
    <div class="max-w-6xl mx-auto">
      <!-- Header -->
      <div class="text-center mb-8">
        <h1 class="text-3xl font-bold text-gray-900 mb-2">Minhas Manifestações</h1>
        <p class="text-gray-600">Digite seu CPF para ver todas as suas solicitações</p>
      </div>

      <!-- Campo de Busca por CPF -->
      <div class="bg-white rounded-2xl shadow-lg p-8 mb-6">
        <div class="flex gap-3">
          <div class="flex-1 relative">
            <component :is="UserIcon" :size="20" class="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" />
            <div class="pl-10">
              <CpfInput
                :model-value="cpfInput"
                :show-status="false"
                @update:model-value="onCpfUpdate"
              />
            </div>
          </div>
          <button
            @click="handleSearch"
            :disabled="cpfInput.length !== 11 || isLoading"
            class="px-8 py-4 bg-gov-blue text-white font-semibold rounded-xl hover:bg-gov-dark transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            <component v-if="isLoading" :is="LoaderIcon" :size="20" class="animate-spin" />
            <span v-else>Buscar</span>
          </button>
        </div>
        <p v-if="searchError" class="mt-4 text-sm text-red-600">{{ searchError }}</p>
      </div>

      <!-- Lista de Manifestações -->
      <div v-if="manifestations.length > 0" class="space-y-4">
        <div class="bg-white rounded-xl shadow-sm p-4 mb-4">
          <p class="text-sm text-gray-600">
            Encontradas <strong>{{ manifestations.length }}</strong> manifestação(ões)
          </p>
        </div>

        <div
          v-for="manifestation in manifestations"
          :key="manifestation.id"
          class="bg-white rounded-xl shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow cursor-pointer"
          @click="goToTrack(manifestation.protocol)"
        >
          <div class="flex items-start justify-between mb-4">
            <div class="flex-1">
              <div class="flex items-center gap-3 mb-2">
                <span 
                  class="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold"
                  :class="getStatusBadgeClass(manifestation.status)"
                >
                  {{ manifestation.status_display }}
                </span>
                <span class="text-xs text-gray-500">
                  {{ formatDate(manifestation.created_at) }}
                </span>
              </div>
              <p class="text-lg font-semibold text-gray-900 mb-1">
                Protocolo: <span class="font-mono text-gov-blue">{{ manifestation.protocol }}</span>
              </p>
              <p class="text-sm text-gray-600 line-clamp-2">
                {{ manifestation.description }}
              </p>
            </div>
            <component :is="ChevronRightIcon" :size="20" class="text-gray-400 flex-shrink-0 ml-4" />
          </div>

          <div class="flex items-center gap-4 text-xs text-gray-500">
            <span v-if="manifestation.category_name" class="flex items-center gap-1">
              <component :is="TagIcon" :size="14" />
              {{ manifestation.category_name }}
            </span>
            <span v-if="manifestation.has_nlp_analysis" class="flex items-center gap-1">
              <component :is="SparklesIcon" :size="14" class="text-blue-500" />
              Análise IA
            </span>
            <span v-if="isOverdue(manifestation)" class="flex items-center gap-1 text-red-600 font-semibold">
              <component :is="AlertCircleIcon" :size="14" />
              Atrasado
            </span>
          </div>
        </div>
      </div>

      <!-- Estado Vazio -->
      <div v-else-if="hasSearched && !isLoading" class="bg-white rounded-xl shadow-sm p-12 text-center">
        <component :is="FileXIcon" :size="48" class="mx-auto text-gray-300 mb-4" />
        <p class="text-gray-600 mb-2">Nenhuma manifestação encontrada</p>
        <p class="text-sm text-gray-500">Verifique se o CPF está correto ou crie uma nova manifestação</p>
        <router-link
          to="/nova-manifestacao"
          class="inline-block mt-4 px-6 py-2 bg-gov-blue text-white rounded-lg hover:bg-gov-dark transition-colors"
        >
          Nova Manifestação
        </router-link>
      </div>

      <!-- Links Úteis -->
      <div class="bg-white rounded-xl shadow-sm p-6 mt-6">
        <h3 class="text-sm font-semibold text-gray-700 mb-3">Outras opções</h3>
        <div class="flex gap-4">
          <router-link
            to="/acompanhar"
            class="text-gov-blue hover:text-gov-dark font-medium text-sm"
          >
            Buscar por protocolo →
          </router-link>
          <router-link
            to="/nova-manifestacao"
            class="text-gov-blue hover:text-gov-dark font-medium text-sm"
          >
            Nova manifestação →
          </router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { User, Loader, ChevronRight, Tag, Sparkles, AlertCircle, FileX } from 'lucide-vue-next'
import apiService from '@/services/api'
import CpfInput from '@/components/CpfInput.vue'

const router = useRouter()

const cpfInput = ref('')
const manifestations = ref<any[]>([])
const isLoading = ref(false)
const searchError = ref<string | null>(null)
const hasSearched = ref(false)

const UserIcon = User
const LoaderIcon = Loader
const ChevronRightIcon = ChevronRight
const TagIcon = Tag
const SparklesIcon = Sparkles
const AlertCircleIcon = AlertCircle
const FileXIcon = FileX

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

function formatDate(dateString: string): string {
  if (!dateString) return ''
  const date = new Date(dateString)
  return date.toLocaleDateString('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  })
}

function isOverdue(manifestation: any): boolean {
  // Lógica simplificada - em produção, calcular baseado no SLA
  if (manifestation.status === 'resolved' || manifestation.status === 'closed') {
    return false
  }
  const created = new Date(manifestation.created_at)
  const daysDiff = Math.floor((Date.now() - created.getTime()) / (1000 * 60 * 60 * 24))
  return daysDiff > 5 // Considerar atrasado após 5 dias (exemplo)
}

function goToTrack(protocol: string) {
  router.push({ path: '/acompanhar', query: { protocol } })
}

function onCpfUpdate(digits: string) {
  cpfInput.value = digits
}

async function handleSearch() {
  const cpf = cpfInput.value.trim()
  if (!cpf || cpf.length !== 11) {
    searchError.value = 'CPF inválido. Digite 11 dígitos.'
    return
  }

  isLoading.value = true
  searchError.value = null
  hasSearched.value = true

  try {
    const response = await apiService.get(`/reports/manifestations/mine/?cpf=${cpf}`)
    manifestations.value = response.data.results || []
    if (manifestations.value.length === 0) {
      searchError.value = 'Nenhuma manifestação encontrada para este CPF.'
    }
  } catch (err: any) {
    searchError.value = err.response?.data?.error || 'Erro ao buscar manifestações. Tente novamente.'
    manifestations.value = []
  } finally {
    isLoading.value = false
  }
}
</script>
