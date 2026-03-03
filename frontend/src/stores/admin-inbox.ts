import { defineStore } from 'pinia'
import { ref, computed, watch } from 'vue'
import apiService from '@/services/api'

export interface InboxItem {
  id: string
  protocol: string
  description: string
  status: string
  status_display: string
  category: string | null
  category_name: string | null
  citizen_name: string | null
  is_anonymous: boolean
  origin: string
  created_at: string
  has_nlp_analysis: boolean
  engagement_count: number
  urgency_level: number | null
  sentiment_score: number | null
  potential_duplicate_id: string | null
}

export type InboxFilter = 'all_open' | 'waiting_triage' | 'in_analysis' | 'resolved'

export const useAdminInboxStore = defineStore('admin-inbox', () => {
  const list = ref<InboxItem[]>([])
  const selectedId = ref<string | null>(null)
  const selectedDetail = ref<any>(null)
  const filter = ref<InboxFilter>('all_open')
  const loading = ref(false)
  const detailLoading = ref(false)
  const error = ref<string | null>(null)

  const selectedItem = computed(() =>
    selectedId.value ? list.value.find((i) => i.id === selectedId.value) ?? null : null
  )

  const sortedList = computed(() => {
    let items = [...list.value]
    if (filter.value === 'all_open') {
      items = items.filter((i) => i.status !== 'resolved' && i.status !== 'closed')
    }
    return items.sort((a, b) => {
      const urgencyA = a.urgency_level ?? 0
      const urgencyB = b.urgency_level ?? 0
      if (urgencyB !== urgencyA) return urgencyB - urgencyA
      const clusterA = a.potential_duplicate_id || a.engagement_count > 1 ? 1 : 0
      const clusterB = b.potential_duplicate_id || b.engagement_count > 1 ? 1 : 0
      if (clusterB !== clusterA) return clusterB - clusterA
      return new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
    })
  })

  async function fetchList() {
    loading.value = true
    error.value = null
    const previousSelectedId = selectedId.value
    
    try {
      const params: Record<string, string> = {
        only_primary: 'true', // Filtrar apenas manifestações principais (sem duplicatas)
      }
      if (filter.value === 'waiting_triage') params.status = 'waiting_triage'
      else if (filter.value === 'in_analysis') params.status = 'in_analysis'
      else if (filter.value === 'resolved') params.status = 'resolved'
      else {
        params.ordering = '-created_at'
      }
      const response = await apiService.get('/reports/manifestations/', { params })
      const newList = Array.isArray(response.data) ? response.data : response.data.results ?? response.data
      list.value = newList
      
      // Aguardar um tick para garantir que sortedList computed seja atualizado
      await new Promise(resolve => setTimeout(resolve, 0))
      
      // REGRA DE OURO: Sincronizar seleção após carregar lista
      // Usar sortedList computed que já aplica os filtros corretamente
      const currentSortedList = sortedList.value
      
      const currentSelectedExists = previousSelectedId && currentSortedList.some((item: InboxItem) => item.id === previousSelectedId)
      
      if (!currentSelectedExists) {
        // 2. Se não existir: selecionar o primeiro item da lista filtrada
        if (currentSortedList.length > 0) {
          const firstId = currentSortedList[0].id
          selectedId.value = firstId
          await fetchDetail(firstId)
        } else {
          // 3. Se a lista estiver vazia: limpar o detalhe
          selectedId.value = null
          selectedDetail.value = null
        }
      } else {
        // Se o item selecionado ainda existe, apenas atualizar o detalhe se necessário
        // (para garantir que está sincronizado com a lista)
        if (previousSelectedId) {
          await fetchDetail(previousSelectedId)
        }
      }
    } catch (e: any) {
      error.value = e.response?.data?.detail || 'Erro ao carregar lista.'
      list.value = []
      // Em caso de erro, limpar seleção
      selectedId.value = null
      selectedDetail.value = null
    } finally {
      loading.value = false
    }
  }

  async function fetchDetail(id: string) {
    if (!id) {
      selectedDetail.value = null
      return
    }
    detailLoading.value = true
    selectedId.value = id
    try {
      const response = await apiService.get(`/reports/manifestations/${id}/`)
      selectedDetail.value = response.data
    } catch (e: any) {
      error.value = e.response?.data?.detail || 'Erro ao carregar detalhes.'
      selectedDetail.value = null
    } finally {
      detailLoading.value = false
    }
  }

  async function confirmAndDispatch(categoryId: string | null, sector?: string | null) {
    if (!selectedDetail.value) return
    const id = selectedDetail.value.id
    try {
      const payload: any = {
        category: categoryId,
        status: 'forwarded', // Despachar diretamente (FORWARDED)
      }
      if (sector) {
        payload.sector = sector
      }
      await apiService.patch(`/reports/manifestations/${id}/`, payload)
      await fetchList() // Atualiza lista (remove o item)
      selectedId.value = null
      selectedDetail.value = null
    } catch (e: any) {
      throw new Error(e.response?.data?.detail || 'Erro ao confirmar.')
    }
  }

  async function updateCategory(categoryId: string | null) {
    if (!selectedDetail.value) return
    const id = selectedDetail.value.id
    try {
      await apiService.patch(`/reports/manifestations/${id}/`, { category: categoryId })
      await fetchDetail(id)
      await fetchList()
    } catch (e: any) {
      throw new Error(e.response?.data?.detail || 'Erro ao atualizar categoria.')
    }
  }

  /** Encaminha para setor (categoria) e marca status como encaminhado */
  async function forwardToCategory(categoryId: string | null) {
    if (!selectedDetail.value || !categoryId) return
    const id = selectedDetail.value.id
    try {
      await apiService.patch(`/reports/manifestations/${id}/`, {
        category: categoryId,
        status: 'forwarded',
      })
      await fetchList() // Atualiza lista (remove o item)
      selectedId.value = null
      selectedDetail.value = null
    } catch (e: any) {
      throw new Error(e.response?.data?.detail || 'Erro ao encaminhar.')
    }
  }

  async function updateUrgency(urgencyLevel: number) {
    if (!selectedDetail.value) return
    const id = selectedDetail.value.id
    try {
      // Atualizar urgência via NLP analysis
      const nlpId = selectedDetail.value.nlp_analysis?.id
      if (nlpId) {
        await apiService.patch(`/intelligence/nlp-analyses/${nlpId}/`, {
          urgency_level: urgencyLevel,
        })
      }
      await fetchDetail(id)
    } catch (e: any) {
      throw new Error(e.response?.data?.detail || 'Erro ao atualizar urgência.')
    }
  }

  async function markAsDuplicate(targetManifestationId: string) {
    if (!selectedDetail.value) return
    const id = selectedDetail.value.id
    try {
      await apiService.patch(`/reports/manifestations/${id}/`, {
        related_group: targetManifestationId,
        is_primary: false,
      })
      await fetchDetail(id)
      await fetchList()
    } catch (e: any) {
      throw new Error(e.response?.data?.detail || 'Erro ao marcar como duplicada.')
    }
  }

  async function setFilter(f: InboxFilter) {
    filter.value = f
    // Ao mudar o filtro, sempre recarregar a lista (que já sincroniza a seleção)
    await fetchList()
  }

  // Watch para garantir sincronização quando sortedList muda
  watch(
    () => sortedList.value,
    (newList) => {
      // Se não há item selecionado e há itens na lista, selecionar o primeiro
      if (!selectedId.value && newList.length > 0) {
        selectedId.value = newList[0].id
        fetchDetail(newList[0].id)
      }
      // Se o item selecionado não existe mais na lista filtrada, selecionar o primeiro
      else if (selectedId.value && !newList.some((item) => item.id === selectedId.value)) {
        if (newList.length > 0) {
          selectedId.value = newList[0].id
          fetchDetail(newList[0].id)
        } else {
          selectedId.value = null
          selectedDetail.value = null
        }
      }
    },
    { immediate: false }
  )

  return {
    list,
    sortedList,
    selectedId,
    selectedItem,
    selectedDetail,
    filter,
    loading,
    detailLoading,
    error,
    fetchList,
    fetchDetail,
    confirmAndDispatch,
    updateCategory,
    forwardToCategory,
    updateUrgency,
    markAsDuplicate,
    setFilter,
  }
})
