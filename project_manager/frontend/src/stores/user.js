import { defineStore } from 'pinia'
import { api } from '../api'

export const useUserStore = defineStore('user', {
  state: () => ({
    token: localStorage.getItem('token') || '',
    user: JSON.parse(localStorage.getItem('user') || 'null'),
  }),
  getters: {
    isLoggedIn: (state) => !!state.token,
    isAdmin: (state) => state.user?.role === 'admin',
    isManager: (state) => state.user?.role === 'admin' || state.user?.role === 'pm',
    roleLabel(state) {
      const map = { admin: '管理员', pm: '项目经理', dev: '开发人员', tester: '测试人员', ops: '运维人员' }
      return map[state.user?.role] || ''
    },
  },
  actions: {
    setAuth(token, user) {
      this.token = token
      this.user = user
      localStorage.setItem('token', token)
      localStorage.setItem('user', JSON.stringify(user))
      localStorage.setItem('role', user.role)
    },
    logout() {
      this.token = ''
      this.user = null
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      localStorage.removeItem('role')
    },
    async fetchMe() {
      const user = await api.me()
      this.user = user
      localStorage.setItem('user', JSON.stringify(user))
      localStorage.setItem('role', user.role)
      return user
    },
    async updateMe(data) {
      const user = await api.updateMe(data)
      this.user = user
      localStorage.setItem('user', JSON.stringify(user))
      localStorage.setItem('role', user.role)
      return user
    },
  },
})