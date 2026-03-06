<template>
  <div class="animate-fade-in">
    <ChatBubble is-bot>
      <span>Escolha a Clínica e o Horário</span>
      <span v-if="!store.isLoadingPartners && store.nearbyPartners.length > 0" class="block mt-2 text-sm text-gray-600">
        Com base na sua localização, estas são as clínicas mais próximas com vagas disponíveis.
      </span>
    </ChatBubble>

    <div class="ml-13 mt-4">
      <!-- Loading State -->
      <div v-if="store.isLoadingPartners" class="flex items-center gap-3 p-6 bg-white rounded-xl border border-gray-200">
        <component :is="LoaderIcon" :size="24" class="animate-spin text-gov-blue" />
        <span class="text-gray-600">Buscando clínicas próximas...</span>
      </div>

      <!-- Sem vagas -->
      <div
        v-else-if="!store.isLoadingPartners && store.nearbyPartners.length === 0"
        class="p-6 bg-amber-50 rounded-xl border border-amber-200 text-center"
      >
        <p class="text-amber-800 font-medium">
          Não há clínicas com vagas disponíveis para o tipo de animal selecionado.
        </p>
        <p class="text-sm text-amber-700 mt-2">
          Entre em contato com a Ouvidoria pelo 156 para mais informações.
        </p>
        <button
          type="button"
          @click="emit('next')"
          class="mt-4 px-6 py-2 bg-amber-600 text-white rounded-lg text-sm font-medium hover:bg-amber-700"
        >
          Continuar sem agendar
        </button>
      </div>

      <!-- Lista de Parceiros -->
      <div v-else class="space-y-4">
        <div
          v-for="partner in store.nearbyPartners"
          :key="partner.id"
          class="bg-white rounded-xl border border-gray-200 overflow-hidden shadow-sm"
        >
          <div class="p-4 border-b border-gray-100">
            <h3 class="font-semibold text-gray-900">{{ partner.name }}</h3>
            <p class="text-sm text-gray-600 mt-1">{{ partner.address }}</p>
            <p class="text-xs text-gov-blue mt-1 font-medium">
              {{ ((partner.distance_meters || 0) / 1000).toFixed(1) }} km de você
            </p>
          </div>

          <div class="p-4 flex flex-wrap gap-2">
            <button
              v-for="schedule in partner.schedules"
              :key="schedule.id"
              type="button"
              :class="[
                'px-4 py-2 rounded-lg text-sm font-medium transition-colors',
                selectedScheduleId === schedule.id
                  ? 'bg-gov-blue text-white border-2 border-gov-blue'
                  : 'bg-gray-100 text-gray-700 border-2 border-transparent hover:bg-gray-200'
              ]"
              @click="selectedScheduleId = schedule.id"
            >
              {{ formatDate(schedule.date) }} - {{ schedule.time_slot }} ({{ schedule.available_slots }} vagas)
            </button>
            <p v-if="!partner.schedules || partner.schedules.length === 0" class="text-sm text-gray-500 italic">
              Sem vagas neste parceiro
            </p>
          </div>
        </div>
      </div>

      <!-- Botão Confirmar -->
      <div class="mt-6">
        <button
          @click="handleNext"
          :disabled="!selectedScheduleId"
          class="w-full px-6 py-3 bg-gov-blue text-white font-medium rounded-xl hover:bg-gov-dark transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Confirmar e Avançar
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Loader } from 'lucide-vue-next'
import ChatBubble from './ChatBubble.vue'
import { useManifestationStore } from '@/stores/manifestation'

const store = useManifestationStore()
const selectedScheduleId = ref<number | null>(null)
const LoaderIcon = Loader

function formatDate(dateStr: string): string {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return d.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit', year: 'numeric' })
}

const emit = defineEmits<{ next: [] }>()

function handleNext() {
  if (selectedScheduleId.value) {
    store.updateServiceData({ schedule_id: selectedScheduleId.value })
    emit('next')
  }
}

onMounted(() => {
  const sd = store.draftAnalysis?.service_data
  const animalType = sd?.animal_type as string | undefined
  const animalGender = sd?.animal_gender as string | undefined
  const typeStr = typeof animalType === 'string' ? animalType.trim() : ''
  const genderStr = typeof animalGender === 'string' ? animalGender.trim() : ''
  const animalLabel = typeStr && genderStr
    ? `${typeStr.charAt(0).toUpperCase() + typeStr.slice(1)} ${genderStr.charAt(0).toUpperCase() + genderStr.slice(1)}`
    : typeStr || 'Gato'
  store.fetchNearestPartners(animalLabel)
})
</script>
