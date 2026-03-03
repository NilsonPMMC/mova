import { defineStore } from 'pinia'
import { ref } from 'vue'
import apiService from '@/services/api'

const AUTH_USER_KEY = 'auth_user'

export interface AuthUser {
  id: number
  email: string
  username: string
  full_name?: string
  sector?: string | null
  is_superuser?: boolean
  is_staff?: boolean
}

interface LoginCredentials {
  username: string
  password: string
}

export const useAuthStore = defineStore('auth', () => {
  const user = ref<AuthUser | null>(loadStoredUser())
  const token = ref<string | null>(localStorage.getItem('access_token'))

  const isAuthenticated = ref(!!token.value)

  function loadStoredUser(): AuthUser | null {
    try {
      const raw = localStorage.getItem(AUTH_USER_KEY)
      return raw ? JSON.parse(raw) : null
    } catch {
      return null
    }
  }

  const login = async (credentials: LoginCredentials) => {
    try {
      const response = await apiService.post('/auth/login/', credentials)
      const { token: newToken, user: userData } = response.data

      localStorage.setItem('access_token', newToken)
      localStorage.setItem(AUTH_USER_KEY, JSON.stringify(userData))
      token.value = newToken
      user.value = userData
      isAuthenticated.value = true

      return { success: true }
    } catch (error: any) {
      return {
        success: false,
        error: error.response?.data?.detail || 'Erro ao fazer login',
      }
    }
  }

  const logout = () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem(AUTH_USER_KEY)
    token.value = null
    user.value = null
    isAuthenticated.value = false
  }

  const checkAuth = () => {
    const t = localStorage.getItem('access_token')
    token.value = t
    isAuthenticated.value = !!t
    // Sempre recarregar dados do usuário do localStorage para garantir dados atualizados
    if (t) {
      const storedUser = loadStoredUser()
      if (storedUser) {
        user.value = storedUser
      }
    } else {
      user.value = null
    }
  }

  return {
    user,
    token,
    isAuthenticated,
    login,
    logout,
    checkAuth,
  }
})
