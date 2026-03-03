import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import NewManifestation from '../views/NewManifestation.vue'
import TrackProtocol from '../views/TrackProtocol.vue'
import MyManifestations from '../views/MyManifestations.vue'
import Inbox from '../views/admin/Inbox.vue'
import GlobalSearch from '../views/admin/GlobalSearch.vue'
import Login from '../views/Login.vue'
import ExecutionBoard from '../views/sector/ExecutionBoard.vue'
import { useAuthStore } from '../stores/auth'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView
    },
    {
      path: '/login',
      name: 'login',
      component: Login
    },
    {
      path: '/nova-manifestacao',
      name: 'new-manifestation',
      component: NewManifestation
    },
    {
      path: '/acompanhar',
      name: 'track-protocol',
      component: TrackProtocol
    },
    {
      path: '/minhas-manifestacoes',
      name: 'my-manifestations',
      component: MyManifestations
    },
    {
      path: '/admin/inbox',
      name: 'admin-inbox',
      component: Inbox,
      meta: { requiresAuth: true }
    },
    {
      path: '/admin/search',
      name: 'admin-search',
      component: GlobalSearch,
      meta: { requiresAuth: true }
    },
    {
      path: '/sector',
      name: 'sector-board',
      component: ExecutionBoard,
      meta: { requiresAuth: true }
    },
    {
      path: '/sector/:sector',
      name: 'sector-board-sector',
      component: ExecutionBoard,
      meta: { requiresAuth: true }
    }
  ]
})

router.beforeEach((to, _from, next) => {
  const auth = useAuthStore()
  auth.checkAuth()
  
  // Verificar autenticação básica
  if (to.meta.requiresAuth && !auth.isAuthenticated) {
    next({ name: 'login', query: { redirect: to.fullPath } })
    return
  }
  
  // Se não está autenticado, prosseguir normalmente
  if (!auth.isAuthenticated || !auth.user) {
    next()
    return
  }
  
  const user = auth.user
  const isSuperuser = user.is_superuser === true
  const hasSector = !!user.sector && user.sector.trim() !== ''
  const isStaff = user.is_staff === true
  
  // Regra 1: /admin/inbox e /admin/search - Apenas Superusuários e Grupo "Ouvidoria"
  // LÓGICA ESTRITA: Se tem setor definido E NÃO é superadmin, BLOQUEAR acesso a /admin
  if (to.path.startsWith('/admin')) {
    // Se tem setor E não é superadmin, bloquear completamente
    if (hasSector && !isSuperuser) {
      // Chuta para o board do setor dele
      next({ name: 'sector-board', query: { sector: user.sector } })
      return
    }
    // Se não tem setor mas também não é superadmin nem staff, bloquear
    if (!isSuperuser && !isStaff) {
      // Sem setor e sem permissão: redirecionar para home
      next({ name: 'home' })
      return
    }
  }
  
  // Regra 2: /sector - Apenas usuários com sector ou superusuários
  if (to.path.startsWith('/sector')) {
    if (!isSuperuser && !hasSector) {
      // Sem setor e não é superadmin: redirecionar
      if (isStaff) {
        // Staff sem setor: pode ir para admin
        next({ name: 'admin-inbox' })
      } else {
        next({ name: 'home' })
      }
      return
    }
  }
  
  next()
})

export default router
