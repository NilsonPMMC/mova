import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import apiService from '@/services/api'

export interface ManifestationData {
  description: string
  location_address?: string
  latitude?: number
  longitude?: number
  is_anonymous: boolean
  origin: string
  category?: string
  citizen_name?: string
  citizen_email?: string
  citizen_cpf?: string
  citizen_phone?: string
}

/** Resultado da análise de IA (rascunho ou pós-envio) para múltiplas demandas (cross-sell) */
export interface DraftAnalysisResult {
  has_multiple_demands?: boolean
  all_demands?: Array<{
    macro_category?: string
    category_detail?: string
    urgency_level?: number
    specific_text?: string
  }>
  [key: string]: unknown
}

export const useManifestationStore = defineStore('manifestation', () => {
  // Estado
  const description = ref<string>('')
  const locationAddress = ref<string>('')
  const latitude = ref<number | null>(null)
  const longitude = ref<number | null>(null)
  const isAnonymous = ref<boolean>(false)
  const origin = ref<string>('web')
  const category = ref<string | null>(null)
  
  // Dados do cidadão (soft auth)
  const citizenName = ref<string>('')
  const citizenEmail = ref<string>('')
  const citizenCpf = ref<string>('')
  const citizenPhone = ref<string>('')
  const citizenCorrection = ref<string>('')
  
  // Análise prévia da IA (inclui has_multiple_demands e all_demands para cross-sell)
  const draftAnalysis = ref<DraftAnalysisResult | null>(null)
  
  // Anexos/Arquivos
  const files = ref<File[]>([])
  const fileDescriptions = ref<string[]>([])
  
  // Estado de submissão
  const isSubmitting = ref<boolean>(false)
  const submittedProtocol = ref<string | null>(null)
  const error = ref<string | null>(null)

  // Computed (CPF, Nome e Telefone são obrigatórios)
  const canSubmit = computed(() => {
    const descOk = description.value.trim().length > 10
    const cpfOk = citizenCpf.value.length === 11
    const nameOk = (citizenName.value || '').trim().length >= 2
    const phoneDigits = (citizenPhone.value || '').replace(/\D/g, '')
    const phoneOk = phoneDigits.length >= 10
    return descOk && !isSubmitting.value && cpfOk && nameOk && phoneOk
  })

  const hasLocation = computed(() => {
    return latitude.value !== null && longitude.value !== null
  })

  // Actions
  function setDescription(value: string) {
    description.value = value
  }

  function setLocation(address: string, lat?: number, lng?: number) {
    locationAddress.value = address
    if (lat !== undefined) {
      // Arredondar latitude para 8 casas decimais
      latitude.value = parseFloat(lat.toFixed(8))
    }
    if (lng !== undefined) {
      // Arredondar longitude para 8 casas decimais
      longitude.value = parseFloat(lng.toFixed(8))
    }
  }

  function setAnonymous(value: boolean) {
    // Mantido apenas por compatibilidade, mas todas manifestações agora são identificadas
    isAnonymous.value = false
  }

  function setOrigin(value: string) {
    origin.value = value
  }

  function setCategory(value: string | null) {
    category.value = value
  }

  function setCitizenData(name: string, email: string, cpf: string, phone?: string) {
    citizenName.value = name
    citizenEmail.value = email
    citizenCpf.value = cpf
    if (phone !== undefined) citizenPhone.value = phone
  }

  async function submitManifestation(): Promise<string | null> {
    if (!canSubmit.value) {
      error.value = 'Por favor, preencha todos os campos obrigatórios.'
      return null
    }

    isSubmitting.value = true
    error.value = null

    try {
      // Se houver arquivos, usar FormData
      const hasFiles = files.value.length > 0
      
      let payload: FormData | any
      let config: any = {}
      
      if (hasFiles) {
        // Criar FormData para multipart/form-data
        payload = new FormData()
        
        // Campos de texto
        payload.append('description', description.value.trim())
        payload.append('origin', origin.value)
        payload.append('is_anonymous', String(isAnonymous.value))
        
        if (locationAddress.value) {
          payload.append('location_address', locationAddress.value)
        }
        
        if (latitude.value !== null && longitude.value !== null) {
          payload.append('latitude', String(parseFloat(latitude.value.toFixed(8))))
          payload.append('longitude', String(parseFloat(longitude.value.toFixed(8))))
        }
        
        if (category.value) {
          payload.append('category', category.value)
        }
        
        // Dados do cidadão (soft auth)
        if (!isAnonymous.value) {
          if (citizenName.value.trim()) {
            payload.append('citizen_name', citizenName.value.trim())
          }
          if (citizenEmail.value.trim()) {
            payload.append('citizen_email', citizenEmail.value.trim())
          }
          if (citizenCpf.value.trim()) {
            payload.append('citizen_cpf', citizenCpf.value.trim())
          }
          if (citizenPhone.value.trim()) {
            payload.append('citizen_phone', citizenPhone.value.trim())
          }
        }
        
        // Correção do cidadão (se houver)
        if (citizenCorrection.value.trim()) {
          payload.append('citizen_correction', citizenCorrection.value.trim())
        }
        
        // Arquivos
        files.value.forEach((file) => {
          payload.append('files', file)
        })
        
        // Descrições dos arquivos (sempre uma por arquivo, para manter ordem)
        fileDescriptions.value.forEach((desc) => {
          payload.append('file_descriptions', typeof desc === 'string' ? desc : '')
        })
        // Se tiver mais arquivos que descrições, completar com string vazia
        for (let i = fileDescriptions.value.length; i < files.value.length; i++) {
          payload.append('file_descriptions', '')
        }
        
        // Não definir Content-Type: o interceptor remove e o browser define
        // multipart/form-data com boundary automaticamente
        config = {}
      } else {
        // Sem arquivos, usar JSON normal
        payload = {
          description: description.value.trim(),
          origin: origin.value,
          is_anonymous: isAnonymous.value,
        }

        if (locationAddress.value) {
          payload.location_address = locationAddress.value
        }

        if (latitude.value !== null && longitude.value !== null) {
          payload.latitude = parseFloat(latitude.value.toFixed(8))
          payload.longitude = parseFloat(longitude.value.toFixed(8))
        }

        if (category.value) {
          payload.category = category.value
        }

        // Dados do cidadão (soft auth)
        if (!isAnonymous.value) {
          if (citizenName.value.trim()) {
            payload.citizen_name = citizenName.value.trim()
          }
          if (citizenEmail.value.trim()) {
            payload.citizen_email = citizenEmail.value.trim()
          }
          if (citizenCpf.value.trim()) {
            payload.citizen_cpf = citizenCpf.value.trim()
          }
          if (citizenPhone.value.trim()) {
            payload.citizen_phone = citizenPhone.value.trim()
          }
        }

        // Correção do cidadão (se houver)
        if (citizenCorrection.value.trim()) {
          payload.citizen_correction = citizenCorrection.value.trim()
        }
      }

      const response = await apiService.post('/reports/manifestations/', payload, config)
      
      submittedProtocol.value = response.data.protocol
      return response.data.protocol
    } catch (err: any) {
      error.value = err.response?.data?.message || err.response?.data?.error || 'Erro ao enviar manifestação. Tente novamente.'
      console.error('Erro ao enviar manifestação:', err)
      return null
    } finally {
      isSubmitting.value = false
    }
  }

  function setCitizenCorrection(value: string) {
    citizenCorrection.value = value
  }

  function setDraftAnalysis(analysis: DraftAnalysisResult | null) {
    draftAnalysis.value = analysis
  }

  /**
   * Prepara o rascunho para registrar uma nova demanda (cross-sell).
   * Limpa protocolo e análise; mantém cidadão e localização; define a descrição como o trecho da demanda.
   */
  function startNewDemandFromCrossSell(demand: { specific_text?: string }) {
    submittedProtocol.value = null
    draftAnalysis.value = null
    error.value = null
    description.value = (demand.specific_text || '').trim() || description.value
  }

  function setFiles(filesList: File[], descriptions: string[] = []) {
    files.value = filesList
    fileDescriptions.value = descriptions.length === filesList.length 
      ? descriptions 
      : [...descriptions, ...new Array(filesList.length - descriptions.length).fill('')]
  }

  function reset() {
    description.value = ''
    locationAddress.value = ''
    latitude.value = null
    longitude.value = null
    isAnonymous.value = false
    origin.value = 'web'
    category.value = null
    citizenName.value = ''
    citizenEmail.value = ''
    citizenCpf.value = ''
    citizenPhone.value = ''
    citizenCorrection.value = ''
    draftAnalysis.value = null
    files.value = []
    fileDescriptions.value = []
    isSubmitting.value = false
    submittedProtocol.value = null
    error.value = null
  }

  return {
    // State
    description,
    locationAddress,
    latitude,
    longitude,
    isAnonymous,
    origin,
    category,
    citizenName,
    citizenEmail,
    citizenCpf,
    citizenPhone,
    citizenCorrection,
    draftAnalysis,
    files,
    fileDescriptions,
    isSubmitting,
    submittedProtocol,
    error,
    // Computed
    canSubmit,
    hasLocation,
    // Actions
    setDescription,
    setLocation,
    setAnonymous,
    setOrigin,
    setCategory,
    setCitizenData,
    setCitizenCorrection,
    setDraftAnalysis,
    setFiles,
    submitManifestation,
    startNewDemandFromCrossSell,
    reset,
  }
})
