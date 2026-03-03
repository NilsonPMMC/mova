import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import apiService from '@/services/api'

export interface EntradaItem {
  id: string
  protocol: string
  description: string
  nlp_summary: string | null
  engagement_count: number
  location_address?: string | null
  urgency_level?: number | null
}

export interface WorkOrderItem {
  id: string
  sector: string
  status: string
  status_display: string
  team_leader: string | null
  team_leader_name: string | null
  block_reason: string | null
  scheduled_date: string | null
  created_at: string
  manifestation_count: number
  technical_summary: string
  heat_count: number
  manifestations: Array<{
    id: string
    protocol: string
    description: string
    location_address: string | null
    engagement_count: number
    nlp_summary: string | null
    urgency_level?: number | null
    latitude?: number | null
    longitude?: number | null
  }>
}

export const useSectorBoardStore = defineStore('sector-board', () => {
  const sector = ref('')
  const entrada = ref<EntradaItem[]>([])
  const workOrders = ref<WorkOrderItem[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  const scheduled = computed(() =>
    workOrders.value
      .filter((wo) => wo.status === 'scheduled')
      .sort((a, b) => {
        // 1º Critério: engagement_count (decrescente)
        if (b.heat_count !== a.heat_count) return b.heat_count - a.heat_count
        // 2º Critério: urgency_level (decrescente) - se disponível
        const urgencyA = a.manifestations?.[0]?.urgency_level ?? 0
        const urgencyB = b.manifestations?.[0]?.urgency_level ?? 0
        return urgencyB - urgencyA
      })
  )
  const inProgress = computed(() =>
    workOrders.value
      .filter((wo) => wo.status === 'in_progress')
      .sort((a, b) => {
        // 1º Critério: engagement_count (decrescente)
        if (b.heat_count !== a.heat_count) return b.heat_count - a.heat_count
        // 2º Critério: urgency_level (decrescente)
        const urgencyA = a.manifestations?.[0]?.urgency_level ?? 0
        const urgencyB = b.manifestations?.[0]?.urgency_level ?? 0
        return urgencyB - urgencyA
      })
  )
  const blocked = computed(() =>
    workOrders.value.filter((wo) => wo.status === 'blocked')
  )
  const done = computed(() =>
    workOrders.value.filter((wo) => wo.status === 'done')
  )
  

  async function setSector(s: string) {
    sector.value = s
    await Promise.all([fetchEntrada(), fetchWorkOrders()])
  }

  async function fetchEntrada() {
    if (!sector.value) return
    try {
      const res = await apiService.get('/reports/manifestations/', {
        params: {
          forwarded_sector: sector.value,
          ordering: '-created_at',
        },
      })
      const data = Array.isArray(res.data) ? res.data : res.data.results ?? res.data
      const mapped = (data as any[]).map((m) => ({
        id: m.id,
        protocol: m.protocol,
        description: m.description || '',
        nlp_summary: m.nlp_summary || null,
        engagement_count: m.engagement_count ?? 1,
        location_address: m.location_address ?? null,
        urgency_level: m.urgency_level ?? null,
      }))
      // Ordenar por engagement_count (decrescente) e depois urgency_level (decrescente)
      entrada.value = mapped.sort((a, b) => {
        if (b.engagement_count !== a.engagement_count) return b.engagement_count - a.engagement_count
        const urgencyA = a.urgency_level ?? 0
        const urgencyB = b.urgency_level ?? 0
        return urgencyB - urgencyA
      })
    } catch (e: any) {
      error.value = e.response?.data?.detail || 'Erro ao carregar entrada.'
      entrada.value = []
    }
  }

  async function fetchWorkOrders() {
    if (!sector.value) return
    try {
      const res = await apiService.get('/reports/work-orders/', {
        params: { sector: sector.value },
      })
      const data = Array.isArray(res.data) ? res.data : res.data.results ?? res.data
      workOrders.value = (data as any[]).map(normalizeWorkOrder)
    } catch (e: any) {
      error.value = e.response?.data?.detail || 'Erro ao carregar OS.'
      workOrders.value = []
    }
  }

  function normalizeWorkOrder(wo: any): WorkOrderItem {
    return {
      id: wo.id,
      sector: wo.sector,
      status: wo.status,
      status_display: wo.status_display,
      team_leader: wo.team_leader,
      team_leader_name: wo.team_leader_name ?? null,
      block_reason: wo.block_reason ?? null,
      scheduled_date: wo.scheduled_date ?? null,
      created_at: wo.created_at,
      manifestation_count: wo.manifestation_count ?? 0,
      technical_summary: wo.technical_summary ?? '',
      heat_count: wo.heat_count ?? 0,
      manifestations: Array.isArray(wo.manifestations) ? wo.manifestations : [],
    }
  }

  async function createWorkOrder(manifestationIds: string[], scheduledDate?: string) {
    if (!sector.value || !manifestationIds.length) return
    loading.value = true
    try {
      await apiService.post('/reports/work-orders/', {
        sector: sector.value,
        manifestation_ids: manifestationIds,
        scheduled_date: scheduledDate || null,
      })
      await Promise.all([fetchEntrada(), fetchWorkOrders()])
    } catch (e: any) {
      throw new Error(e.response?.data?.detail || 'Erro ao criar OS.')
    } finally {
      loading.value = false
    }
  }

  async function updateWorkOrderStatus(
    id: string,
    status: string,
    blockReason?: string | null
  ) {
    try {
      const payload: any = { status }
      if (status === 'blocked' && blockReason != null) payload.block_reason = blockReason
      await apiService.patch(`/reports/work-orders/${id}/`, payload)
      await fetchWorkOrders()
    } catch (e: any) {
      throw new Error(e.response?.data?.detail || 'Erro ao atualizar status.')
    }
  }

  async function finishManifestation(
    manifestationId: string,
    solutionNote: string,
    solutionPhoto?: File | null
  ) {
    try {
      const formData = new FormData()
      formData.append('solution_note', solutionNote)
      if (solutionPhoto) {
        formData.append('solution_photo', solutionPhoto)
      }
      await apiService.post(`/reports/manifestations/${manifestationId}/finish/`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      })
      // Recarregar dados
      await Promise.all([fetchEntrada(), fetchWorkOrders()])
    } catch (e: any) {
      throw new Error(e.response?.data?.detail || 'Erro ao concluir manifestação.')
    }
  }

  return {
    sector,
    entrada,
    workOrders,
    scheduled,
    inProgress,
    blocked,
    done,
    loading,
    error,
    setSector,
    fetchEntrada,
    fetchWorkOrders,
    createWorkOrder,
    updateWorkOrderStatus,
    finishManifestation,
  }
})
