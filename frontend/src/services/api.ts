import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1',
  timeout: 30000, // Aumentado para uploads de arquivos (30s)
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor
api.interceptors.request.use(
  (config) => {
    // DRF TokenAuthentication espera "Token <key>", não "Bearer"
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Token ${token}`
    }
    
    // Se for FormData, remover Content-Type para o browser definir automaticamente
    // (incluindo boundary para multipart/form-data)
    if (config.data instanceof FormData && config.headers) {
      delete config.headers['Content-Type']
    }
    
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      localStorage.removeItem('auth_user')
    }
    return Promise.reject(error)
  }
)

const apiService = {
  get: (url: string, config?: any) => api.get(url, config),
  post: (url: string, data?: any, config?: any) => api.post(url, data, config),
  put: (url: string, data?: any, config?: any) => api.put(url, data, config),
  patch: (url: string, data?: any, config?: any) => api.patch(url, data, config),
  delete: (url: string, config?: any) => api.delete(url, config),
  async getNearestPartners(lat: number, lon: number, animalType?: string) {
    try {
      const params = new URLSearchParams({
        lat: lat.toString(),
        lon: lon.toString()
      })
      if (animalType) {
        params.append('animal_type', animalType)
      }
      const response = await api.get(`/reports/nearest-partners/?${params.toString()}`)
      return response.data
    } catch (error) {
      console.error('Erro ao buscar parceiros próximos:', error)
      return []
    }
  },
}

export default apiService
