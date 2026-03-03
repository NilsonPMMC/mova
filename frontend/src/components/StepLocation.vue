<template>
  <div class="animate-slide-up">
    <ChatBubble is-bot>
      {{ message }}
    </ChatBubble>
    
    <div class="ml-13 mt-2 space-y-3">
      <!-- Botão de Geolocalização -->
      <button
        @click="getCurrentLocation"
        :disabled="isLoading"
        class="w-full px-4 py-3 rounded-xl border-2 border-gov-blue bg-white text-gov-blue font-medium hover:bg-gov-light transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
      >
        <component
          :is="isLoading ? LoaderIcon : MapPinIcon"
          :size="20"
          :class="{ 'animate-spin': isLoading }"
        />
        {{ isLoading ? 'Obtendo localização...' : 'Usar minha localização atual' }}
      </button>

      <!-- Ou campo de texto manual -->
      <div class="text-center text-sm text-gray-500">ou</div>

      <input
        v-model="localAddress"
        type="text"
        placeholder="Digite o endereço manualmente"
        class="w-full px-4 py-3 rounded-xl border-2 border-gray-200 focus:border-gov-blue focus:outline-none transition-colors text-gray-800 placeholder-gray-400"
        @input="handleInput"
      />

      <!-- Status da localização -->
      <div v-if="locationStatus" class="text-sm px-3 py-2 rounded-lg" :class="locationStatusClass">
        {{ locationStatus }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { MapPin, Loader } from 'lucide-vue-next'
import ChatBubble from './ChatBubble.vue'
import { useManifestationStore } from '@/stores/manifestation'

defineProps<{
  message: string
}>()

const emit = defineEmits<{
  'location-set': []
}>()

const store = useManifestationStore()
const localAddress = ref(store.locationAddress || '')
const isLoading = ref(false)
const locationStatus = ref<string>('')
const locationStatusClass = ref('')

const MapPinIcon = MapPin
const LoaderIcon = Loader

watch(() => store.locationAddress, (newVal) => {
  if (newVal) {
    localAddress.value = newVal
  }
})

async function getCurrentLocation() {
  if (!navigator.geolocation) {
    locationStatus.value = 'Geolocalização não suportada pelo seu navegador.'
    locationStatusClass.value = 'bg-red-50 text-red-600'
    return
  }

  isLoading.value = true
  locationStatus.value = ''

  try {
    const position = await new Promise<GeolocationPosition>((resolve, reject) => {
      navigator.geolocation.getCurrentPosition(resolve, reject, {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 0
      })
    })

    // Arredondar para 8 casas decimais (conforme modelo Django)
    // Latitude: max_digits=10, decimal_places=8 (máx 2 antes + 8 depois)
    // Longitude: max_digits=11, decimal_places=8 (máx 3 antes + 8 depois)
    const lat = parseFloat(position.coords.latitude.toFixed(8))
    const lng = parseFloat(position.coords.longitude.toFixed(8))

    // Tentar obter endereço reverso (opcional)
    try {
      const response = await fetch(
        `https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lng}&zoom=18&addressdetails=1`
      )
      const data = await response.json()
      const address = data.display_name || `${lat.toFixed(6)}, ${lng.toFixed(6)}`
      
      store.setLocation(address, lat, lng)
      localAddress.value = address
      locationStatus.value = 'Localização obtida com sucesso!'
      locationStatusClass.value = 'bg-green-50 text-green-600'
    } catch {
      // Se falhar o reverse geocoding, usar apenas coordenadas
      const address = `${lat.toFixed(6)}, ${lng.toFixed(6)}`
      store.setLocation(address, lat, lng)
      localAddress.value = address
      locationStatus.value = 'Coordenadas obtidas!'
      locationStatusClass.value = 'bg-green-50 text-green-600'
    }

    emit('location-set')
  } catch (error: any) {
    let message = 'Erro ao obter localização.'
    if (error.code === 1) {
      message = 'Permissão de localização negada. Por favor, digite o endereço manualmente.'
    } else if (error.code === 2) {
      message = 'Não foi possível determinar sua localização. Tente novamente ou digite o endereço.'
    } else if (error.code === 3) {
      message = 'Tempo esgotado ao obter localização. Tente novamente.'
    }
    
    locationStatus.value = message
    locationStatusClass.value = 'bg-yellow-50 text-yellow-600'
  } finally {
    isLoading.value = false
  }
}

function handleInput(event: Event) {
  const target = event.target as HTMLInputElement
  localAddress.value = target.value
  store.setLocation(target.value)
}
</script>
