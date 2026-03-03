<template>
  <Transition name="slide-up">
    <div
      v-if="showPrompt"
      class="fixed bottom-0 left-0 right-0 z-50 bg-white border-t-2 border-blue-600 shadow-lg p-4 md:p-6"
    >
      <div class="max-w-4xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
        <div class="flex-1">
          <p class="text-gray-800 font-medium text-sm md:text-base">
            {{ message }}
          </p>
        </div>
        <div class="flex gap-2">
          <button
            @click="dismissPrompt"
            class="px-4 py-2 text-gray-600 hover:text-gray-800 text-sm font-medium transition-colors"
          >
            Agora não
          </button>
          <button
            @click="installApp"
            class="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium text-sm transition-colors shadow-md"
          >
            Instalar
          </button>
        </div>
      </div>
    </div>
  </Transition>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'

const showPrompt = ref(false)
const deferredPrompt = ref<BeforeInstallPromptEvent | null>(null)
const message = 'Instale o App da Ouvidoria para acompanhar suas solicitações.'

interface BeforeInstallPromptEvent extends Event {
  prompt: () => Promise<void>
  userChoice: Promise<{ outcome: 'accepted' | 'dismissed' }>
}

// Handlers para eventos PWA
const handleBeforeInstallPrompt = (e: Event) => {
  e.preventDefault()
  deferredPrompt.value = e as BeforeInstallPromptEvent
  showPrompt.value = true
}

const handleAppInstalled = () => {
  showPrompt.value = false
  deferredPrompt.value = null
  localStorage.removeItem('pwa-install-dismissed')
}

onMounted(() => {
  // Verificar se já foi instalado
  if (window.matchMedia('(display-mode: standalone)').matches) {
    return // Já está instalado
  }

  // Verificar se já foi rejeitado (localStorage)
  const dismissed = localStorage.getItem('pwa-install-dismissed')
  if (dismissed) {
    const dismissedTime = parseInt(dismissed, 10)
    const daysSinceDismissed = (Date.now() - dismissedTime) / (1000 * 60 * 60 * 24)
    
    // Mostrar novamente após 7 dias
    if (daysSinceDismissed < 7) {
      return
    }
  }

  // Escutar eventos PWA
  window.addEventListener('beforeinstallprompt', handleBeforeInstallPrompt)
  window.addEventListener('appinstalled', handleAppInstalled)
})

onUnmounted(() => {
  // Cleanup: remover listeners
  window.removeEventListener('beforeinstallprompt', handleBeforeInstallPrompt)
  window.removeEventListener('appinstalled', handleAppInstalled)
})

const installApp = async () => {
  if (!deferredPrompt.value) {
    return
  }

  try {
    // Mostrar prompt de instalação
    await deferredPrompt.value.prompt()
    
    // Aguardar escolha do usuário
    const choiceResult = await deferredPrompt.value.userChoice
    
    if (choiceResult.outcome === 'accepted') {
      console.log('Usuário aceitou instalar o PWA')
    } else {
      console.log('Usuário rejeitou instalar o PWA')
    }
    
    // Limpar referência
    deferredPrompt.value = null
    showPrompt.value = false
  } catch (error) {
    console.error('Erro ao instalar PWA:', error)
  }
}

const dismissPrompt = () => {
  showPrompt.value = false
  // Salvar timestamp de quando foi rejeitado
  localStorage.setItem('pwa-install-dismissed', Date.now().toString())
}
</script>

<style scoped>
.slide-up-enter-active,
.slide-up-leave-active {
  transition: transform 0.3s ease-out, opacity 0.3s ease-out;
}

.slide-up-enter-from {
  transform: translateY(100%);
  opacity: 0;
}

.slide-up-leave-to {
  transform: translateY(100%);
  opacity: 0;
}
</style>
