<template>
  <div class="min-h-screen bg-gray-50 pb-20">
    <!-- Header -->
    <header class="bg-white shadow-sm sticky top-0 z-10">
      <div class="max-w-2xl mx-auto px-4 py-4 flex items-center gap-3">
        <button
          @click="$router.push('/')"
          class="p-2 hover:bg-gray-100 rounded-lg transition-colors"
        >
          <component :is="ArrowLeftIcon" :size="20" class="text-gray-600" />
        </button>
        <div>
          <h1 class="text-lg font-semibold text-gray-900">Nova Manifestação</h1>
          <p class="text-xs text-gray-500">Ouvidoria Municipal</p>
        </div>
      </div>
    </header>

    <!-- Chat Container -->
    <div class="max-w-2xl mx-auto px-4 py-6">
      <!-- Passo 1: Boas-vindas -->
      <div v-if="currentStep === 1" class="animate-fade-in">
        <ChatBubble is-bot>
          Olá! Sou a IA da Ouvidoria. Posso ajudar você a registrar uma solicitação de forma rápida. Vamos começar?
        </ChatBubble>
        <div class="ml-13 mt-4">
          <button
            @click="nextStep"
            class="px-6 py-3 bg-gov-blue text-white font-medium rounded-xl hover:bg-gov-dark transition-colors"
          >
            Começar
          </button>
        </div>
      </div>

      <!-- Passo 2: Identificação -->
      <div v-if="currentStep === 2">
        <StepIdentification
          message="Para começarmos, como você se chama? E qual seu CPF ou E-mail para acompanharmos sua manifestação?"
          @continue="nextStep"
        />
      </div>

      <!-- Passo 3: Descrição -->
      <div v-if="currentStep === 3">
        <StepDescription
          message="Entendi! Agora, por favor, descreva o problema ou situação que você gostaria de reportar."
          placeholder="Ex: Tem um buraco enorme na rua principal que está causando acidentes..."
          @submit="handleDescriptionSubmit"
        />
        <div v-if="store.description.length > 10" class="ml-13 mt-4">
          <button
            @click="handleDescriptionSubmit"
            :disabled="!store.canSubmit"
            class="px-6 py-3 bg-gov-blue text-white font-medium rounded-xl hover:bg-gov-dark transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Continuar
          </button>
        </div>
      </div>

      <!-- Passo 4: Análise e Confirmação -->
      <div v-if="currentStep === 4">
        <StepAnalysis
          ref="stepAnalysisRef"
          :description="store.description"
          :is-submitting="store.isSubmitting"
          @confirm="handleAnalysisConfirm"
          @continue-anyway="handleAnalysisConfirm"
          @back="currentStep = 3"
        />
      </div>

      <!-- Passo 5: Localização -->
      <div v-if="currentStep === 5">
        <StepLocation
          message="Entendi. E onde isso aconteceu?"
          @location-set="handleLocationSet"
        />
        <div v-if="store.hasLocation || store.locationAddress" class="ml-13 mt-4">
          <button
            @click="nextStep"
            class="px-6 py-3 bg-gov-blue text-white font-medium rounded-xl hover:bg-gov-dark transition-colors"
          >
            Continuar
          </button>
        </div>
        <!-- Permitir pular localização -->
        <div v-else class="ml-13 mt-4">
          <button
            @click="nextStep"
            class="text-sm text-gray-600 hover:text-gray-800 underline"
          >
            Pular esta etapa
          </button>
        </div>
      </div>

      <!-- Passo 6: Anexos -->
      <div v-if="currentStep === 6">
        <StepAttachments
          ref="stepAttachmentsRef"
          message="Deseja adicionar fotos ou documentos como evidência? (Opcional)"
          @continue="handleAttachmentsContinue"
          @skip="nextStep"
          @files-selected="handleFilesSelected"
        />
      </div>

      <!-- Passo 7: Revisão -->
      <div v-if="currentStep === 7">
        <StepReview
          message="Por favor, revise as informações antes de enviar:"
          @submit="handleSubmit"
        />
      </div>

      <!-- Passo 8: Sucesso -->
      <div v-if="currentStep === 8">
        <StepSuccess
          v-if="store.submittedProtocol"
          :protocol="store.submittedProtocol"
          @new="handleNewManifestation"
          @home="$router.push('/')"
          @register-another-demand="handleRegisterAnotherDemand"
        />
      </div>

      <!-- Erro -->
      <div v-if="store.error" class="ml-13 mt-4">
        <div class="bg-red-50 border-2 border-red-200 rounded-xl p-4">
          <p class="text-sm text-red-600">{{ store.error }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ArrowLeft } from 'lucide-vue-next'
import ChatBubble from '@/components/ChatBubble.vue'
import StepIdentification from '@/components/StepIdentification.vue'
import StepDescription from '@/components/StepDescription.vue'
import StepAnalysis from '@/components/StepAnalysis.vue'
import StepLocation from '@/components/StepLocation.vue'
import StepAttachments from '@/components/StepAttachments.vue'
import StepReview from '@/components/StepReview.vue'
import StepSuccess from '@/components/StepSuccess.vue'
import { useManifestationStore } from '@/stores/manifestation'

const store = useManifestationStore()
const currentStep = ref(1)
const stepAnalysisRef = ref<any>(null)
const stepAttachmentsRef = ref<any>(null)

const ArrowLeftIcon = ArrowLeft

onMounted(() => {
  // Detectar origem (web, app, etc)
  const userAgent = navigator.userAgent.toLowerCase()
  if (/mobile|android|iphone|ipad/.test(userAgent)) {
    store.setOrigin('app')
  } else {
    store.setOrigin('web')
  }
})

function nextStep() {
  currentStep.value++
  // Scroll suave para o topo
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

function handleDescriptionSubmit() {
  if (store.canSubmit) {
    nextStep() // Vai para análise
  }
}

function handleAnalysisConfirm() {
  // Obter correção do componente StepAnalysis se houver
  if (stepAnalysisRef.value) {
    const correction = stepAnalysisRef.value.getCorrection()
    if (correction) {
      store.setCitizenCorrection(correction)
    }
  }
  nextStep() // Vai para localização
}

function handleLocationSet() {
  // Pode avançar automaticamente se quiser
  // nextStep()
}

function handleFilesSelected(files: File[], descriptions: string[]) {
  store.setFiles(files, descriptions)
}

function handleAttachmentsContinue() {
  // Arquivos já foram atualizados via evento files-selected
  nextStep() // Vai para revisão
}

async function handleSubmit() {
  const protocol = await store.submitManifestation()
  if (protocol) {
    currentStep.value = 8 // Passo de sucesso (agora é 8 porque adicionamos passo de anexos)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }
}

function handleNewManifestation() {
  store.reset()
  currentStep.value = 1
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

function handleRegisterAnotherDemand() {
  currentStep.value = 3
  window.scrollTo({ top: 0, behavior: 'smooth' })
}
</script>
