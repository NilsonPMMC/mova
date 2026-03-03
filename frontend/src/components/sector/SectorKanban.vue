<template>
  <div class="flex gap-4 overflow-x-auto pb-4" style="min-height: calc(100vh - 180px);">
    <!-- Entrada -->
    <div class="w-72 shrink-0 rounded-lg bg-slate-100 border border-slate-200 p-3">
      <h3 class="text-sm font-semibold text-slate-700 mb-2">Entrada</h3>
      <p class="text-xs text-slate-500 mb-3">O que a Ouvidoria encaminhou</p>
      <div class="space-y-2 overflow-y-auto" style="max-height: calc(100vh - 240px);">
        <EntradaCard
          v-for="item in store.entrada"
          :key="item.id"
          :item="item"
          @create-order="onCreateOrder(item.id)"
        />
      </div>
    </div>

    <!-- Cronograma -->
    <div
      class="w-72 shrink-0 rounded-lg bg-blue-50 border border-blue-200 p-3"
      style="min-height: calc(100vh - 180px);"
      data-status="scheduled"
      @dragover="onDragOver"
      @drop="onDrop"
    >
      <h3 class="text-sm font-semibold text-slate-700 mb-2">Cronograma</h3>
      <p class="text-xs text-slate-500 mb-3">Esta semana</p>
      <div class="space-y-2 overflow-y-auto" style="min-height: calc(100vh - 240px); max-height: calc(100vh - 240px);">
        <div
          v-for="element in store.scheduled"
          :key="element.id"
          :data-id="element.id"
          draggable="true"
          class="cursor-grab active:cursor-grabbing"
          @dragstart="onDragStart($event, element.id, 'scheduled')"
        >
          <WorkOrderCard :item="element" @open-dossier="openDossier" @open-detail="openTaskDetail" />
        </div>
      </div>
    </div>

    <!-- Em Rua -->
    <div
      class="w-72 shrink-0 rounded-lg bg-emerald-50 border border-emerald-200 p-3"
      style="min-height: calc(100vh - 180px);"
      data-status="in_progress"
      @dragover="onDragOver"
      @drop="onDrop"
    >
      <h3 class="text-sm font-semibold text-slate-700 mb-2">Em Rua</h3>
      <p class="text-xs text-slate-500 mb-3">Equipes trabalhando</p>
      <div class="space-y-2 overflow-y-auto" style="min-height: calc(100vh - 240px); max-height: calc(100vh - 240px);">
        <div
          v-for="element in store.inProgress"
          :key="element.id"
          :data-id="element.id"
          draggable="true"
          class="cursor-grab active:cursor-grabbing"
          @dragstart="onDragStart($event, element.id, 'in_progress')"
        >
          <WorkOrderCard :item="element" @open-dossier="openDossier" @open-detail="openTaskDetail" />
        </div>
      </div>
    </div>

    <!-- Bloqueado -->
    <div
      class="w-72 shrink-0 rounded-lg bg-red-50 border border-red-200 p-3"
      style="min-height: calc(100vh - 180px);"
      data-status="blocked"
      @dragover="onDragOver"
      @drop="onDrop"
    >
      <h3 class="text-sm font-semibold text-slate-700 mb-2">Bloqueado</h3>
      <p class="text-xs text-slate-500 mb-3">Não é comigo / Falta material</p>
      <div class="space-y-2 overflow-y-auto" style="min-height: calc(100vh - 240px); max-height: calc(100vh - 240px);">
        <div
          v-for="element in store.blocked"
          :key="element.id"
          :data-id="element.id"
          draggable="true"
          class="cursor-grab active:cursor-grabbing"
          @dragstart="onDragStart($event, element.id, 'blocked')"
        >
          <WorkOrderCard :item="element" @open-dossier="openDossier" @open-detail="openTaskDetail" />
        </div>
      </div>
    </div>

    <!-- Concluído -->
    <div
      class="w-72 shrink-0 rounded-lg bg-emerald-50 border border-emerald-200 p-3"
      style="min-height: calc(100vh - 180px);"
      data-status="done"
      @dragover="onDragOver"
      @drop="onDrop"
    >
      <div class="flex items-center justify-between mb-2">
        <h3 class="text-sm font-semibold text-slate-700">Concluído</h3>
        <span class="inline-flex items-center gap-1 text-xs text-slate-500">
          <Lock :size="14" class="stroke-current" />
          Trava
        </span>
      </div>
      <p class="text-xs text-slate-500 mb-3">Finalizados (não editáveis)</p>
      <div class="space-y-2 overflow-y-auto" style="min-height: calc(100vh - 240px); max-height: calc(100vh - 240px);">
        <div
          v-for="element in store.done"
          :key="element.id"
          :data-id="element.id"
          class="opacity-75 cursor-not-allowed"
        >
          <WorkOrderCard :item="element" @open-dossier="openDossier" @open-detail="openTaskDetail" />
        </div>
      </div>
    </div>
  </div>

  <BlockReasonModal
    v-if="showBlockModal"
    :work-order-id="pendingBlockId"
    @confirm="onBlockConfirm"
    @cancel="showBlockModal = false; pendingBlockId = null; store.fetchWorkOrders()"
  />
  <DossierModal
    v-if="dossierItem"
    :item="dossierItem"
    @close="dossierItem = null"
  />
  <TaskDetailModal
    v-if="taskDetailItem"
    :item="taskDetailItem"
    @close="taskDetailItem = null"
  />
  <FinishTaskModal
    v-if="showFinishModal && pendingFinishItem"
    :item="pendingFinishItem"
    @confirm="onFinishConfirm"
    @cancel="showFinishModal = false; pendingFinishItem = null"
  />
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { Lock } from '@/utils/icons'
import EntradaCard from './EntradaCard.vue'
import WorkOrderCard from './WorkOrderCard.vue'
import BlockReasonModal from './BlockReasonModal.vue'
import DossierModal from './DossierModal.vue'
import TaskDetailModal from './TaskDetailModal.vue'
import FinishTaskModal from './FinishTaskModal.vue'
import { useSectorBoardStore } from '@/stores/sector-board'
import type { WorkOrderItem } from '@/stores/sector-board'

const store = useSectorBoardStore()

const showBlockModal = ref(false)
const pendingBlockId = ref<string | null>(null)
const dossierItem = ref<WorkOrderItem | null>(null)
const taskDetailItem = ref<WorkOrderItem | null>(null)
const showFinishModal = ref(false)
const pendingFinishItem = ref<WorkOrderItem | null>(null)
const draggedFromStatus = ref<string | null>(null)

function onCreateOrder(manifestationId: string) {
  store.createWorkOrder([manifestationId]).catch((e) => alert(e.message))
}

function onDragStart(evt: DragEvent, id: string, fromStatus: string) {
  if (evt.dataTransfer) {
    evt.dataTransfer.setData('text/plain', id)
    evt.dataTransfer.effectAllowed = 'move'
    draggedFromStatus.value = fromStatus
  }
}

function onDragOver(evt: DragEvent) {
  evt.preventDefault()
  if (evt.dataTransfer) evt.dataTransfer.dropEffect = 'move'
}

function onDrop(evt: DragEvent) {
  evt.preventDefault()
  const id = evt.dataTransfer?.getData('text/plain')
  if (!id) return
  const target = (evt.currentTarget as HTMLElement)?.closest?.('[data-status]') as HTMLElement
  const targetStatus = target?.dataset?.status
  if (!targetStatus) return
  
  // Trava de conclusão: se destino for "done", abrir modal de conclusão
  // NÃO atualizar visualmente até confirmar no modal
  if (targetStatus === 'done') {
    const workOrder = store.workOrders.find((wo) => wo.id === id)
    if (workOrder) {
      pendingFinishItem.value = workOrder
      showFinishModal.value = true
      draggedFromStatus.value = null
    }
    return
  }
  
  if (targetStatus === 'blocked') {
    pendingBlockId.value = id
    showBlockModal.value = true
    draggedFromStatus.value = null
    return
  }
  
  // Outros status: atualizar imediatamente
  store.updateWorkOrderStatus(id, targetStatus).catch((e) => {
    alert(e.message)
    // Em caso de erro, recarregar para restaurar estado visual
    store.fetchWorkOrders()
  })
  draggedFromStatus.value = null
}

function onBlockConfirm(reason: string) {
  if (!pendingBlockId.value) return
  store.updateWorkOrderStatus(pendingBlockId.value, 'blocked', reason).then(() => {
    showBlockModal.value = false
    pendingBlockId.value = null
  }).catch((e) => alert(e.message))
}

function openDossier(item: WorkOrderItem) {
  dossierItem.value = item
}

function openTaskDetail(item: WorkOrderItem) {
  taskDetailItem.value = item
}

async function onFinishConfirm(solutionNote: string, solutionPhoto?: File | null) {
  if (!pendingFinishItem.value) return
  
  try {
    // Concluir todas as manifestações da OS
    const manifestationIds = pendingFinishItem.value.manifestations.map((m) => m.id)
    
    // Se for cluster (pai), concluir apenas a pai (o backend resolve as filhas)
    const parentManifestationId = manifestationIds[0] // Assumindo que a primeira é a pai
    
    await store.finishManifestation(parentManifestationId, solutionNote, solutionPhoto)
    
    // Atualizar status da OS para done (isso vai atualizar o visual automaticamente)
    await store.updateWorkOrderStatus(pendingFinishItem.value.id, 'done')
    
    showFinishModal.value = false
    pendingFinishItem.value = null
  } catch (e: any) {
    alert(e.message || 'Erro ao concluir manifestação.')
    // Em caso de erro, recarregar para restaurar estado visual
    await store.fetchWorkOrders()
  }
}
</script>
