<template>
  <div class="animate-slide-up">
    <ChatBubble is-bot>
      {{ message }}
    </ChatBubble>
    
    <div class="ml-13 mt-2">
      <div class="bg-gray-50 rounded-xl p-4 space-y-3">
        <!-- Descrição -->
        <div>
          <p class="text-xs font-semibold text-gray-500 uppercase mb-1">Descrição</p>
          <p class="text-sm text-gray-800">{{ description }}</p>
        </div>

        <!-- Localização -->
        <div v-if="locationAddress">
          <p class="text-xs font-semibold text-gray-500 uppercase mb-1">Localização</p>
          <p class="text-sm text-gray-800">{{ locationAddress }}</p>
        </div>

        <!-- Anônimo -->
        <div>
          <p class="text-xs font-semibold text-gray-500 uppercase mb-1">Tipo</p>
          <p class="text-sm text-gray-800">
            {{ isAnonymous ? 'Manifestação anônima' : 'Manifestação identificada' }}
          </p>
        </div>

        <!-- Anexos -->
        <div v-if="files && files.length > 0">
          <p class="text-xs font-semibold text-gray-500 uppercase mb-1">Anexos</p>
          <div class="space-y-2">
            <div
              v-for="(file, index) in files"
              :key="index"
              class="flex items-center gap-2 text-sm text-gray-800"
            >
              <component :is="FileIcon" :size="16" class="text-gray-500" />
              <span class="flex-1 truncate">{{ file.name }}</span>
              <span class="text-xs text-gray-500">{{ formatFileSize(file.size) }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Botão de Enviar -->
      <button
        @click="$emit('submit')"
        :disabled="!canSubmit || isSubmitting"
        class="w-full mt-4 px-6 py-3 bg-gov-blue text-white font-semibold rounded-xl hover:bg-gov-dark transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
      >
        <component
          v-if="isSubmitting"
          :is="LoaderIcon"
          :size="20"
          class="animate-spin"
        />
        {{ isSubmitting ? 'Enviando...' : 'Enviar Manifestação' }}
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Loader, File } from 'lucide-vue-next'
import ChatBubble from './ChatBubble.vue'
import { useManifestationStore } from '@/stores/manifestation'

defineProps<{
  message: string
}>()

defineEmits<{
  submit: []
}>()

const store = useManifestationStore()
const description = store.description
const locationAddress = store.locationAddress
const isAnonymous = store.isAnonymous
const canSubmit = store.canSubmit
const isSubmitting = store.isSubmitting
const files = store.files

const LoaderIcon = Loader
const FileIcon = File

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}
</script>
