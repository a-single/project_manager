import { defineStore } from 'pinia'
import { api } from '../api'

const ROLE_LABELS = {
  admin: '管理员',
  pm: '项目经理',
  dev: '开发人员',
  tester: '测试人员',
  ops: '运维人员',
}

export const useUserStore = defineStore('user', {
  state: () => ({
    token: localStorage.getItem('token') || '',
    user: JSON.parse(localStorage.getItem('user') || 'null'),
  }),
  getters: {
    isAdmin: (s) => s.user?.role === 'admin',
    isPM: (s) => s.user?.role === 'pm' || s.user?.role === 'admin',
    roleLabel: (s) => ROLE_LABELS[s.user?.role] || s.user?.role || '',
  },
  actions: {
    async login(username, password) {
      const data = await api.auth.login({ username, password })
      this.token = data.token
      this.user = data.user
      localStorage.setItem('token', data.token)
      localStorage.setItem('user', JSON.stringify(data.user))
    },
    async refreshMe() {
      if (!this.token) return
      this.user = await api.auth.me()
      localStorage.setItem('user', JSON.stringify(this.user))
    },
    logout() {
      this.token = ''
      this.user = null
      localStorage.removeItem('token')
      localStorage.removeItem('user')
    },
  },
})