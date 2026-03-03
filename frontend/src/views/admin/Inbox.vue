<template>
  <div class="h-screen flex flex-col bg-slate-100">
    <header class="shrink-0 bg-white border-b border-slate-200 px-6 py-4 flex items-center justify-between">
      <div class="flex items-center gap-6">
        <div>
          <h1 class="text-xl font-bold text-slate-800">Cockpit da Ouvidoria</h1>
          <p class="text-sm text-slate-500 mt-0.5">Triagem e operação</p>
        </div>
        <nav class="flex gap-2">
          <router-link
            to="/admin/inbox"
            class="px-3 py-1.5 text-sm font-medium rounded-lg transition-colors"
            :class="$route.name === 'admin-inbox' ? 'bg-slate-800 text-white' : 'text-slate-600 hover:bg-slate-100'"
          >
            Triagem
          </router-link>
          <router-link
            to="/admin/search"
            class="px-3 py-1.5 text-sm font-medium rounded-lg transition-colors"
            :class="$route.name === 'admin-search' ? 'bg-slate-800 text-white' : 'text-slate-600 hover:bg-slate-100'"
          >
            Pesquisar / Monitorar
          </router-link>
        </nav>
      </div>
      <div class="flex items-center gap-3">
        <span class="text-sm text-slate-600">{{ auth.user?.full_name || auth.user?.email || auth.user?.username }}</span>
        <button
          type="button"
          class="text-sm text-slate-500 hover:text-slate-700 underline"
          @click="logout"
        >
          Sair
        </button>
      </div>
    </header>
    <div class="flex-1 flex min-h-0">
      <aside class="w-1/3 max-w-md shrink-0 flex flex-col min-h-0">
        <InboxList />
      </aside>
      <main class="flex-1 min-w-0 flex flex-col min-h-0">
        <InboxDetail />
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import InboxList from '@/components/admin/InboxList.vue'
import InboxDetail from '@/components/admin/InboxDetail.vue'
import { useAdminInboxStore } from '@/stores/admin-inbox'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const store = useAdminInboxStore()
const auth = useAuthStore()

function logout() {
  auth.logout()
  router.push('/login')
}

onMounted(async () => {
  // Garantir que ao montar o componente, sempre seleciona o primeiro item
  await store.fetchList()
  // Se após fetchList não há seleção (lista vazia ou erro), garantir estado limpo
  if (!store.selectedId && store.sortedList.length > 0) {
    store.fetchDetail(store.sortedList[0].id)
  }
})
</script>
