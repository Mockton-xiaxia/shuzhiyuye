import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import http from '@/api/http'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('fishery_token') || '')
  const user = ref(JSON.parse(localStorage.getItem('fishery_user') || 'null'))
  const roles = ref([])
  const permissions = ref([])
  const menus = ref([])
  const portal = computed(() => user.value?.portal || 'GOV')

  async function login(username, password) {
    const res = await http.post('/auth/login', { username, password, rememberMe: true })
    token.value = res.data.accessToken
    user.value = res.data.user
    roles.value = res.data.roles || []
    permissions.value = res.data.permissions || []
    localStorage.setItem('fishery_token', token.value)
    localStorage.setItem('fishery_user', JSON.stringify(user.value))
    await fetchMe()
    return res.data
  }

  async function fetchMe() {
    const res = await http.get('/auth/me')
    user.value = res.data.user
    roles.value = res.data.roles || []
    permissions.value = res.data.permissions || []
    menus.value = res.data.menus || []
    localStorage.setItem('fishery_user', JSON.stringify(user.value))
  }

  function logout() {
    token.value = ''
    user.value = null
    roles.value = []
    permissions.value = []
    menus.value = []
    localStorage.removeItem('fishery_token')
    localStorage.removeItem('fishery_user')
  }

  return { token, user, roles, permissions, menus, portal, login, fetchMe, logout }
})
