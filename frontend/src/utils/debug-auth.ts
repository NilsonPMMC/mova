/**
 * Utilitário de debug para verificar dados de autenticação
 * Use no console do navegador: window.debugAuth()
 */
export function debugAuth() {
  const authUser = localStorage.getItem('auth_user')
  const token = localStorage.getItem('access_token')
  
  console.log('=== DEBUG AUTH ===')
  console.log('Token:', token ? 'Presente' : 'Ausente')
  console.log('Auth User (raw):', authUser)
  
  if (authUser) {
    try {
      const parsed = JSON.parse(authUser)
      console.log('Auth User (parsed):', parsed)
      console.log('is_superuser:', parsed.is_superuser)
      console.log('sector:', parsed.sector)
    } catch (e) {
      console.error('Erro ao parsear auth_user:', e)
    }
  }
  
  return { token, authUser }
}

// Disponibilizar globalmente para debug
if (typeof window !== 'undefined') {
  (window as any).debugAuth = debugAuth
}
