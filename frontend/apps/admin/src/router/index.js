import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import catalog from '@/catalog/features.json'

const featurePaths = [...(catalog.GOV || []), ...(catalog.ENT || [])]
  .filter((f) => f.shape !== 'screen')
  .map((f) => ({
    path: f.path.replace(/^\//, ''),
    component: () => import('@/views/FeaturePage.vue'),
    meta: { feature: f.path },
  }))

const routes = [
  { path: '/login', name: 'login', component: () => import('@/views/Login.vue'), meta: { public: true } },
  { path: '/p/trace/:code', name: 'public-trace', component: () => import('@/views/PublicTrace.vue'), meta: { public: true } },
  { path: '/gov/cockpit', name: 'gov-cockpit', component: () => import('@/views/Cockpit.vue') },
  { path: '/ent/screen', name: 'ent-screen', component: () => import('@/views/EntScreen.vue') },
  { path: '/screen/home', redirect: '/gov/cockpit' },
  {
    path: '/',
    component: () => import('@/layouts/MainLayout.vue'),
    redirect: () => {
      const auth = useAuthStore()
      return auth.portal === 'ENT' ? '/ent/workbench' : '/gov/workbench'
    },
    children: [
      { path: 'workbench', redirect: () => {
        const auth = useAuthStore()
        return auth.portal === 'ENT' ? '/ent/workbench' : '/gov/workbench'
      }},
      ...featurePaths,
      // fallback legacy aliases
      { path: 'gov/map', component: () => import('@/components/GisMapPage.vue') },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach(async (to) => {
  if (to.meta.public) return true
  const auth = useAuthStore()
  if (!auth.token) return '/login'
  if (!auth.menus.length) {
    try {
      await auth.fetchMe()
    } catch {
      auth.logout()
      return '/login'
    }
  }
  return true
})

export default router
