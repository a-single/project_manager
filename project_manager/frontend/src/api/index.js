import axios from 'axios'

const http = axios.create({ baseURL: '/api', timeout: 30000 })

http.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

http.interceptors.response.use(
  (res) => res.data,
  (err) => {
    const status = err.response?.status
    if (status === 401 && !window.location.pathname.startsWith('/login')) {
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    const msg =
      err.response?.data?.detail || err.message || '请求失败'
    return Promise.reject(new Error(typeof msg === 'string' ? msg : JSON.stringify(msg)))
  },
)

export const api = {
  login: (data) => http.post('/auth/login', data),
  me: () => http.get('/auth/me'),
  updateMe: (data) => http.put('/users/me', data),
  users: {
    list: () => http.get('/users'),
    create: (data) => http.post('/users', data),
    update: (id, data) => http.put(`/users/${id}`, data),
    remove: (id) => http.delete(`/users/${id}`),
  },
  projects: {
    list: () => http.get('/projects'),
    create: (data) => http.post('/projects', data),
    get: (id) => http.get(`/projects/${id}`),
    remove: (id) => http.delete(`/projects/${id}`),
    archived: (params) => http.get('/projects/archived', { params }),
    archive: (id) => http.post(`/projects/${id}/archive`),
    unarchive: (id) => http.post(`/projects/${id}/unarchive`),
    members: (id) => http.get(`/projects/${id}/members`),
    candidates: (id) => http.get(`/projects/${id}/candidates`),
    addMember: (id, userId) => http.post(`/projects/${id}/members`, { user_id: userId }),
    removeMember: (id, userId) => http.delete(`/projects/${id}/members/${userId}`),
  },
  tasks: {
    list: (params) => http.get('/tasks', { params }),
    get: (id) => http.get(`/tasks/${id}`),
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
    download: async (attachmentId, fileName) => {
      const blob = await http.get(`/attachments/${attachmentId}/download`, {
        responseType: 'blob',
      })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = fileName
      a.click()
      URL.revokeObjectURL(url)
    },
  },
  notifications: {
    list: (params) => http.get('/notifications', { params }),
    unread: () => http.get('/notifications/unread-count'),
    read: (id) => http.put(`/notifications/${id}/read`),
    readAll: () => http.put('/notifications/read-all'),
  },
  stats: {
    tasks: (params) => http.get('/stats/task-records', { params }),
    overdueCounts: (projectId) => http.get('/stats/overdue-counts', { params: { project_id: projectId } }),
  },
  report: {
    mine: (params) => http.get('/report/mine', { params }),
  },
}

export default http