<template>
  <div
    :class="[
      'flex items-start gap-3 mb-4 animate-fade-in',
      isBot ? 'justify-start' : 'justify-end flex-row-reverse'
    ]"
  >
    <!-- Avatar -->
    <div
      :class="[
        'flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center',
        isBot ? 'bg-gov-blue text-white' : 'bg-gray-200 text-gray-600'
      ]"
    >
      <component
        :is="isBot ? BotIcon : UserIcon"
        :size="20"
        class="stroke-current"
      />
    </div>

    <!-- Message Bubble -->
    <div
      :class="[
        'chat-bubble',
        isBot ? 'chat-bubble-left' : 'chat-bubble-right'
      ]"
    >
      <p class="text-sm leading-relaxed whitespace-pre-wrap">
        <slot />
      </p>
      <p v-if="timestamp" class="text-xs mt-2 opacity-70">
        {{ timestamp }}
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Bot, User } from 'lucide-vue-next'

defineProps<{
  isBot?: boolean
  timestamp?: string
}>()

const BotIcon = Bot
const UserIcon = User
</script>
