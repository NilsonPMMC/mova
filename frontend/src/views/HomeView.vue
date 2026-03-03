<template>
  <div class="min-h-screen bg-gradient-to-br from-gov-blue to-gov-dark flex items-center justify-center p-4">
    <div class="max-w-md w-full bg-white rounded-2xl shadow-xl p-8 text-center">
      <div class="mb-6">
        <div class="inline-flex items-center justify-center w-20 h-20 bg-gov-blue rounded-full mb-4">
          <component :is="MessageSquareIcon" :size="40" class="text-white" />
        </div>
        <h1 class="text-3xl font-bold text-gray-900 mb-2">Ouvidoria Municipal</h1>
        <p class="text-gray-600">Sua voz é importante para melhorar nossa cidade</p>
      </div>

      <div class="space-y-4">
        <router-link
          to="/nova-manifestacao"
          class="block w-full px-6 py-4 bg-gov-blue text-white font-semibold rounded-xl hover:bg-gov-dark transition-colors shadow-lg"
        >
          Nova Manifestação
        </router-link>

        <div class="grid grid-cols-2 gap-3 mt-4">
          <router-link
            to="/acompanhar"
            class="block px-4 py-3 bg-gray-100 text-gray-700 font-medium rounded-xl hover:bg-gray-200 transition-colors text-sm"
          >
            Acompanhar Protocolo
          </router-link>
          <router-link
            to="/minhas-manifestacoes"
            class="block px-4 py-3 bg-gray-100 text-gray-700 font-medium rounded-xl hover:bg-gray-200 transition-colors text-sm"
          >
            Minhas Manifestações
          </router-link>
        </div>

        <div class="text-xs text-gray-500 mt-6">
          <p>Status da API: {{ apiStatus }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { MessageSquare } from 'lucide-vue-next'
import apiService from '@/services/api'

const apiStatus = ref('Verificando...')
const MessageSquareIcon = MessageSquare

onMounted(async () => {
  try {
    const response = await apiService.get('/health/')
    if (response.data.status === 'ok') {
      apiStatus.value = 'Conectado'
    } else {
      apiStatus.value = 'Erro na resposta'
    }
  } catch (error) {
    apiStatus.value = 'Desconectado'
    console.error('Erro ao conectar com o backend:', error)
  }
})
</script>
