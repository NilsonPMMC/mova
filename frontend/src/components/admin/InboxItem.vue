<template>
  <button
    type="button"
    class="relative w-full text-left rounded-lg border p-4 transition-colors hover:bg-slate-50 focus:outline-none focus:ring-2 focus:ring-gov-blue/30"
    :class="[
      isSelected ? 'ring-2 ring-blue-600 bg-blue-50 border-blue-300' : '',
      !isSelected && hasStack ? 'border-2 border-amber-300 bg-white shadow-md shadow-amber-200/50' : '',
      !isSelected && !hasStack ? 'border border-slate-200 bg-white' : ''
    ]"
    @click="$emit('select')"
  >
    <div
      class="absolute left-0 top-0 bottom-0 w-1 rounded-tl-lg rounded-bl-lg"
      :class="borderClass"
    />
    <div class="flex-1 min-w-0 pl-3">
        <div class="flex items-center justify-between gap-2 mb-1">
          <span class="font-mono text-sm font-semibold text-slate-800 truncate">
            {{ item.protocol }}
          </span>
          <span class="text-xs text-slate-500 shrink-0">
            {{ timeAgo }}
          </span>
        </div>
        <p class="text-sm text-slate-600 truncate mb-2">
          {{ item.category_name || 'Sem categoria' }}
        </p>
        <div class="flex flex-wrap gap-1">
          <span
            v-if="(item.urgency_level ?? 0) >= 4"
            class="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium bg-red-100 text-red-800"
          >
            <Flame :size="12" class="stroke-current" />
            Alta Urgência
          </span>
          <span
            v-if="hasStack"
            class="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium bg-amber-500 text-white font-semibold"
          >
            <Users :size="12" class="stroke-current" />
            {{ item.engagement_count }} Relatos Agrupados
          </span>
          <span
            v-if="item.sentiment_score != null && item.sentiment_score < -0.5"
            class="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium bg-orange-100 text-orange-800"
          >
            <Frown :size="12" class="stroke-current" />
            Sentimento Negativo
          </span>
        </div>
    </div>
  </button>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Flame, Users, Frown } from '@/utils/icons'
import type { InboxItem as InboxItemType } from '@/stores/admin-inbox'

const props = defineProps<{
  item: InboxItemType
  isSelected: boolean
}>()

defineEmits<{ select: [] }>()

const hasStack = computed(() => (props.item.engagement_count ?? 1) > 1)

const borderClass = computed(() => {
  const s = props.item.status
  if (s === 'resolved' || s === 'closed') return 'bg-emerald-500'
  if ((props.item.urgency_level ?? 0) >= 4) return 'bg-red-500'
  if ((props.item.urgency_level ?? 0) >= 3) return 'bg-amber-500'
  return 'bg-blue-500'
})

const timeAgo = computed(() => {
  const date = new Date(props.item.created_at)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffM = Math.floor(diffMs / 60000)
  const diffH = Math.floor(diffM / 60)
  const diffD = Math.floor(diffH / 24)
  if (diffM < 60) return `há ${diffM}min`
  if (diffH < 24) return `há ${diffH}h`
  return `há ${diffD}d`
})
</script>
