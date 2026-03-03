import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import './style.css'
import './utils/debug-auth'

// O vite-plugin-pwa registra o Service Worker automaticamente
// Não é necessário registrar manualmente

const app = createApp(App)

app.use(createPinia())
app.use(router)

app.mount('#app')
