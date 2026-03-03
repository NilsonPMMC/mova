<template>
  <div
    class="rounded-lg border border-slate-200 bg-white p-3 shadow-sm hover:shadow transition-shadow cursor-grab active:cursor-grabbing"
  >
    <div class="flex items-start justify-between gap-2">
      <div class="min-w-0 flex-1">
        <div class="flex items-center gap-2 flex-wrap mb-1">
          <span
            class="text-xs font-medium px-1.5 py-0.5 rounded"
            :class="item.heat_count > 5 ? 'text-red-600 bg-red-50 font-bold' : 'text-amber-600 bg-amber-50'"
          >
            {{ item.heat_count }} afetados
          </span>
          <span v-if="item.manifestation_count > 1" class="text-xs text-slate-500">
            Cluster: {{ item.manifestation_count }} manifestações
          </span>
        </div>
        <p class="text-sm text-slate-700 line-clamp-2">{{ item.technical_summary || 'Sem resumo técnico' }}</p>
        <p v-if="item.team_leader_name" class="text-xs text-slate-500 mt-1">{{ item.team_leader_name }}</p>
      </div>
    </div>
    <div class="mt-2 flex gap-1">
      <button
        type="button"
        class="text-xs px-2 py-1 rounded border border-slate-200 text-slate-600 hover:bg-slate-50"
        @click.stop="emit('open-detail', item)"
      >
        Ver Detalhes
      </button>
      <button
        type="button"
        class="text-xs px-2 py-1 rounded border border-slate-200 text-slate-600 hover:bg-slate-50"
        @click.stop="emit('open-dossier', item)"
      >
        Dossiê
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { WorkOrderItem } from '@/stores/sector-board'

defineProps<{ item: WorkOrderItem }>()
const emit = defineEmits<{
  (e: 'open-dossier', item: WorkOrderItem): void
  (e: 'open-detail', item: WorkOrderItem): void
}>()
</script>
