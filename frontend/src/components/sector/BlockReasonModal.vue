<template>
  <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
    <div class="bg-white rounded-xl shadow-xl max-w-md w-full p-6">
      <h3 class="text-lg font-semibold text-slate-800 mb-2">Por que não pode resolver?</h3>
      <p class="text-sm text-slate-500 mb-4">Informe o motivo do bloqueio.</p>
      <select
        v-model="selectedReason"
        class="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm mb-3"
      >
        <option value="">Selecione...</option>
        <option value="Setor Incorreto">Setor Incorreto (volta para Ouvidoria)</option>
        <option value="Falta Orçamento">Falta Orçamento (notifica Gestão)</option>
        <option value="Aguardando Chuva Parar">Aguardando Chuva Parar (pausa SLA)</option>
        <option value="Falta de Material">Falta de Material</option>
        <option value="Outro">Outro</option>
      </select>
      <textarea
        v-model="customReason"
        rows="2"
        class="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm"
        placeholder="Detalhe (opcional)"
      />
      <div class="flex gap-2 mt-4 justify-end">
        <button type="button" class="px-4 py-2 rounded-lg border border-slate-300 text-slate-700 hover:bg-slate-50" @click="emit('cancel')">
          Cancelar
        </button>
        <button
          type="button"
          class="px-4 py-2 rounded-lg bg-red-600 text-white hover:bg-red-700 disabled:opacity-50"
          :disabled="!reasonText"
          @click="confirm"
        >
          Bloquear
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

defineProps<{ workOrderId: string | null }>()
const emit = defineEmits(['confirm', 'cancel'])

const selectedReason = ref('')
const customReason = ref('')

const reasonText = computed(() => {
  const r = selectedReason.value?.trim()
  if (r === 'Outro') return customReason.value?.trim() || ''
  if (r) return customReason.value?.trim() ? r + ': ' + customReason.value.trim() : r
  return ''
})

function confirm() {
  if (reasonText.value) emit('confirm', reasonText.value)
}
</script>
