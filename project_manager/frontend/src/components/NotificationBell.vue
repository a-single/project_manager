<template>
  <el-popover
    placement="bottom-end"
    :width="360"
    trigger="click"
    @show="load"
  >
    <template #reference>
      <el-badge :value="notificationStore.count" :hidden="notificationStore.count === 0" :max="99">
        <el-button :icon="Bell" circle text />
      </el-badge>
    </template>

    <div class="notif-panel">
      <div class="notif-head">
        <span>消息提醒</span>
        <el-button link type="primary" size="small" :disabled="items.length === 0" @click="markAll">
          全部已读
        </el-button>
      </div>
      <el-scrollbar max-height="320px">
        <div v-if="items.length === 0" class="empty">暂无消息</div>
        <div
          v-for="n in items"
          :key="n.id"
          class="notif-item"
          :class="{ unread: !n.is_read }"
          @click="open(n)"
        >
          <div class="notif-title">
            <el-tag size="small" :type="notifTag(n).type">
              {{ notifTag(n).label }}
            </el-tag>
            <span class="notif-time">{{ fmtDate(n.created_at) }}</span>
          </div>
          <div class="notif-msg">{{ n.message }}</div>
        </div>
      </el-scrollbar>
    </div>
  </el-popover>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { Bell } from '@element-plus/icons-vue'
import { api } from '../api'
import { useNotificationStore } from '../stores/notification'
import { fmtDate } from '../utils/format'

const router = useRouter()
const notificationStore = useNotificationStore()
const items = ref([])

onMounted(load)

const NOTIF_TAGS = {
  task_assigned: { label: '派发', type: 'warning' },
  task_completed: { label: '完成', type: 'success' },
  task_approved: { label: '确认', type: 'success' },
  task_rejected: { label: '驳回', type: 'danger' },
}

function notifTag(n) {
  return NOTIF_TAGS[n.type] || { label: '消息', type: 'info' }
}

async function load() {
  items.value = await api.notifications.list()
}

function open(n) {
  if (!n.is_read) {
    api.notifications.read(n.id).then(async () => {
      n.is_read = true
      notificationStore.count = Math.max(0, notificationStore.count - 1)
    })
  }
  if (n.task_id) {
    router.push({ path: '/tasks', query: { focus: n.task_id } })
  }
}

async function markAll() {
  await api.notifications.readAll()
  items.value.forEach((n) => (n.is_read = true))
  notificationStore.count = 0
}
</script>

<style scoped>
.notif-panel {
  padding: 4px;
}
.notif-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
  padding-bottom: 8px;
  border-bottom: 1px solid #f0f0f0;
}
.empty {
  text-align: center;
  color: #909399;
  padding: 24px 0;
}
.notif-item {
  padding: 10px 8px;
  border-bottom: 1px solid #f5f5f5;
  cursor: pointer;
  border-radius: 4px;
}
.notif-item:hover {
  background: #f5f7fa;
}
.notif-item.unread {
  background: #ecf5ff;
}
.notif-title {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.notif-time {
  font-size: 12px;
  color: #909399;
}
.notif-msg {
  margin-top: 6px;
  font-size: 13px;
  color: #303133;
  line-height: 1.4;
}
</style>