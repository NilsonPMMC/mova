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

      <div class="flex gap-2">
        <input
          v-model="localAddress"
          type="text"
          placeholder="Digite o endereço manualmente"
          class="flex-1 px-4 py-3 rounded-xl border-2 border-gray-200 focus:border-gov-blue focus:outline-none transition-colors text-gray-800 placeholder-gray-400"
          @input="handleInput"
        />
        <button
          type="button"
          @click="geocodeAddress"
          :disabled="!localAddress.trim() || isGeocoding"
          class="px-4 py-3 rounded-xl border-2 border-gov-blue bg-gov-blue text-white font-medium hover:bg-gov-dark transition-colors disabled:opacity-50 disabled:cursor-not-allowed whitespace-nowrap"
        >
          {{ isGeocoding ? 'Buscando...' : 'Validar no Mapa' }}
        </button>
      </div>

      <!-- Mapa (iframe OpenStreetMap quando há coordenadas válidas) -->
      <div v-if="lat && lng" class="mt-4 rounded-md overflow-hidden h-64 border border-gray-300 w-full">
        <iframe
          width="100%"
          height="100%"
          frameborder="0"
          scrolling="no"
          :src="`https://www.openstreetmap.org/export/embed.html?bbox=${lng - 0.003},${lat - 0.003},${lng + 0.003},${lat + 0.003}&layer=mapnik&marker=${lat},${lng}`"
        />
      </div>

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
const isGeocoding = ref(false)
const locationStatus = ref<string>('')
const locationStatusClass = ref('')

const lat = ref<number | null>(store.latitude ?? null)
const lng = ref<number | null>(store.longitude ?? null)

const MapPinIcon = MapPin
const LoaderIcon = Loader

watch(() => store.locationAddress, (newVal) => {
  if (newVal) {
    localAddress.value = newVal
  }
})

watch([() => store.latitude, () => store.longitude], ([newLat, newLng]) => {
  if (newLat != null && newLng != null) {
    lat.value = newLat as number
    lng.value = newLng as number
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
    const latVal = parseFloat(position.coords.latitude.toFixed(8))
    const lngVal = parseFloat(position.coords.longitude.toFixed(8))

    // Tentar obter endereço reverso (opcional)
    try {
      const response = await fetch(
        `https://nominatim.openstreetmap.org/reverse?format=json&lat=${latVal}&lon=${lngVal}&zoom=18&addressdetails=1`,
        { headers: { 'User-Agent': 'Mova-Ouvidoria-Mogi/1.0' } }
      )
      const data = await response.json()
      const address = data.display_name || `${latVal.toFixed(6)}, ${lngVal.toFixed(6)}`

      store.setLocation(address, latVal, lngVal)
      lat.value = latVal
      lng.value = lngVal
      localAddress.value = address
      locationStatus.value = 'Localização obtida com sucesso!'
      locationStatusClass.value = 'bg-green-50 text-green-600'
    } catch {
      const address = `${latVal.toFixed(6)}, ${lngVal.toFixed(6)}`
      store.setLocation(address, latVal, lngVal)
      lat.value = latVal
      lng.value = lngVal
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

async function geocodeAddress() {
  const address = localAddress.value.trim()
  if (!address) {
    locationStatus.value = 'Digite um endereço para validar.'
    locationStatusClass.value = 'bg-yellow-50 text-yellow-600'
    return
  }

  isGeocoding.value = true
  locationStatus.value = ''

  try {
    const url = `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(address)}&limit=1`
    const res = await fetch(url, {
      headers: { 'Accept-Language': 'pt-BR,pt;q=0.9', 'User-Agent': 'Mova-Ouvidoria-Mogi/1.0' },
    })
    const data = await res.json()

    if (!Array.isArray(data) || data.length === 0) {
      locationStatus.value = 'Endereço não encontrado. Tente ser mais específico (ex.: cidade, estado).'
      locationStatusClass.value = 'bg-yellow-50 text-yellow-600'
      lat.value = null
      lng.value = null
      return
    }

    const latVal = parseFloat(data[0].lat)
    const lngVal = parseFloat(data[0].lon)
    lat.value = parseFloat(latVal.toFixed(8))
    lng.value = parseFloat(lngVal.toFixed(8))

    store.setLocation(address, lat.value, lng.value)
    locationStatus.value = 'Endereço validado no mapa. Confira a posição no mapa.'
    locationStatusClass.value = 'bg-green-50 text-green-600'

    emit('location-set')
  } catch (err) {
    locationStatus.value = 'Erro ao buscar o endereço. Tente novamente.'
    locationStatusClass.value = 'bg-red-50 text-red-600'
    lat.value = null
    lng.value = null
  } finally {
    isGeocoding.value = false
  }
}
</script>
