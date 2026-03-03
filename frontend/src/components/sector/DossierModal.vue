<template>
  <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 overflow-y-auto">
    <div class="bg-white rounded-xl shadow-xl max-w-2xl w-full my-8 p-6 max-h-[90vh] overflow-y-auto">
      <div class="flex justify-between items-start mb-4">
        <h3 class="text-lg font-semibold text-slate-800">Dossiê — {{ item.manifestation_count }} manifestação(ões)</h3>
        <button
          type="button"
          class="text-slate-500 hover:text-slate-700 p-1"
          @click="$emit('close')"
        >
          <X :size="20" class="stroke-current" />
        </button>
      </div>
      <p class="text-sm text-slate-600 mb-4">{{ item.technical_summary }}</p>
      <div class="space-y-4">
        <div
          v-for="m in item.manifestations"
          :key="m.id"
          class="border border-slate-200 rounded-lg p-3"
        >
          <p class="font-mono text-xs text-slate-500">{{ m.protocol }}</p>
          <p v-if="m.location_address" class="text-sm text-slate-700 mt-1">{{ m.location_address }}</p>
          <p class="text-sm text-slate-600 mt-1">{{ m.description?.slice(0, 200) }}{{ (m.description?.length || 0) > 200 ? '…' : '' }}</p>
          <p v-if="m.nlp_summary" class="text-xs text-slate-500 mt-1">Resumo IA: {{ m.nlp_summary }}</p>
        </div>
      </div>
      <p class="text-xs text-slate-400 mt-4">Fotos e mapa completos disponíveis no sistema ao abrir cada protocolo.</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { X } from '@/utils/icons'
import type { WorkOrderItem } from '@/stores/sector-board'

defineProps<{ item: WorkOrderItem }>()
defineEmits<{ (e: 'close'): void }>()
</script>
