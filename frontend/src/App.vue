<template>
  <div id="app">
    <RouterView />
    <InstallPrompt />
  </div>
</template>

<script setup lang="ts">
import { RouterView } from 'vue-router'
import InstallPrompt from './components/InstallPrompt.vue'
</script>

<style>
#app {
  min-height: 100vh;
}
</style>
