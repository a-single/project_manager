import { defineStore } from 'pinia'
import { api } from '../api'
import { playNotifySound } from '../utils/sound'

const TYPE_LABELS = {
  task_assigned: { label: '派发', cls: 'tag-primary' },
  task_completed: { label: '完成', cls: 'tag-success' },
  task_approved: { label: '确认', cls: 'tag-success' },
  task_rejected: { label: '驳回', cls: 'tag-danger' },
}

export const useNotificationStore = defineStore('notification', {
  state: () => ({
    items: [],
    unread: 0,
    pollTimer: null,
    firstMute: false,
  }),
  actions: {
    typeLabel(t) {
      return TYPE_LABELS[t] || { label: '消息', cls: 'tag-gray' }
    },
    async load({ unreadOnly = false } = {}) {
      try {
        this.items = await api.notifications.list({
          unread_only: unreadOnly,
          limit: 30,
        })
      } catch {
        /* 忽略静默失败 */
      }
    },
    async refreshUnread() {
      try {
        const r = await api.notifications.unreadCount()
        if (r && typeof r.count === 'number') {
          // 首次进入静音，避免历史未读一进来就响；之后未读增加才提醒
          if (this.firstMute && r.count > this.unread) {
            playNotifySound()
          }
          this.firstMute = true
          this.unread = r.count
        }
      } catch {
        /* 忽略 */
      }
    },
    async markAllRead() {
      try {
        await api.notifications.markRead()
        this.unread = 0
        await this.load({ unreadOnly: true })
      } catch {
        /* 忽略 */
      }
    },
    startPolling() {
      this.stopPolling()
      this.refreshUnread()
      this.pollTimer = setInterval(() => this.refreshUnread(), 8000)
    },
    stopPolling() {
      if (this.pollTimer) {
        clearInterval(this.pollTimer)
        this.pollTimer = null
      }
    },
  },
})