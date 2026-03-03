<template>
  <div
    class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
    @click.self="$emit('close')"
  >
    <div class="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col">
      <div class="px-6 py-4 border-b border-slate-200 flex items-center justify-between">
        <h2 class="text-lg font-semibold text-slate-800">
          Detalhes da Ordem de Serviço
        </h2>
        <button
          type="button"
          class="text-slate-500 hover:text-slate-700 p-1"
          @click="$emit('close')"
        >
          <X :size="20" class="stroke-current" />
        </button>
      </div>
      
      <div class="flex-1 overflow-y-auto p-6">
        <div v-if="loading" class="flex items-center justify-center py-12">
          <span class="text-slate-500">Carregando...</span>
        </div>
        
        <div v-else-if="detail" class="space-y-6">
          <!-- Informações Principais -->
          <div class="grid grid-cols-2 gap-4">
            <div>
              <h3 class="text-xs font-semibold text-slate-600 mb-1">Protocolo Principal</h3>
              <p class="text-sm text-slate-800 font-mono">{{ detail.manifestations?.[0]?.protocol || '—' }}</p>
            </div>
            <div>
              <h3 class="text-xs font-semibold text-slate-600 mb-1">Setor</h3>
              <p class="text-sm text-slate-800">{{ detail.sector }}</p>
            </div>
            <div>
              <h3 class="text-xs font-semibold text-slate-600 mb-1">Status</h3>
              <p class="text-sm text-slate-800">{{ detail.status_display }}</p>
            </div>
            <div>
              <h3 class="text-xs font-semibold text-slate-600 mb-1">Engajamento</h3>
              <p class="text-sm text-slate-800">
                <span :class="detail.heat_count > 5 ? 'text-red-600 font-bold' : 'text-amber-600'">
                  {{ detail.heat_count }} afetados
                </span>
              </p>
            </div>
          </div>

          <!-- Mapa -->
          <div v-if="hasMap" class="h-64 rounded-lg border border-slate-200 overflow-hidden bg-slate-100">
            <iframe
              :src="mapEmbedUrl"
              class="w-full h-full border-0"
              title="Localização no mapa"
            />
          </div>

          <!-- Descrição Técnica -->
          <div>
            <h3 class="text-sm font-semibold text-slate-700 mb-2">Descrição Técnica</h3>
            <p class="text-slate-600 whitespace-pre-wrap">{{ detail.technical_summary || 'Sem descrição técnica' }}</p>
          </div>

          <!-- Manifestações Agrupadas -->
          <div v-if="detail.manifestations && detail.manifestations.length > 0">
            <h3 class="text-sm font-semibold text-slate-700 mb-2">
              Manifestações Agrupadas ({{ detail.manifestations.length }})
            </h3>
            <div class="space-y-2">
              <div
                v-for="m in detail.manifestations"
                :key="m.id"
                class="p-3 bg-slate-50 rounded-lg border border-slate-200"
              >
                <p class="text-xs font-mono text-slate-600 mb-1">{{ m.protocol }}</p>
                <p class="text-sm text-slate-700">{{ m.description }}</p>
                <p v-if="m.location_address" class="inline-flex items-center gap-1 text-xs text-slate-500 mt-1">
                  <MapPin :size="12" class="stroke-current" />
                  {{ m.location_address }}
                </p>
              </div>
            </div>
          </div>

          <!-- Fotos do Cidadão -->
          <div v-if="attachments.length > 0">
            <h3 class="text-sm font-semibold text-slate-700 mb-2">Fotos do Cidadão</h3>
            <div class="grid grid-cols-3 gap-2">
              <a
                v-for="att in attachments"
                :key="att.id"
                :href="att.file_url || getMediaUrl(att.file)"
                target="_blank"
                class="block rounded-lg border border-slate-200 overflow-hidden hover:opacity-90"
              >
                <img
                  v-if="att.file_type === 'IMAGE'"
                  :src="att.file_url || getMediaUrl(att.file)"
                  :alt="att.filename"
                  class="w-full h-24 object-cover"
                />
                <div v-else class="w-full h-24 bg-slate-100 flex items-center justify-center text-slate-500 text-xs">
                  PDF/Doc
                </div>
                <p class="p-2 text-xs text-slate-600 truncate">{{ att.filename }}</p>
              </a>
            </div>
          </div>
        </div>
      </div>

      <div class="px-6 py-4 border-t border-slate-200 flex justify-between">
        <button
          type="button"
          class="inline-flex items-center gap-2 px-4 py-2 bg-slate-200 text-slate-700 rounded-lg text-sm font-medium hover:bg-slate-300"
          @click="printOS"
        >
          <Printer :size="16" class="stroke-current" />
          Imprimir Ordem de Serviço
        </button>
        <button
          type="button"
          class="px-4 py-2 bg-slate-200 text-slate-700 rounded-lg text-sm font-medium hover:bg-slate-300"
          @click="$emit('close')"
        >
          Fechar
        </button>
      </div>
    </div>

    <!-- Frame oculto para impressão -->
    <iframe id="print-os-frame" class="hidden" title="Impressão OS" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { X, MapPin, Printer } from '@/utils/icons'
import apiService from '@/services/api'
import type { WorkOrderItem } from '@/stores/sector-board'

const props = defineProps<{
  item: WorkOrderItem
}>()

defineEmits<{ close: [] }>()

const detail = ref<WorkOrderItem | null>(null)
const loading = ref(true)
const attachments = ref<any[]>([])

const apiOrigin = (() => {
  try {
    const base = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'
    return new URL(base).origin
  } catch {
    return 'http://localhost:8000'
  }
})()

function getMediaUrl(url: string | undefined): string {
  if (!url) return ''
  if (url.startsWith('http')) return url
  return `${apiOrigin}${url.startsWith('/') ? url : `/${url}`}`
}

const hasMap = computed(() => {
  if (!detail.value || !detail.value.manifestations?.length) return false
  const firstManifestation = detail.value.manifestations[0]
  return firstManifestation?.latitude != null && firstManifestation?.longitude != null
})

const mapEmbedUrl = computed(() => {
  if (!hasMap.value || !detail.value?.manifestations?.length) return ''
  const m = detail.value.manifestations[0]
  const lat = Number(m.latitude)
  const lon = Number(m.longitude)
  const d = 0.01
  const bbox = [lon - d, lat - d, lon + d, lat + d].join(',')
  return `https://www.openstreetmap.org/export/embed.html?bbox=${encodeURIComponent(bbox)}&layer=mapnik&marker=${lat},${lon}`
})

async function loadDetail() {
  loading.value = true
  try {
    // Buscar detalhes da primeira manifestação para obter mapa e anexos
    if (props.item.manifestations && props.item.manifestations.length > 0) {
      const firstManifestationId = props.item.manifestations[0].id
      const res = await apiService.get(`/reports/manifestations/${firstManifestationId}/`)
      attachments.value = res.data.attachments || []
    }
    detail.value = props.item
  } catch (e: any) {
    console.error('Erro ao carregar detalhes:', e)
    detail.value = props.item
  } finally {
    loading.value = false
  }
}

function printOS() {
  if (!detail.value) return
  
  const firstManifestation = detail.value.manifestations?.[0]
  const address = firstManifestation?.location_address || 'Endereço não informado'
  
  const html = `
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>Ordem de Serviço - ${firstManifestation?.protocol || detail.value.id}</title>
  <style>
    @media print {
      @page { margin: 1cm; }
      body { font-family: Arial, sans-serif; font-size: 12pt; }
      .no-print { display: none; }
      .map-container { display: none !important; }
      .address { font-size: 20pt !important; font-weight: bold; margin: 20px 0; }
      .reference-point { font-size: 14pt !important; margin-top: 10px; }
    }
    body { font-family: Arial, sans-serif; padding: 20px; }
    .header { text-align: center; margin-bottom: 30px; border-bottom: 2px solid #000; padding-bottom: 10px; }
    .logo-placeholder { height: 60px; background: #f0f0f0; display: flex; align-items: center; justify-content: center; margin-bottom: 10px; }
    .section { margin-bottom: 20px; }
    .section h3 { font-size: 14pt; font-weight: bold; margin-bottom: 10px; border-bottom: 1px solid #ccc; padding-bottom: 5px; }
    .address { font-size: 16pt; font-weight: bold; margin: 15px 0; }
    .map-container { width: 100%; height: 300px; border: 1px solid #ccc; margin: 15px 0; }
    .signature { margin-top: 40px; border-top: 1px solid #000; padding-top: 10px; }
    .signature-line { margin-top: 50px; }
  </style>
</head>
<body>
  <div class="header">
    <div class="logo-placeholder">LOGO DA PREFEITURA</div>
    <h1>ORDEM DE SERVIÇO</h1>
    <p><strong>Protocolo:</strong> ${firstManifestation?.protocol || '—'} | <strong>Setor:</strong> ${detail.value.sector}</p>
  </div>
  
  <div class="section">
    <h3>Endereço</h3>
    <div class="address">
      ${address.replace(/</g, '&lt;')}
    </div>
  </div>
  
  ${hasMap.value ? `<div class="section map-container">
    <h3>Localização no Mapa</h3>
    <div class="map-container">
      <iframe src="${mapEmbedUrl.value}" style="width: 100%; height: 100%; border: 0;"></iframe>
    </div>
  </div>` : ''}
  
  <div class="section">
    <h3>Descrição Técnica</h3>
    <p>${(detail.value.technical_summary || 'Sem descrição técnica').replace(/</g, '&lt;').replace(/\n/g, '<br>')}</p>
  </div>
  
  ${detail.value.manifestations && detail.value.manifestations.length > 1 ? `
  <div class="section">
    <h3>Manifestações Agrupadas (${detail.value.manifestations.length})</h3>
    <ul>
      ${detail.value.manifestations.map((m: any) => 
        `<li>${m.protocol} - ${(m.description || '').substring(0, 100).replace(/</g, '&lt;')}</li>`
      ).join('')}
    </ul>
  </div>
  ` : ''}
  
  <div class="signature">
    <div class="signature-line">
      <p>Assinatura da Equipe: _______________________</p>
      <p>Data: ___/___/_____</p>
    </div>
  </div>
</body>
</html>
  `
  
  const frame = document.getElementById('print-os-frame') as HTMLIFrameElement
  if (frame?.contentWindow) {
    frame.contentWindow.document.write(html)
    frame.contentWindow.document.close()
    frame.contentWindow.focus()
    frame.contentWindow.print()
  }
}

onMounted(() => {
  loadDetail()
})
</script>
