<template>
  <div class="h-screen flex flex-col bg-slate-100">
    <header class="shrink-0 bg-white border-b border-slate-200 px-6 py-4 flex items-center justify-between">
      <div class="flex items-center gap-6">
        <div>
          <h1 class="text-xl font-bold text-slate-800">Monitoramento Global</h1>
          <p class="text-sm text-slate-500 mt-0.5">Pesquisar e acompanhar manifestações</p>
        </div>
        <nav class="flex gap-2">
          <router-link
            to="/admin/inbox"
            class="px-3 py-1.5 text-sm font-medium rounded-lg transition-colors"
            :class="$route.name === 'admin-inbox' ? 'bg-slate-800 text-white' : 'text-slate-600 hover:bg-slate-100'"
          >
            Triagem
          </router-link>
          <router-link
            to="/admin/search"
            class="px-3 py-1.5 text-sm font-medium rounded-lg transition-colors"
            :class="$route.name === 'admin-search' ? 'bg-slate-800 text-white' : 'text-slate-600 hover:bg-slate-100'"
          >
            Pesquisar / Monitorar
          </router-link>
        </nav>
      </div>
      <div class="flex items-center gap-3">
        <span class="text-sm text-slate-600">{{ auth.user?.full_name || auth.user?.email || auth.user?.username }}</span>
        <button
          type="button"
          class="text-sm text-slate-500 hover:text-slate-700 underline"
          @click="logout"
        >
          Sair
        </button>
      </div>
    </header>

    <div class="flex-1 overflow-hidden flex flex-col p-6">
      <!-- Barra de Busca e Filtros -->
      <div class="bg-white rounded-lg shadow-sm border border-slate-200 p-4 mb-4">
        <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
          <!-- Busca Textual -->
          <div class="md:col-span-2">
            <label class="block text-xs font-medium text-slate-600 mb-1">Buscar</label>
            <input
              v-model="searchQuery"
              type="text"
              placeholder="Protocolo, nome, palavra-chave..."
              class="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-gov-blue focus:border-transparent"
              @keyup.enter="performSearch"
            />
          </div>

          <!-- Filtro Status -->
          <div>
            <label class="block text-xs font-medium text-slate-600 mb-1">Status</label>
            <select
              v-model="filters.status"
              class="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-gov-blue focus:border-transparent"
            >
              <option value="">Todos</option>
              <option value="waiting_triage">Aguardando Triagem</option>
              <option value="in_analysis">Em Análise</option>
              <option value="forwarded">Encaminhada</option>
              <option value="duplicate_forwarded">Duplicata Encaminhada</option>
              <option value="resolved">Resolvida</option>
              <option value="closed">Encerrada</option>
            </select>
          </div>

          <!-- Filtro Setor -->
          <div>
            <label class="block text-xs font-medium text-slate-600 mb-1">Setor</label>
            <select
              v-model="filters.sector"
              class="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-gov-blue focus:border-transparent"
            >
              <option value="">Todos</option>
              <option v-for="s in sectors" :key="s" :value="s">{{ s }}</option>
            </select>
          </div>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <!-- Filtro Data Início -->
          <div>
            <label class="block text-xs font-medium text-slate-600 mb-1">Data Início</label>
            <input
              v-model="filters.dateFrom"
              type="date"
              class="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-gov-blue focus:border-transparent"
            />
          </div>

          <!-- Filtro Data Fim -->
          <div>
            <label class="block text-xs font-medium text-slate-600 mb-1">Data Fim</label>
            <input
              v-model="filters.dateTo"
              type="date"
              class="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-gov-blue focus:border-transparent"
            />
          </div>

          <!-- Filtro Bairro -->
          <div>
            <label class="block text-xs font-medium text-slate-600 mb-1">Bairro</label>
            <input
              v-model="filters.neighborhood"
              type="text"
              placeholder="Nome do bairro..."
              class="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-gov-blue focus:border-transparent"
            />
          </div>
        </div>

        <!-- Botões de Ação -->
        <div class="flex gap-2 mt-4">
          <button
            type="button"
            class="px-4 py-2 bg-gov-blue text-white rounded-lg text-sm font-medium hover:bg-gov-dark transition-colors"
            @click="performSearch"
          >
            🔍 Buscar
          </button>
          <button
            type="button"
            class="px-4 py-2 border border-slate-300 text-slate-700 rounded-lg text-sm font-medium hover:bg-slate-50 transition-colors"
            @click="clearFilters"
          >
            Limpar Filtros
          </button>
        </div>
      </div>

      <!-- Tabela de Resultados -->
      <div class="flex-1 overflow-hidden flex flex-col bg-white rounded-lg shadow-sm border border-slate-200">
        <div v-if="loading" class="flex-1 flex items-center justify-center p-12">
          <span class="text-slate-500">Carregando...</span>
        </div>

        <div v-else-if="results.length === 0" class="flex-1 flex items-center justify-center p-12">
          <div class="text-center">
            <p class="text-slate-500 mb-2">Nenhuma manifestação encontrada.</p>
            <p class="text-xs text-slate-400">Tente ajustar os filtros de busca.</p>
          </div>
        </div>

        <div v-else class="flex-1 overflow-auto">
          <table class="w-full text-sm">
            <thead class="bg-slate-50 border-b border-slate-200 sticky top-0">
              <tr>
                <th class="px-4 py-3 text-left text-xs font-semibold text-slate-700 uppercase tracking-wider">
                  Protocolo
                </th>
                <th class="px-4 py-3 text-left text-xs font-semibold text-slate-700 uppercase tracking-wider">
                  Assunto (Resumo)
                </th>
                <th class="px-4 py-3 text-left text-xs font-semibold text-slate-700 uppercase tracking-wider">
                  Setor Atual
                </th>
                <th class="px-4 py-3 text-left text-xs font-semibold text-slate-700 uppercase tracking-wider">
                  Status
                </th>
                <th class="px-4 py-3 text-left text-xs font-semibold text-slate-700 uppercase tracking-wider">
                  Data
                </th>
                <th class="px-4 py-3 text-left text-xs font-semibold text-slate-700 uppercase tracking-wider">
                  Ações
                </th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-200">
              <tr
                v-for="item in results"
                :key="item.id"
                class="hover:bg-slate-50 transition-colors"
              >
                <td class="px-4 py-3">
                  <span class="font-mono font-semibold text-slate-800">{{ item.protocol }}</span>
                </td>
                <td class="px-4 py-3">
                  <div class="max-w-md">
                    <p class="text-slate-700 truncate" :title="item.description">
                      {{ item.nlp_summary || item.description?.substring(0, 100) || '—' }}
                    </p>
                    <p v-if="item.engagement_count > 1" class="text-xs text-amber-600 mt-1">
                      <Users :size="14" class="stroke-current inline" />
                      {{ item.engagement_count }} relatos agrupados
                    </p>
                  </div>
                </td>
                <td class="px-4 py-3">
                  <span class="text-slate-600">
                    {{ item.category_detail?.default_sector || item.category_name || '—' }}
                  </span>
                </td>
                <td class="px-4 py-3">
                  <span
                    class="inline-flex items-center px-2 py-1 rounded text-xs font-medium"
                    :class="statusBadgeClass(item.status)"
                  >
                    {{ item.status_display }}
                  </span>
                </td>
                <td class="px-4 py-3 text-slate-600">
                  {{ formatDate(item.created_at) }}
                </td>
                <td class="px-4 py-3">
                  <button
                    type="button"
                    class="text-gov-blue hover:text-gov-dark text-xs font-medium underline"
                    @click="viewDetail(item.id)"
                  >
                    Ver Detalhe
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Paginação -->
        <div v-if="results.length > 0 && (hasNext || hasPrevious)" class="px-4 py-3 border-t border-slate-200 flex items-center justify-between">
          <div class="text-xs text-slate-600">
            Mostrando {{ results.length }} resultado(s)
          </div>
          <div class="flex gap-2">
            <button
              v-if="hasPrevious"
              type="button"
              class="px-3 py-1 border border-slate-300 rounded text-xs text-slate-700 hover:bg-slate-50"
              @click="loadPrevious"
            >
              ← Anterior
            </button>
            <button
              v-if="hasNext"
              type="button"
              class="px-3 py-1 border border-slate-300 rounded text-xs text-slate-700 hover:bg-slate-50"
              @click="loadNext"
            >
              Próxima →
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Modal de Detalhe -->
    <div
      v-if="selectedDetail"
      class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
      @click.self="selectedDetail = null"
    >
      <div class="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        <div class="px-6 py-4 border-b border-slate-200 flex items-center justify-between">
          <h2 class="text-lg font-semibold text-slate-800">
            Detalhe: {{ selectedDetail.protocol }}
          </h2>
          <button
            type="button"
            class="text-slate-500 hover:text-slate-700"
            @click="selectedDetail = null"
          >
            <X :size="20" class="stroke-current" />
          </button>
        </div>
        <div class="flex-1 overflow-y-auto p-6">
          <div class="space-y-4">
            <div>
              <h3 class="text-sm font-semibold text-slate-700 mb-2">Descrição</h3>
              <p class="text-slate-600 whitespace-pre-wrap">{{ selectedDetail.description }}</p>
            </div>
            <div class="grid grid-cols-2 gap-4">
              <div>
                <h3 class="text-sm font-semibold text-slate-700 mb-2">Status</h3>
                <p class="text-slate-600">{{ selectedDetail.status_display }}</p>
              </div>
              <div>
                <h3 class="text-sm font-semibold text-slate-700 mb-2">Categoria</h3>
                <p class="text-slate-600">{{ selectedDetail.category_name || '—' }}</p>
              </div>
              <div>
                <h3 class="text-sm font-semibold text-slate-700 mb-2">Setor</h3>
                <p class="text-slate-600">{{ selectedDetail.category_detail?.default_sector || '—' }}</p>
              </div>
              <div>
                <h3 class="text-sm font-semibold text-slate-700 mb-2">Data de Criação</h3>
                <p class="text-slate-600">{{ formatDate(selectedDetail.created_at) }}</p>
              </div>
            </div>
            <div v-if="selectedDetail.location_address">
              <h3 class="text-sm font-semibold text-slate-700 mb-2">Localização</h3>
              <p class="text-slate-600">{{ selectedDetail.location_address }}</p>
            </div>
          </div>
        </div>
        <div class="px-6 py-4 border-t border-slate-200 flex justify-end">
          <button
            type="button"
            class="px-4 py-2 bg-slate-200 text-slate-700 rounded-lg text-sm font-medium hover:bg-slate-300"
            @click="selectedDetail = null"
          >
            Fechar
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Users, X } from '@/utils/icons'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import apiService from '@/services/api'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

const searchQuery = ref('')
const filters = ref({
  status: '',
  sector: '',
  dateFrom: '',
  dateTo: '',
  neighborhood: '',
})
const results = ref<any[]>([])
const loading = ref(false)
const selectedDetail = ref<any>(null)
const sectors = ref<string[]>([])
const hasNext = ref(false)
const hasPrevious = ref(false)
const nextUrl = ref<string | null>(null)
const previousUrl = ref<string | null>(null)

function statusBadgeClass(status: string): string {
  const classes: Record<string, string> = {
    waiting_triage: 'bg-blue-100 text-blue-800',
    in_analysis: 'bg-amber-100 text-amber-800',
    forwarded: 'bg-green-100 text-green-800',
    duplicate_forwarded: 'bg-purple-100 text-purple-800',
    resolved: 'bg-emerald-100 text-emerald-800',
    closed: 'bg-slate-100 text-slate-800',
  }
  return classes[status] || 'bg-slate-100 text-slate-800'
}

function formatDate(dateString: string): string {
  if (!dateString) return '—'
  const date = new Date(dateString)
  return date.toLocaleDateString('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

async function loadSectors() {
  try {
    const res = await apiService.get('/reports/categories/')
    const data = Array.isArray(res.data) ? res.data : res.data.results || []
    const uniqueSectors = new Set<string>()
    data.forEach((c: any) => {
      if (c.default_sector) uniqueSectors.add(c.default_sector)
    })
    sectors.value = Array.from(uniqueSectors).sort()
  } catch {
    sectors.value = []
  }
}

async function performSearch() {
  loading.value = true
  try {
    const params: Record<string, string> = {}
    
    if (searchQuery.value.trim()) {
      params.search = searchQuery.value.trim()
    }
    if (filters.value.status) {
      params.status = filters.value.status
    }
    if (filters.value.sector) {
      params.forwarded_sector = filters.value.sector
    }
    if (filters.value.dateFrom) {
      params.created_at__gte = filters.value.dateFrom
    }
    if (filters.value.dateTo) {
      params.created_at__lte = filters.value.dateTo
    }
    if (filters.value.neighborhood) {
      params.location_address__icontains = filters.value.neighborhood
    }
    
    params.ordering = '-created_at'
    
    const response = await apiService.get('/reports/manifestations/', { params })
    
    if (Array.isArray(response.data)) {
      results.value = response.data
      hasNext.value = false
      hasPrevious.value = false
    } else {
      results.value = response.data.results || []
      hasNext.value = !!response.data.next
      hasPrevious.value = !!response.data.previous
      nextUrl.value = response.data.next
      previousUrl.value = response.data.previous
    }
  } catch (e: any) {
    console.error('Erro ao buscar:', e)
    results.value = []
  } finally {
    loading.value = false
  }
}

async function loadNext() {
  if (!nextUrl.value) return
  loading.value = true
  try {
    const response = await apiService.get(nextUrl.value)
    if (Array.isArray(response.data)) {
      results.value = response.data
      hasNext.value = false
      hasPrevious.value = false
    } else {
      results.value = response.data.results || []
      hasNext.value = !!response.data.next
      hasPrevious.value = !!response.data.previous
      nextUrl.value = response.data.next
      previousUrl.value = response.data.previous
    }
  } catch (e: any) {
    console.error('Erro ao carregar próxima página:', e)
  } finally {
    loading.value = false
  }
}

async function loadPrevious() {
  if (!previousUrl.value) return
  loading.value = true
  try {
    const response = await apiService.get(previousUrl.value)
    if (Array.isArray(response.data)) {
      results.value = response.data
      hasNext.value = false
      hasPrevious.value = false
    } else {
      results.value = response.data.results || []
      hasNext.value = !!response.data.next
      hasPrevious.value = !!response.data.previous
      nextUrl.value = response.data.next
      previousUrl.value = response.data.previous
    }
  } catch (e: any) {
    console.error('Erro ao carregar página anterior:', e)
  } finally {
    loading.value = false
  }
}

async function viewDetail(id: string) {
  try {
    const response = await apiService.get(`/reports/manifestations/${id}/`)
    selectedDetail.value = response.data
  } catch (e: any) {
    console.error('Erro ao carregar detalhe:', e)
    alert('Erro ao carregar detalhes da manifestação.')
  }
}

function clearFilters() {
  searchQuery.value = ''
  filters.value = {
    status: '',
    sector: '',
    dateFrom: '',
    dateTo: '',
    neighborhood: '',
  }
  results.value = []
}

function logout() {
  auth.logout()
  router.push('/login')
}

onMounted(() => {
  loadSectors()
})
</script>
