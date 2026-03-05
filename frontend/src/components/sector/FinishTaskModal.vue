<template>
  <div
    class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
    @click.self="$emit('cancel')"
  >
    <div class="bg-white rounded-lg shadow-xl max-w-2xl w-full">
      <div class="px-6 py-4 border-b border-slate-200">
        <h2 class="text-lg font-semibold text-slate-800">Concluir Ordem de Serviço</h2>
        <p class="text-sm text-slate-500 mt-1">
          Descreva a solução aplicada. Esta ação marcará a manifestação como resolvida.
        </p>
      </div>
      
      <form @submit.prevent="handleSubmit" class="p-6 space-y-4">
        <div>
          <label class="block text-sm font-medium text-slate-700 mb-2">
            Nota de Solução <span class="text-red-500">*</span>
          </label>
          <textarea
            v-model="solutionNote"
            rows="4"
            required
            placeholder="Descreva o que foi feito para resolver o problema..."
            class="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-gov-blue focus:border-transparent"
          />
          <p class="text-xs text-slate-500 mt-1">
            Esta nota será visível ao cidadão no rastreamento da manifestação.
          </p>
        </div>

        <div>
          <label class="block text-sm font-medium text-slate-700 mb-2">
            Foto da Solução (opcional)
          </label>
          <input
            ref="fileInputRef"
            type="file"
            accept="image/*"
            class="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm"
            @change="handleFileChange"
          />
          <p v-if="selectedFile" class="text-xs text-slate-500 mt-1">
            Arquivo selecionado: {{ selectedFile.name }}
          </p>
        </div>

        <div v-if="item.heat_count > 1" class="p-3 bg-amber-50 border border-amber-200 rounded-lg">
          <p class="inline-flex items-start gap-2 text-sm text-amber-800">
            <AlertTriangle :size="16" class="stroke-current shrink-0 mt-0.5" />
            <span>Esta ordem agrupa <strong>{{ item.heat_count }} manifestações</strong>. Todas serão marcadas como resolvidas automaticamente.</span>
          </p>
        </div>

        <div class="flex gap-3 justify-end pt-4 border-t border-slate-200">
          <button
            type="button"
            class="px-4 py-2 border border-slate-300 text-slate-700 rounded-lg text-sm font-medium hover:bg-slate-50"
            @click="$emit('cancel')"
          >
            Cancelar
          </button>
          <button
            type="submit"
            :disabled="!solutionNote.trim() || isSubmitting"
            class="inline-flex items-center gap-2 px-4 py-2 bg-emerald-600 text-white rounded-lg text-sm font-medium hover:bg-emerald-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <CheckCircle2 v-if="!isSubmitting" :size="16" class="stroke-current" />
            <Loader2 v-else :size="16" class="stroke-current animate-spin" />
            {{ isSubmitting ? 'Salvando...' : 'Confirmar Conclusão' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { AlertTriangle, CheckCircle2, Loader2 } from '@/utils/icons'
import type { WorkOrderItem } from '@/stores/sector-board'

defineProps<{
  item: WorkOrderItem
}>()

const emit = defineEmits<{
  confirm: [solutionNote: string, solutionPhoto?: File | null]
  cancel: []
}>()

const solutionNote = ref('')
const selectedFile = ref<File | null>(null)
const fileInputRef = ref<HTMLInputElement | null>(null)
const isSubmitting = ref(false)

function handleFileChange(e: Event) {
  const target = e.target as HTMLInputElement
  selectedFile.value = target.files?.[0] || null
}

function handleSubmit() {
  if (!solutionNote.value.trim()) return
  emit('confirm', solutionNote.value.trim(), selectedFile.value)
}
</script>
