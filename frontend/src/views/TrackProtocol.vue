<template>
  <div class="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 py-8 px-4">
    <div class="max-w-4xl mx-auto">
      <!-- Header -->
      <div class="text-center mb-8">
        <h1 class="text-3xl font-bold text-gray-900 mb-2">Acompanhar Manifestação</h1>
        <p class="text-gray-600">Digite seu protocolo para ver o andamento</p>
      </div>

      <!-- Campo de Busca -->
      <div class="bg-white rounded-2xl shadow-lg p-8 mb-6">
        <div class="flex gap-3">
          <div class="flex-1 relative">
            <component :is="SearchIcon" :size="20" class="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" />
            <input
              v-model="protocolInput"
              @keyup.enter="handleSearch"
              type="text"
              placeholder="Digite seu protocolo (ex: OUV-20260216-XXXXX)"
              class="w-full pl-12 pr-4 py-4 border-2 border-gray-200 rounded-xl focus:border-gov-blue focus:outline-none text-lg"
            />
          </div>
          <button
            @click="handleSearch"
            :disabled="!protocolInput.trim() || isSearching"
            class="px-8 py-4 bg-gov-blue text-white font-semibold rounded-xl hover:bg-gov-dark transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            <component v-if="isSearching" :is="LoaderIcon" :size="20" class="animate-spin" />
            <span v-else>Buscar</span>
          </button>
        </div>
        <p v-if="error" class="mt-4 text-sm text-red-600">{{ error }}</p>
      </div>

      <!-- Resultado da Busca -->
      <div v-if="searchedProtocol">
        <TimelineStatus :protocol="searchedProtocol" />
      </div>

      <!-- Links Úteis -->
      <div class="bg-white rounded-xl shadow-sm p-6 mt-6">
        <h3 class="text-sm font-semibold text-gray-700 mb-3">Outras opções</h3>
        <div class="flex gap-4">
          <router-link
            to="/minhas-manifestacoes"
            class="text-gov-blue hover:text-gov-dark font-medium text-sm"
          >
            Ver todas as minhas manifestações →
          </router-link>
          <router-link
            to="/nova-manifestacao"
            class="text-gov-blue hover:text-gov-dark font-medium text-sm"
          >
            Nova manifestação →
          </router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { Search, Loader } from 'lucide-vue-next'
import TimelineStatus from '@/components/TimelineStatus.vue'

const route = useRoute()

const protocolInput = ref('')
const searchedProtocol = ref<string | null>(null)
const isSearching = ref(false)
const error = ref<string | null>(null)

const SearchIcon = Search
const LoaderIcon = Loader

function handleSearch() {
  const protocol = protocolInput.value.trim().toUpperCase()
  if (!protocol) {
    error.value = 'Digite um protocolo válido'
    return
  }
  
  error.value = null
  searchedProtocol.value = protocol
}

// Se protocolo vier na query, buscar automaticamente
onMounted(() => {
  const protocolFromQuery = route.query.protocol as string
  if (protocolFromQuery) {
    protocolInput.value = protocolFromQuery.toUpperCase()
    searchedProtocol.value = protocolFromQuery.toUpperCase()
  }
})
</script>
