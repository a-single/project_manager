import { defineStore } from 'pinia'
import { ElNotification } from 'element-plus'
import { api } from '../api'
import { playNotifySound } from '../utils/sound'

export const useNotificationStore = defineStore('notification', {
  state: () => ({
    count: 0,
    hasNew: false,
    timer: null,
  }),
  actions: {
    async refresh({ notify = true } = {}) {
      try {
        const res = await api.notifications.unread()
        const newCount = res.count
        const increased = newCount > this.count
        this.hasNew = increased
        if (increased && notify) {
          playNotifySound()
          const items = await api.notifications.list({ unread_only: true })
          const top = items[0]
          if (top) {
            const config = {
              task_assigned: { title: '新任务提醒', type: 'warning' },
              task_completed: { title: '任务完成通知', type: 'success' },
              task_approved: { title: '任务确认通知', type: 'success' },
              task_rejected: { title: '任务驳回通知', type: 'error' },
            }[top.type] || { title: '消息提醒', type: 'info' }
            ElNotification({
              title: config.title,
              message: top.message,
              type: config.type,
              duration: 6000,
            })
          }
        }
        this.count = newCount
        return newCount
      } catch (e) {
        /* 网络异常时静默，避免频繁提示 */
        return this.count
      }
    },
    startPolling(interval = 8000) {
      this.refresh({ notify: false })
      this.stopPolling()
      this.timer = setInterval(() => this.refresh(), interval)
    },
    stopPolling() {
      if (this.timer) {
        clearInterval(this.timer)
        this.timer = null
      }
    },
  },
})