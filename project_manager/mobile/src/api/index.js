import axios from 'axios'

const http = axios.create({ baseURL: '/api', timeout: 20000 })

http.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

http.interceptors.response.use(
  (res) => res.data,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      const loc = window.location
      const login = `#/login?redirect=${encodeURIComponent(loc.hash.slice(1))}`
      if (!loc.hash.includes('/login')) {
        window.location.hash = login
      }
    }
    const detail = err.response?.data?.detail
    if (typeof detail === 'string') throw new Error(detail)
    if (Array.isArray(detail) && detail[0]?.msg) throw new Error(detail[0].msg)
    if (err.response?.status === 404) throw new Error('资源不存在')
    throw new Error(err.message || '网络错误')
  },
)

export const api = {
  auth: {
    login: (data) => http.post('/auth/login', data),
    me: () => http.get('/users/me'),
  },
  users: {
    list: () => http.get('/users'),
  },
  projects: {
    list: () => http.get('/projects'),
    get: (id) => http.get(`/projects/${id}`),
    remove: (id) => http.delete(`/projects/${id}`),
    archived: (params) => http.get('/projects/archived', { params }),
    archive: (id) => http.post(`/projects/${id}/archive`),
    unarchive: (id) => http.post(`/projects/${id}/unarchive`),
    members: (id) => http.get(`/projects/${id}/members`),
    candidates: (id) => http.get(`/projects/${id}/candidates`),
    create: (name, description) => http.post('/projects', { name, description }),
    setMember: (id, data) => http.post(`/projects/${id}/members`, data),
    removeMember: (id, userId) => http.delete(`/projects/${id}/members/${userId}`),
  },
  tasks: {
    list: (params) => http.get('/tasks', { params }),
    create: (projectId, data) => http.post(`/projects/${projectId}/tasks`, data),
    complete: (id, formData) =>
      http.post(`/tasks/${id}/complete`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      }),
    approve: (id, comment = '') => {
      const fd = new FormData()
      if (comment) fd.append('comment', comment)
      return http.post(`/tasks/${id}/approve`, fd)
    },
    reject: (id, comment) => {
      const fd = new FormData()
      fd.append('comment', comment)
      return http.post(`/tasks/${id}/reject`, fd)
    },
    // 移动端附件下载：直接跳转触发系统下载
    attachmentUrl: (id) => `${axios.defaults.baseURL}/attachments/${id}/download`,
  },
  notifications: {
    list: (params) => http.get('/notifications', { params }),
    unreadCount: () => http.get('/notifications/unread-count'),
    markRead: () => http.put('/notifications/read-all'),
  },
  stats: {
    tasks: (params) => http.get('/stats/task-records', { params }),
    overdueCounts: (projectId) => http.get('/stats/overdue-counts', { params: { project_id: projectId } }),
  },
  report: {
    mine: (params) => http.get('/report/mine', { params }),
  },
}

export default api