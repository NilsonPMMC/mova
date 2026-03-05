<template>
  <div class="min-h-screen bg-slate-100">
    <header class="bg-white border-b border-slate-200 px-6 py-4">
      <div class="flex items-center justify-between">
        <div>
          <h1 class="text-xl font-bold text-slate-800">
            Board de Execução
            <span v-if="!auth.user?.is_superuser && auth.user?.sector">
              — Setor: {{ auth.user.sector }}
            </span>
            <span v-else-if="store.sector">
              — {{ sectorLabel }}
            </span>
          </h1>
          <p class="text-sm text-slate-500 mt-0.5">Organize o dia da equipe de rua</p>
        </div>
        <div class="flex items-center gap-3">
          <!-- Debug: mostrar informações do usuário -->
          <div v-if="false" class="text-xs text-red-500">
            Debug: is_superuser={{ auth.user?.is_superuser }}, sector={{ auth.user?.sector }}
          </div>
          
          <!-- Superadmin pode trocar de setor -->
          <select
            v-if="auth.user?.is_superuser === true"
            v-model="selectedSector"
            class="border border-slate-300 rounded-lg px-3 py-2 text-sm"
            @change="onSectorChange"
          >
            <option value="">Selecione o setor</option>
            <option v-for="s in sectors" :key="s" :value="s">{{ s }}</option>
          </select>
          <!-- User comum: apenas mostra o setor fixo -->
          <div v-else-if="auth.user?.sector" class="px-3 py-2 bg-slate-100 rounded-lg text-sm text-slate-700">
            Setor: {{ auth.user.sector }}
          </div>
          <!-- Se não tem setor e não é superadmin, mostrar aviso -->
          <div v-else-if="auth.user && !auth.user.is_superuser" class="inline-flex items-center gap-2 px-3 py-2 bg-yellow-100 rounded-lg text-sm text-yellow-800">
            <AlertTriangle :size="16" class="stroke-current" />
            Usuário sem setor atribuído
          </div>
          <button
            v-if="store.scheduled.length"
            type="button"
            class="px-4 py-2 rounded-lg bg-slate-700 text-white text-sm font-medium hover:bg-slate-800"
            @click="printScheduled"
          >
            Imprimir Ordens do Cronograma ({{ store.scheduled.length }})
          </button>
          <button
            type="button"
            class="px-4 py-2 rounded-lg border border-slate-300 text-slate-700 text-sm font-medium hover:bg-slate-100"
            @click="handleLogout"
          >
            Sair
          </button>
        </div>
      </div>
    </header>
    <main class="p-4">
      <div v-if="store.loading && !store.entrada.length && !store.workOrders.length" class="flex justify-center py-12">
        <span class="text-slate-500">Carregando...</span>
      </div>
      <SectorKanban v-else-if="store.sector" ref="kanbanRef" />
      <div v-else class="flex justify-center py-12 text-slate-500">
        Selecione um setor acima para carregar o board.
      </div>
    </main>
    <iframe id="print-frame" class="hidden" title="Impressão OS" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { AlertTriangle } from '@/utils/icons'
import SectorKanban from '@/components/sector/SectorKanban.vue'
import { useSectorBoardStore } from '@/stores/sector-board'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const store = useSectorBoardStore()
const auth = useAuthStore()

const sectors = ['OBRAS', 'SAUDE', 'ZELADORIA', 'TRANSPORTE', 'EDUCACAO', 'SEGURANCA', 'MEIO_AMBIENTE', 'ILUMINACAO']

const selectedSector = ref('')
const kanbanRef = ref<InstanceType<typeof SectorKanban> | null>(null)

const sectorLabel = computed(() => {
  const s = store.sector || selectedSector.value
  if (!s) return '—'
  return sectors.includes(s) ? s : s
})

function onSectorChange() {
  store.setSector(selectedSector.value)
}

async function initializeSector() {
  auth.checkAuth()

  if (auth.user && auth.user.is_superuser === false && auth.user.sector) {
    const s = auth.user.sector
    selectedSector.value = s
    if (store.sector !== s) await store.setSector(s)
  } else if (auth.user?.is_superuser === true) {
    const sectorFromRoute = (route.params.sector as string) || (route.query.sector as string) || ''
    if (sectorFromRoute) {
      const s = sectorFromRoute.toUpperCase()
      selectedSector.value = s
      if (store.sector !== s) await store.setSector(s)
    }
  }
}

// Watch para reagir quando o usuário mudar (ex: após login)
watch(() => auth.user, async (newUser) => {
  if (newUser) {
    await initializeSector()
  }
}, { immediate: false })

onMounted(async () => {
  await initializeSector()
})

function printScheduled() {
  const items = store.scheduled
  if (!items.length) return
  const html = buildPrintHtml(items)
  const frame = document.getElementById('print-frame') as HTMLIFrameElement
  if (frame?.contentWindow) {
    frame.contentWindow.document.write(html)
    frame.contentWindow.document.close()
    frame.contentWindow.focus()
    frame.contentWindow.print()
  }
}

function handleLogout() {
  auth.logout()
  router.push({ name: 'login' })
}

function buildPrintHtml(items: any[]): string {
  // Layout de Lista Zebrada (Tabela) para relatório agrupado
  const rows = items.map((wo, idx) => {
    const firstManifestation = wo.manifestations?.[0]
    const address = firstManifestation?.location_address || 'Endereço não informado'
    const summary = wo.technical_summary || 'Sem resumo técnico'
    const priority = wo.heat_count > 5 ? '🔴 Alta' : wo.heat_count > 2 ? '🟡 Média' : '🟢 Baixa'
    
    return `
      <tr style="background-color: ${idx % 2 === 0 ? '#f9fafb' : '#ffffff'};">
        <td style="padding: 8px; border-bottom: 1px solid #e5e7eb; font-family: monospace; font-size: 11pt;">${firstManifestation?.protocol || wo.id}</td>
        <td style="padding: 8px; border-bottom: 1px solid #e5e7eb; font-size: 11pt;">${address.replace(/</g, '&lt;')}</td>
        <td style="padding: 8px; border-bottom: 1px solid #e5e7eb; font-size: 11pt;">${summary.substring(0, 100).replace(/</g, '&lt;')}${summary.length > 100 ? '...' : ''}</td>
        <td style="padding: 8px; border-bottom: 1px solid #e5e7eb; font-size: 11pt; text-align: center;">${priority}</td>
      </tr>
    `
  }).join('')
  
  return `
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>Cronograma de Serviços — ${store.sector || 'Setor'}</title>
  <style>
    @media print {
      @page { margin: 1cm; }
      body { font-family: Arial, sans-serif; font-size: 11pt; }
    }
    body { font-family: Arial, sans-serif; padding: 20px; }
    .header { text-align: center; margin-bottom: 20px; border-bottom: 2px solid #000; padding-bottom: 10px; }
    .logo-placeholder { height: 50px; background: #f0f0f0; display: flex; align-items: center; justify-content: center; margin-bottom: 10px; }
    table { width: 100%; border-collapse: collapse; margin-top: 15px; }
    th { background-color: #1e40af; color: white; padding: 10px; text-align: left; font-weight: bold; font-size: 11pt; }
    td { padding: 8px; border-bottom: 1px solid #e5e7eb; font-size: 11pt; }
    .footer { margin-top: 30px; padding-top: 10px; border-top: 1px solid #000; font-size: 10pt; }
  </style>
</head>
<body>
  <div class="header">
    <div class="logo-placeholder">LOGO DA PREFEITURA</div>
    <h1>CRONOGRAMA DE SERVIÇOS</h1>
    <p><strong>Setor:</strong> ${store.sector || '—'} | <strong>Data:</strong> ${new Date().toLocaleDateString('pt-BR')}</p>
  </div>
  
  <table>
    <thead>
      <tr>
        <th style="width: 15%;">Protocolo</th>
        <th style="width: 30%;">Endereço</th>
        <th style="width: 45%;">Problema (Resumo)</th>
        <th style="width: 10%;">Prioridade</th>
      </tr>
    </thead>
    <tbody>
      ${rows}
    </tbody>
  </table>
  
  <div class="footer">
    <p><strong>Total de Ordens:</strong> ${items.length}</p>
    <p style="margin-top: 20px;">Assinatura do Encarregado: _______________________ Data: ___/___/_____</p>
  </div>
</body>
</html>
  `
}
</script>
