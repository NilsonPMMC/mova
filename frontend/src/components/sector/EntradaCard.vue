<template>
  <div class="rounded-lg border border-slate-200 bg-white p-3 shadow-sm">
    <div class="flex items-start justify-between gap-2">
      <div class="min-w-0 flex-1">
        <div class="flex items-center gap-2 flex-wrap mb-1">
          <span
            class="text-xs font-medium px-1.5 py-0.5 rounded"
            :class="item.engagement_count > 5 ? 'text-red-600 bg-red-50 font-bold' : 'text-amber-600 bg-amber-50'"
          >
            {{ item.engagement_count }} afetados
          </span>
        </div>
        <p class="text-sm font-mono text-slate-600">{{ item.protocol }}</p>
        <p class="text-sm text-slate-700 line-clamp-2 mt-0.5">{{ item.nlp_summary || item.description }}</p>
      </div>
    </div>
    <div class="mt-2">
      <button
        type="button"
        class="text-xs px-2 py-1 rounded bg-slate-700 text-white hover:bg-slate-800"
        @click="$emit('create-order', item.id)"
      >
        Adicionar ao cronograma
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { EntradaItem } from '@/stores/sector-board'

defineProps<{ item: EntradaItem }>()
defineEmits<{ (e: 'create-order', manifestationId: string): void }>()
</script>
