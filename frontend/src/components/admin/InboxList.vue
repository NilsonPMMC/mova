<template>
  <div class="h-full flex flex-col bg-slate-50 border-r border-slate-200">
    <div class="p-4 border-b border-slate-200 bg-white shrink-0">
      <h2 class="text-lg font-semibold text-slate-800 mb-3">Fila de Triagem</h2>
      <div class="flex flex-wrap gap-2">
        <button
          v-for="opt in filterOptions"
          :key="opt.value"
          type="button"
          class="px-3 py-1.5 rounded-lg text-sm font-medium transition-colors"
          :class="store.filter === opt.value
            ? 'bg-slate-800 text-white'
            : 'bg-slate-200 text-slate-700 hover:bg-slate-300'"
          @click="store.setFilter(opt.value)"
        >
          {{ opt.label }}
        </button>
      </div>
    </div>
    <div class="flex-1 overflow-y-auto p-3 space-y-2">
      <div v-if="store.loading" class="flex items-center justify-center py-12">
        <span class="text-sm text-slate-500">Carregando...</span>
      </div>
      <template v-else-if="store.sortedList.length">
        <InboxItem
          v-for="item in store.sortedList"
          :key="item.id"
          :item="item"
          :is-selected="store.selectedId === item.id"
          @select="store.fetchDetail(item.id)"
        />
      </template>
      <div v-else class="py-12 text-center text-sm text-slate-500">
        Nenhuma manifestação encontrada.
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useAdminInboxStore } from '@/stores/admin-inbox'
import InboxItem from './InboxItem.vue'
import type { InboxFilter } from '@/stores/admin-inbox'

const store = useAdminInboxStore()

const filterOptions: { value: InboxFilter; label: string }[] = [
  { value: 'all_open', label: 'Abertos' },
  { value: 'waiting_triage', label: 'Triagem' },
  { value: 'in_analysis', label: 'Em análise' },
  { value: 'resolved', label: 'Resolvidos' },
]
</script>
