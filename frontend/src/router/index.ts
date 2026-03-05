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

  // ——— TRAVA: rota exige auth e não está autenticado ———
  if (to.meta.requiresAuth && !auth.isAuthenticated) {
    if (to.path === '/login') {
      return next()
    }
    return next({ name: 'login', query: { redirect: to.fullPath } })
  }

  // ——— TRAVA: autenticado tentando acessar login ———
  if (to.path === '/login' && auth.isAuthenticated) {
    return next({ name: 'home' })
  }

  // Sem usuário carregado ainda: liberar (evita loop em rotas públicas)
  if (!auth.isAuthenticated || !auth.user) {
    return next()
  }

  const user = auth.user
  const isSuperuser = user.is_superuser === true
  const hasSector = !!user.sector && user.sector.trim() !== ''
  const isStaff = user.is_staff === true

  // ——— Regra ADMIN: tem setor e não é super → vai para /sector ———
  if (to.path.startsWith('/admin')) {
    if (hasSector && !isSuperuser) {
      if (to.path.startsWith('/sector')) return next()
      return next({ name: 'sector-board', query: { sector: user.sector } })
    }
    if (!isSuperuser && !isStaff) {
      if (to.path === '/') return next()
      return next({ name: 'home' })
    }
  }

  // ——— Regra SECTOR: sem setor e não é super → redireciona ———
  if (to.path.startsWith('/sector')) {
    if (!isSuperuser && !hasSector) {
      if (isStaff) {
        if (to.path.startsWith('/admin')) return next()
        return next({ name: 'admin-inbox' })
      }
      if (to.path === '/') return next()
      return next({ name: 'home' })
    }
  }

  return next()
})

export default router
