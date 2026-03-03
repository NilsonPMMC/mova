<template>
  <div class="animate-slide-up">
    <ChatBubble is-bot>
      {{ message }}
    </ChatBubble>
    
    <div class="ml-13 mt-2">
      <textarea
        v-model="localDescription"
        :placeholder="placeholder"
        :rows="rows"
        class="w-full px-4 py-3 rounded-xl border-2 border-gray-200 focus:border-gov-blue focus:outline-none resize-none transition-colors text-gray-800 placeholder-gray-400"
        @input="handleInput"
        @keydown.enter.exact.prevent="handleEnter"
      />
      <p class="text-xs text-gray-500 mt-1 ml-1">
        {{ localDescription.length }} caracteres
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import ChatBubble from './ChatBubble.vue'
import { useManifestationStore } from '@/stores/manifestation'

const props = defineProps<{
  message: string
  placeholder?: string
  modelValue?: string
}>()

const emit = defineEmits<{
  'update:modelValue': [value: string]
  'submit': []
}>()

const store = useManifestationStore()
const localDescription = ref(props.modelValue || store.description || '')
const rows = ref(3)

watch(() => props.modelValue, (newVal) => {
  if (newVal !== undefined) {
    localDescription.value = newVal
  }
})

function handleInput(event: Event) {
  const target = event.target as HTMLTextAreaElement
  localDescription.value = target.value
  store.setDescription(target.value)
  emit('update:modelValue', target.value)
  
  // Auto-expand textarea
  target.style.height = 'auto'
  const newHeight = Math.min(target.scrollHeight, 200)
  target.style.height = `${newHeight}px`
  rows.value = Math.ceil(newHeight / 24)
}

function handleEnter() {
  if (localDescription.value.trim().length > 10) {
    emit('submit')
  }
}
</script>
