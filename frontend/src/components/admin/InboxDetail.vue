<template>
  <div class="h-full flex flex-col bg-white">
    <div v-if="store.detailLoading" class="flex-1 flex items-center justify-center p-12">
      <span class="text-slate-500">Carregando...</span>
    </div>

    <template v-else-if="detail">
      <div class="flex-1 overflow-y-auto">
        <!-- Seção 1: Validação da IA -->
        <div class="p-6 border-b border-slate-200 bg-slate-50">
          <h3 class="text-sm font-semibold text-slate-700 mb-3">Validação da IA</h3>
          <div v-if="!showCategoryCorrect">
            <p class="text-slate-700 mb-4">
              A IA classificou como <strong>{{ categoryName }}</strong> com Urgência <strong>{{ urgencyLabel }}</strong>. Confere?
            </p>
            <div class="flex gap-3">
              <button
                type="button"
                class="inline-flex items-center gap-2 px-4 py-2 rounded-lg font-medium bg-emerald-600 text-white hover:bg-emerald-700 transition-colors"
                @click="handleConfirmAndDispatch"
              >
                <CheckCircle2 :size="16" class="stroke-current" />
                Confirmar & Despachar
              </button>
              <button
                type="button"
                class="inline-flex items-center gap-2 px-4 py-2 rounded-lg font-medium border border-slate-300 text-slate-700 hover:bg-slate-100 transition-colors"
                @click="showCategoryCorrect = true"
              >
                <Edit :size="16" class="stroke-current" />
                Corrigir
              </button>
            </div>
          </div>
          
          <!-- Modo Corrigir: Formulário Inline -->
          <div v-else class="space-y-4 p-4 bg-white rounded-lg border-2 border-amber-300">
            <h4 class="text-sm font-semibold text-slate-800">Ajuste Manual</h4>
            
            <div>
              <label class="block text-xs font-medium text-slate-600 mb-2">Categoria</label>
              <select
                v-model="selectedCategoryId"
                class="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm"
              >
                <option value="">Selecione a categoria</option>
                <option v-for="c in categories" :key="c.id" :value="c.id">{{ c.name }}</option>
              </select>
            </div>
            
            <div>
              <label class="block text-xs font-medium text-slate-600 mb-2">
                Urgência: <strong>{{ urgencyLabels[selectedUrgency] }}</strong>
              </label>
              <div class="flex items-center gap-3">
                <input
                  v-model.number="selectedUrgency"
                  type="range"
                  min="1"
                  max="5"
                  step="1"
                  class="flex-1 h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-gov-blue"
                />
                <div class="flex gap-1 text-xs text-slate-500 min-w-[200px]">
                  <span :class="selectedUrgency === 1 ? 'font-semibold text-slate-800' : ''">Baixa</span>
                  <span :class="selectedUrgency === 2 ? 'font-semibold text-slate-800' : ''">Média</span>
                  <span :class="selectedUrgency === 3 ? 'font-semibold text-slate-800' : ''">Alta</span>
                  <span :class="selectedUrgency === 4 ? 'font-semibold text-slate-800' : ''">Crítica</span>
                </div>
              </div>
            </div>
            
            <div class="flex gap-2">
              <button
                type="button"
                class="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-emerald-600 text-white text-sm font-medium hover:bg-emerald-700 transition-colors"
                @click="handleSaveAndDispatch"
              >
                <Save :size="16" class="stroke-current" />
                Salvar e Despachar
              </button>
              <button
                type="button"
                class="px-4 py-2 rounded-lg border border-slate-300 text-slate-700 text-sm font-medium hover:bg-slate-100 transition-colors"
                @click="showCategoryCorrect = false"
              >
                Cancelar
              </button>
            </div>
          </div>
        </div>

        <!-- Seção 1.5: Avaliação do Cidadão (se resolvida e com pesquisa) -->
        <div
          v-if="detail.status === 'resolved' && detail.satisfaction_survey"
          class="p-6 border-b border-slate-200"
          :class="detail.satisfaction_survey.rating < 3 ? 'bg-red-50 border-red-300' : 'bg-emerald-50 border-emerald-200'"
        >
          <h3 class="inline-flex items-center gap-2 text-sm font-semibold text-slate-700 mb-3">
            <BarChart3 :size="16" class="stroke-current" />
            Avaliação do Cidadão
            <span v-if="detail.satisfaction_survey.rating < 3" class="inline-flex items-center gap-1 text-red-600 ml-2">
              <AlertTriangle :size="14" class="stroke-current" />
              Atenção: Nota Baixa
            </span>
          </h3>
          <div class="space-y-3">
            <div class="flex items-center gap-2">
              <span class="text-sm font-medium text-slate-700">Nota:</span>
              <div class="flex gap-0.5">
                <Star
                  v-for="i in 5"
                  :key="i"
                  :size="18"
                  :class="i <= detail.satisfaction_survey.rating ? 'fill-yellow-400 text-yellow-400' : 'text-slate-300'"
                  class="stroke-current"
                />
              </div>
              <span class="text-sm text-slate-600">({{ detail.satisfaction_survey.rating }}/5)</span>
            </div>
            <div v-if="detail.satisfaction_survey.comment" class="p-3 bg-white rounded-lg border border-slate-200">
              <p class="text-sm text-slate-700 whitespace-pre-wrap">{{ detail.satisfaction_survey.comment }}</p>
            </div>
          </div>
        </div>

        <!-- Seção 2: Contexto (Abas) -->
        <div class="p-6 border-b border-slate-200">
          <div class="flex gap-2 border-b border-slate-200 mb-4">
            <button
              v-for="tab in tabs"
              :key="tab.id"
              type="button"
              class="px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors"
              :class="activeTab === tab.id ? 'border-gov-blue text-gov-blue' : 'border-transparent text-slate-600 hover:text-slate-800'"
              @click="activeTab = tab.id"
            >
              {{ tab.label }}
            </button>
          </div>

          <div v-show="activeTab === 'relato'" class="space-y-4">
            <p class="text-slate-700 whitespace-pre-wrap">{{ detail.description }}</p>
            <div v-if="detail.attachments?.length" class="grid grid-cols-3 gap-2">
              <a
                v-for="att in detail.attachments"
                :key="att.id"
                :href="att.file_url || getMediaUrl(att.file)"
                target="_blank"
                class="block rounded-lg border border-slate-200 overflow-hidden hover:opacity-90"
              >
                <img
                  v-if="att.file_type === 'IMAGE'"
                  :src="att.file_url || getMediaUrl(att.file)"
                  :alt="att.filename"
                  class="w-full h-24 object-cover"
                />
                <div v-else class="w-full h-24 bg-slate-100 flex items-center justify-center text-slate-500 text-xs">
                  PDF/Doc
                </div>
                <p class="p-2 text-xs text-slate-600 truncate">{{ att.filename }}</p>
              </a>
            </div>
          </div>

          <div v-show="activeTab === 'mapa'" class="h-64 rounded-lg border border-slate-200 overflow-hidden bg-slate-100">
            <iframe
              v-if="hasCoords && osmEmbedUrl"
              :src="osmEmbedUrl"
              class="w-full h-full border-0"
              title="Localização no mapa"
            />
            <p v-else class="p-4 text-sm text-slate-500">Sem localização informada.</p>
          </div>

          <div v-show="activeTab === 'cidadao'" class="space-y-2">
            <p><span class="font-medium text-slate-700">Nome:</span> {{ detail.citizen_name || 'Anônimo' }}</p>
            <p v-if="detail.engagement_count" class="text-sm text-slate-600">
              Histórico: {{ detail.engagement_count }} manifestação(ões) relacionada(s).
            </p>
          </div>

          <!-- Nova Aba: Relatos Agrupados -->
          <div v-show="activeTab === 'agrupados'" class="space-y-3">
            <div v-if="relatedManifestations.length === 0" class="text-sm text-slate-500 py-4">
              Nenhum relato agrupado encontrado.
            </div>
            <div
              v-for="rel in relatedManifestations"
              :key="rel.id"
              class="p-4 bg-slate-50 rounded-lg border border-slate-200"
            >
              <div class="flex items-start justify-between mb-2">
                <span class="font-mono text-xs font-semibold text-slate-600">{{ rel.protocol }}</span>
                <span class="text-xs text-slate-500">{{ formatDate(rel.created_at) }}</span>
              </div>
              <p class="text-sm text-slate-700 whitespace-pre-wrap">{{ rel.description }}</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Seção 3: Rodapé fixo - Apenas dropdown de setor (sem botão redundante) -->
      <div class="p-4 border-t border-slate-200 bg-slate-50 shrink-0">
        <div class="flex flex-wrap gap-3 items-end">
          <div class="flex-1 min-w-[200px]">
            <label class="block text-xs font-medium text-slate-600 mb-1">Resposta (interno / externo)</label>
            <textarea
              v-model="replyText"
              rows="2"
              class="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm"
              placeholder="Digite sua nota..."
            />
          </div>
          <div class="flex gap-2">
            <div>
              <label class="block text-xs font-medium text-slate-600 mb-1">Ajustar setor manualmente</label>
              <select
                v-model="forwardCategoryId"
                class="border border-slate-300 rounded-lg px-3 py-2 text-sm min-w-[180px]"
              >
                <option value="">Selecione...</option>
                <option v-for="c in categories" :key="c.id" :value="c.id">
                  {{ c.name }}{{ c.default_sector ? ` (${c.default_sector})` : '' }}
                </option>
              </select>
            </div>
            <button
              v-if="forwardCategoryId"
              type="button"
              class="px-4 py-2 rounded-lg bg-gov-blue text-white text-sm font-medium hover:bg-gov-dark self-end"
              @click="forwardToCategory"
            >
              Aplicar Setor
            </button>
            <button
              v-if="detail.potential_duplicate_id"
              type="button"
              class="px-4 py-2 rounded-lg border border-amber-500 text-amber-700 text-sm font-medium hover:bg-amber-50 self-end"
              @click="markAsDuplicate"
            >
              Marcar como Duplicada
            </button>
          </div>
        </div>
      </div>
    </template>

    <div v-else class="flex-1 flex items-center justify-center p-12 text-slate-500">
      Selecione uma manifestação na lista.
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { CheckCircle2, Edit, Save, BarChart3, AlertTriangle, Star } from '@/utils/icons'
import { useAdminInboxStore } from '@/stores/admin-inbox'
import apiService from '@/services/api'

const store = useAdminInboxStore()
const detail = computed(() => store.selectedDetail)

const activeTab = ref<'relato' | 'mapa' | 'cidadao' | 'agrupados'>('relato')
const tabs = computed(() => {
  const base: { id: 'relato' | 'mapa' | 'cidadao' | 'agrupados'; label: string }[] = [
    { id: 'relato', label: 'Relato' },
    { id: 'mapa', label: 'Mapa' },
    { id: 'cidadao', label: 'Cidadão' },
  ]
  if (relatedManifestations.value.length > 0) {
    base.push({ id: 'agrupados', label: `Relatos Agrupados (${relatedManifestations.value.length})` })
  }
  return base
})

const showCategoryCorrect = ref(false)
const selectedCategoryId = ref('')
const selectedUrgency = ref(3)
const categories = ref<{ id: string; name: string; default_sector?: string }[]>([])
const replyText = ref('')
const forwardCategoryId = ref('')
const relatedManifestations = ref<any[]>([])

const urgencyLabels: Record<number, string> = {
  1: 'Muito Baixa',
  2: 'Baixa',
  3: 'Média',
  4: 'Alta',
  5: 'Crítica',
}

const osmEmbedUrl = computed(() => {
  const lat = detail.value?.latitude
  const lng = detail.value?.longitude
  if (lat == null || lng == null) return ''
  const n = Number(lat)
  const e = Number(lng)
  const d = 0.01
  const bbox = [e - d, n - d, e + d, n + d].join(',')
  return `https://www.openstreetmap.org/export/embed.html?bbox=${encodeURIComponent(bbox)}&layer=mapnik&marker=${n},${e}`
})

const categoryName = computed(() => {
  const d = detail.value
  if (!d) return '—'
  if (d.category_detail?.name) return d.category_detail.name
  return d.nlp_analysis?.suggested_category_name || '—'
})

const urgencyLabel = computed(() => {
  const n = detail.value?.nlp_analysis?.urgency_level ?? 3
  return urgencyLabels[n] || 'Média'
})

const hasCoords = computed(() => {
  const d = detail.value
  return d?.latitude != null && d?.longitude != null
})

const suggestedCategoryId = computed(() => {
  const d = detail.value
  return d?.category_detail?.id ?? d?.nlp_analysis?.suggested_category ?? null
})

const apiOrigin = (() => {
  try {
    const base = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'
    return new URL(base).origin
  } catch {
    return 'http://localhost:8000'
  }
})()

function getMediaUrl(url: string | undefined): string {
  if (!url) return ''
  if (url.startsWith('http')) return url
  return `${apiOrigin}${url.startsWith('/') ? url : `/${url}`}`
}

function formatDate(dateString: string): string {
  if (!dateString) return ''
  const date = new Date(dateString)
  return date.toLocaleDateString('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

async function loadCategories() {
  try {
    const res = await apiService.get('/reports/categories/')
    const data = Array.isArray(res.data) ? res.data : res.data.results || []
    categories.value = data.map((c: any) => ({
      id: String(c.id),
      name: c.name,
      default_sector: c.default_sector || undefined,
    }))
  } catch {
    categories.value = []
  }
}

function loadRelatedManifestations() {
  if (!detail.value) {
    relatedManifestations.value = []
    return
  }
  // Os dados já vêm do backend no detail.value.related_manifestations
  relatedManifestations.value = detail.value.related_manifestations || []
}

watch(
  () => detail.value?.id,
  () => {
    const suggestedId = suggestedCategoryId.value
    if (suggestedId) forwardCategoryId.value = String(suggestedId)
    else forwardCategoryId.value = ''
    
    // Resetar modo corrigir
    showCategoryCorrect.value = false
    selectedCategoryId.value = ''
    selectedUrgency.value = detail.value?.nlp_analysis?.urgency_level ?? 3
    
    // Carregar relatos relacionados
    loadRelatedManifestations()
  },
  { immediate: true }
)

async function handleConfirmAndDispatch() {
  const catId = detail.value?.category_detail?.id || detail.value?.nlp_analysis?.suggested_category || detail.value?.category
  const sector = detail.value?.category_detail?.default_sector
  try {
    await store.confirmAndDispatch(catId ?? null, sector)
    showCategoryCorrect.value = false
  } catch (e: any) {
    alert(e?.message || 'Erro ao confirmar.')
  }
}

async function handleSaveAndDispatch() {
  try {
    // Atualizar categoria se mudou
    if (selectedCategoryId.value) {
      await store.updateCategory(selectedCategoryId.value || null)
    }
    
    // Atualizar urgência se mudou
    const currentUrgency = detail.value?.nlp_analysis?.urgency_level ?? 3
    if (selectedUrgency.value !== currentUrgency) {
      await store.updateUrgency(selectedUrgency.value)
    }
    
    // Despachar
    const catId = selectedCategoryId.value || detail.value?.category_detail?.id || detail.value?.nlp_analysis?.suggested_category || detail.value?.category
    const sector = categories.value.find((c) => c.id === selectedCategoryId.value)?.default_sector || detail.value?.category_detail?.default_sector
    await store.confirmAndDispatch(catId ?? null, sector)
    
    showCategoryCorrect.value = false
  } catch (e: any) {
    alert(e?.message || 'Erro ao salvar.')
  }
}

async function forwardToCategory() {
  if (!forwardCategoryId.value) return
  try {
    await store.forwardToCategory(forwardCategoryId.value)
  } catch (e: any) {
    alert(e?.message || 'Erro ao encaminhar.')
  }
}

async function markAsDuplicate() {
  const targetId = detail.value?.potential_duplicate_id
  if (!targetId) return
  try {
    await store.markAsDuplicate(targetId)
  } catch (e: any) {
    alert(e?.message || 'Erro ao marcar duplicata.')
  }
}

onMounted(() => {
  loadCategories()
})
</script>
