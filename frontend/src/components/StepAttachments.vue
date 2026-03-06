<template>
  <div class="animate-fade-in">
    <!-- Mensagem do Bot -->
    <ChatBubble is-bot>
      {{ message }}
      <span v-if="files.length === 0" class="block mt-2 text-sm text-gray-600">
        Você pode enviar fotos ou documentos para comprovar sua manifestação (máximo 5MB por arquivo).
      </span>
    </ChatBubble>

    <div class="ml-13 mt-4">
      <!-- Instruções específicas para Castração -->
      <div v-if="isCastration" class="mb-6 bg-blue-50 p-4 rounded-lg border border-blue-200">
        <h3 class="font-bold text-blue-800 mb-2">Documentos Obrigatórios para Castração</h3>
        <ul class="list-disc pl-5 text-sm text-blue-700 space-y-1">
          <li>Foto do RG ou CNH (Frente e Verso)</li>
          <li>Comprovante de Endereço atualizado no seu nome (ou pais/cônjuge)</li>
        </ul>
      </div>

      <!-- Área de Upload -->
      <div
        @drop.prevent="handleDrop"
        @dragover.prevent="isDragging = true"
        @dragleave.prevent="isDragging = false"
        @click="triggerFileInput"
        :class="[
          'border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition-colors',
          isDragging ? 'border-gov-blue bg-blue-50' : 'border-gray-300 hover:border-gov-blue hover:bg-gray-50'
        ]"
      >
        <input
          ref="fileInputRef"
          type="file"
          multiple
          accept="image/*,.pdf"
          :capture="isMobile ? 'environment' : undefined"
          @change="handleFileSelect"
          class="hidden"
        />
        
        <div class="flex flex-col items-center gap-3">
          <component :is="UploadIcon" :size="32" class="text-gray-400" />
          <div>
            <p class="text-sm font-medium text-gray-700">
              Arraste arquivos aqui ou clique para selecionar
            </p>
            <p class="text-xs text-gray-500 mt-1">
              Formatos aceitos: JPG, PNG, WEBP, PDF (máx. 5MB cada)
            </p>
          </div>
        </div>
      </div>

      <!-- Lista de Arquivos Selecionados -->
      <div v-if="files.length > 0" class="mt-4 space-y-3">
        <div
          v-for="(file, index) in files"
          :key="index"
          class="bg-white border border-gray-200 rounded-lg p-3 flex items-start gap-3"
        >
          <!-- Preview de Imagem -->
          <div v-if="isImage(file)" class="flex-shrink-0">
            <img
              :src="getFilePreview(file)"
              :alt="file.name"
              class="w-16 h-16 object-cover rounded"
            />
          </div>
          
          <!-- Ícone para PDF -->
          <div v-else class="flex-shrink-0 w-16 h-16 bg-red-100 rounded flex items-center justify-center">
            <component :is="FileIcon" :size="24" class="text-red-600" />
          </div>

          <!-- Informações do Arquivo -->
          <div class="flex-1 min-w-0">
            <p class="text-sm font-medium text-gray-900 truncate">{{ file.name }}</p>
            <p class="text-xs text-gray-500">{{ formatFileSize(file.size) }}</p>
            
            <!-- Campo de Descrição Opcional -->
            <input
              v-model="fileDescriptions[index]"
              type="text"
              :placeholder="`Descrição opcional (ex: 'Foto do buraco')`"
              class="mt-2 w-full px-3 py-1.5 text-xs border border-gray-300 rounded-lg focus:ring-2 focus:ring-gov-blue focus:border-transparent"
              @input="updateFileDescription(index, ($event.target as HTMLInputElement)?.value ?? '')"
            />
          </div>

          <!-- Botão Remover -->
          <button
            @click.stop="removeFile(index)"
            class="flex-shrink-0 p-1 text-red-500 hover:bg-red-50 rounded transition-colors"
          >
            <component :is="XIcon" :size="20" />
          </button>
        </div>
      </div>

      <!-- Procuração Digital (Condução do Animal) -->
      <div v-if="isCastration" class="mt-8 border-t border-slate-200 pt-6">
        <h3 class="font-bold text-slate-800 mb-4">Procuração Digital (Condução do Animal)</h3>
        <div class="mb-4">
          <label class="flex items-center gap-2 text-sm text-slate-700 cursor-pointer">
            <input type="checkbox" v-model="isOwnerTaking" class="rounded border-slate-300 w-5 h-5 text-blue-600 focus:ring-blue-500">
            <span class="font-medium">Eu mesmo(a) vou levar o animal no dia da cirurgia.</span>
          </label>
        </div>

        <div v-if="!isOwnerTaking" class="space-y-4 bg-slate-50 p-4 rounded-lg border border-slate-200 animate-fade-in">
          <p class="text-sm text-slate-600 mb-2">Preencha os dados da pessoa que conduzirá o animal por você:</p>
          <div>
            <label class="block text-xs font-medium text-slate-700 mb-1">Nome Completo do Condutor</label>
            <input type="text" v-model="conductorName" placeholder="Nome da pessoa que vai levar" class="w-full rounded-md border-slate-300 text-sm p-2">
          </div>
          <div>
            <label class="block text-xs font-medium text-slate-700 mb-1">CPF do Condutor</label>
            <input type="text" v-model="conductorCpf" placeholder="000.000.000-00" class="w-full rounded-md border-slate-300 text-sm p-2">
          </div>
          <div class="mt-4 bg-white p-3 border border-slate-200 rounded">
            <label class="flex items-start gap-2 text-sm text-slate-700 cursor-pointer">
              <input type="checkbox" v-model="acceptProxy" class="mt-1 rounded border-slate-300 text-blue-600 focus:ring-blue-500">
              <span class="text-xs leading-relaxed">Declaro, sob as penas da lei, que autorizo o cidadão acima a conduzir meu animal para a clínica, assumindo a responsabilidade por eventuais decisões médicas de emergência.</span>
            </label>
          </div>
        </div>
      </div>

      <!-- Botões de Ação -->
      <div class="mt-6 flex gap-3">
        <button
          @click="handleNext"
          class="flex-1 px-6 py-3 bg-gov-blue text-white font-medium rounded-xl hover:bg-gov-dark transition-colors"
        >
          Continuar
        </button>
        <button
          v-if="files.length === 0 && !isCastration"
          @click="$emit('skip')"
          class="px-6 py-3 bg-gray-200 text-gray-700 font-medium rounded-xl hover:bg-gray-300 transition-colors"
        >
          Pular esta etapa
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { Upload, File, X } from 'lucide-vue-next'
import ChatBubble from './ChatBubble.vue'
import { useManifestationStore } from '@/stores/manifestation'

defineProps<{
  message?: string
}>()

const emit = defineEmits<{
  continue: []
  skip: []
  'files-selected': [files: File[], descriptions: string[]]
}>()

const store = useManifestationStore()
const isCastration = computed(() => store.draftAnalysis?.intent === 'SERVICE_CASTRATION')

// Variáveis da Procuração Digital
const isOwnerTaking = ref(true)
const conductorName = ref('')
const conductorCpf = ref('')
const acceptProxy = ref(false)

const fileInputRef = ref<HTMLInputElement | null>(null)
const files = ref<File[]>([])
const fileDescriptions = ref<string[]>([])
const isDragging = ref(false)
const isMobile = ref(false)

const UploadIcon = Upload
const FileIcon = File
const XIcon = X

const MAX_FILE_SIZE = 5 * 1024 * 1024 // 5MB
const ALLOWED_TYPES = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp', 'application/pdf']

onMounted(() => {
  // Detectar se é mobile
  const userAgent = navigator.userAgent.toLowerCase()
  isMobile.value = /mobile|android|iphone|ipad/.test(userAgent)
})

function triggerFileInput() {
  fileInputRef.value?.click()
}

function validateFile(file: File): string | null {
  // Validar tamanho
  if (file.size > MAX_FILE_SIZE) {
    return `O arquivo "${file.name}" é muito grande. Tamanho máximo: 5MB.`
  }
  
  // Validar tipo
  if (!ALLOWED_TYPES.includes(file.type)) {
    return `O arquivo "${file.name}" não é um formato permitido. Use JPG, PNG, WEBP ou PDF.`
  }
  
  // Validar extensão
  const ext = file.name.split('.').pop()?.toLowerCase()
  const allowedExts = ['jpg', 'jpeg', 'png', 'webp', 'pdf']
  if (!ext || !allowedExts.includes(ext)) {
    return `O arquivo "${file.name}" não é um formato permitido. Use JPG, PNG, WEBP ou PDF.`
  }
  
  return null
}

function handleFileSelect(event: Event) {
  const target = event.target as HTMLInputElement
  if (target.files) {
    addFiles(Array.from(target.files))
  }
}

function handleDrop(event: DragEvent) {
  isDragging.value = false
  if (event.dataTransfer?.files) {
    addFiles(Array.from(event.dataTransfer.files))
  }
}

function addFiles(newFiles: File[]) {
  const validFiles: File[] = []
  const errors: string[] = []
  
  for (const file of newFiles) {
    const error = validateFile(file)
    if (error) {
      errors.push(error)
    } else {
      validFiles.push(file)
    }
  }
  
  if (errors.length > 0) {
    alert(errors.join('\n'))
  }
  
  if (validFiles.length > 0) {
    files.value.push(...validFiles)
    fileDescriptions.value.push(...new Array(validFiles.length).fill(''))
    emit('files-selected', files.value, fileDescriptions.value)
  }
}

function removeFile(index: number) {
  files.value.splice(index, 1)
  fileDescriptions.value.splice(index, 1)
  emit('files-selected', files.value, fileDescriptions.value)
}

function updateFileDescription(index: number, value: string) {
  fileDescriptions.value[index] = value
  emit('files-selected', files.value, fileDescriptions.value)
}

function isImage(file: File): boolean {
  return file.type.startsWith('image/')
}

function getFilePreview(file: File): string {
  return URL.createObjectURL(file)
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

function handleNext() {
  // Validação de Documentos Obrigatórios para Castração
  const currentFiles = files.value || []
  if (isCastration.value && currentFiles.length < 2) {
    alert('Atenção: Para o serviço de castração, é obrigatório anexar no mínimo 2 documentos (Foto do RG/CNH e Comprovante de Endereço).')
    return
  }

  if (isCastration.value && !isOwnerTaking.value) {
    if (!conductorName.value?.trim() || !conductorCpf.value?.trim()) {
      alert('Por favor, preencha o nome e o CPF do condutor.')
      return
    }
    const cpfDigits = conductorCpf.value.replace(/\D/g, '')
    if (cpfDigits.length !== 11) {
      alert('Por favor, informe um CPF válido do condutor (11 dígitos).')
      return
    }
    if (!acceptProxy.value) {
      alert('Você precisa aceitar o termo de responsabilidade da procuração.')
      return
    }
    store.updateServiceData({
      is_owner_taking: false,
      conductor_name: conductorName.value.trim(),
      conductor_cpf: conductorCpf.value.trim(),
      proxy_accepted: true,
    })
  } else if (isCastration.value && isOwnerTaking.value) {
    store.updateServiceData({ is_owner_taking: true })
  }
  emit('continue')
}

// Expor dados para componente pai
defineExpose({
  getFiles: () => files.value,
  getDescriptions: () => fileDescriptions.value
})
</script>
