<template>
  <div v-if="!route.meta.hideLayout" class="app-frame">
    <header class="app-header">
      <div class="header-left" @click="handleHeaderLeft">
        <svg v-if="canBack" style="width: 22px; height: 22px" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M15 18l-6-6 6-6" /></svg>
        <button v-else class="icon-btn" title="服务器设置" @click.stop="openServerSettings">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="3"></circle>
            <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 1 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 1 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 1 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 1 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"></path>
          </svg>
        </button>
      </div>
      <span class="title">{{ pageTitle }}</span>
      <div class="header-right">
        <div class="bell-wrap" @click="toggleNotif">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="position: relative">
            <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path>
            <path d="M13.73 21a2 2 0 0 1-3.46 0"></path>
          </svg>
          <span v-if="notifStore.unread > 0" class="badge">{{ notifStore.unread > 99 ? '99+' : notifStore.unread }}</span>
        </div>
        <div class="me-wrap" @click.stop="userMenuOpen = true">
          <span class="me-avatar">{{ meInitial }}</span>
        </div>
      </div>
    </header>

    <transition :key="'notif'" name="fade">
      <div v-if="notifOpen" class="notif-panel">
        <div class="row" style="padding: 12px 14px; border-bottom: 1px solid var(--line)">
          <span style="font-weight: 700">消息通知</span>
          <button class="btn btn-ghost" style="padding: 4px 10px; font-size: 12px" @click="markAll">全部已读</button>
        </div>
        <div v-if="notifStore.items.length === 0" class="empty">
          <div class="empty-icon">🔔</div>暂无消息
        </div>
        <div
          v-for="n in notifStore.items"
          :key="n.id"
          class="notif-item"
          @click="goTask(n)"
        >
          <span :class="['notif-dot', n.is_read ? 'read' : '']"></span>
          <div style="min-width: 0">
            <div class="row">
              <span class="tag" :class="notifStore.typeLabel(n.type).cls">{{ notifStore.typeLabel(n.type).label }}</span>
              <span class="muted">{{ fmtDate(n.created_at) }}</span>
            </div>
            <div style="margin-top: 6px; font-size: 14px; line-height: 1.5">{{ n.message }}</div>
          </div>
        </div>
      </div>
    </transition>
    <div v-if="notifOpen" class="sheet-mask" style="z-index: 940" @click="notifOpen = false"></div>

    <!-- 用户菜单 -->
    <div v-if="userMenuOpen" class="sheet-mask" style="z-index: 960" @click="userMenuOpen = false"></div>
    <div class="sheet user-sheet" v-if="userMenuOpen" style="z-index: 961">
      <div class="sheet-title">
        <span>我的账户</span>
        <button class="btn btn-ghost" style="padding: 4px 10px; font-size: 12px" @click="userMenuOpen = false">关闭</button>
      </div>
      <div class="me-card">
        <span class="me-avatar lg">{{ meInitial }}</span>
        <div>
          <div style="font-weight: 700">{{ userStore.user?.full_name || userStore.user?.username }}</div>
          <div class="muted" style="margin-top: 2px">@{{ userStore.user?.username }} · {{ userStore.roleLabel }}</div>
        </div>
      </div>
      <button class="btn btn-danger btn-block" style="margin-top: 18px" @click="logout">退出登录</button>
    </div>

    <main class="page-ghost">
      <router-view />
    </main>

    <nav class="tabbar" v-if="route.meta.hideTabber !== true">
      <div v-for="t in tabs" :key="t.path" class="tab" :class="{ active: t.path === activePath }" @click="go(t.path)">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path v-if="t.icon === 'home'" d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path>
          <path v-else-if="t.icon === 'tasks'" d="M9 11l3 3L22 4"></path>
          <path v-else-if="t.icon === 'tasks'" d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"></path>
          <path v-else-if="t.icon === 'projects'" d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path>
          <path v-else-if="t.icon === 'report'" d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
          <path v-else-if="t.icon === 'report'" d="M14 2v6h6"></path>
        </svg>
        <span>{{ t.label }}</span>
      </div>
    </nav>
  </div>
  <router-view v-else />
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from './stores/user'
import { useNotificationStore } from './stores/notification'
import { api } from './api'
import { fmtDate } from './utils/format'
import { primeAudio } from './utils/sound'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const notifStore = useNotificationStore()
const notifOpen = ref(false)
const userMenuOpen = ref(false)

const TITLE_MAP = {
  home: '工作台',
  tasks: '我的任务',
  projects: '项目管理',
  projectDetail: '项目详情',
  stats: '任务统计',
  archived: '归档项目',
  report: '日报导出',
  login: '登录',
}

const pageTitle = computed(() => TITLE_MAP[route.name] || '项目管理')

const meInitial = computed(() =>
  (userStore.user?.full_name || userStore.user?.username || '?').slice(0, 1),
)

// 项目经理/管理员：底部 tab“日报”替换为“归档项目”；普通员工保留“日报导出”
const tabs = computed(() => {
  const base = [
    { path: '/', label: '首页', icon: 'home' },
    { path: '/tasks', label: '任务', icon: 'tasks' },
    { path: '/projects', label: '项目', icon: 'projects' },
  ]
  if (userStore.isPM) {
    base.push({ path: '/archived', label: '归档', icon: 'report' })
  } else {
    base.push({ path: '/report', label: '日报', icon: 'report' })
  }
  return base
})

const activePath = computed(() => {
  if (route.path.startsWith('/projects')) return '/projects'
  return route.path
})

const canBack = computed(() => route.name === 'projectDetail')

function handleHeaderLeft() {
  if (canBack.value) router.back()
}

/** 左上角“服务器设置”按钮：安卓壳通过 JSBridge 弹出系统设置对话框 */
function openServerSettings() {
  const bridge = window.Android
  if (bridge && typeof bridge.showServerSettings === 'function') {
    bridge.showServerSettings()
  } else {
    alert('该功能需在安卓 App 内使用：点击左上角齿轮即可修改服务器地址')
  }
}

function go(path) {
  if (route.path === path) return
  router.push(path)
}

async function toggleNotif() {
  notifOpen.value = !notifOpen.value
  if (notifOpen.value) {
    await notifStore.load({ unreadOnly: true })
  }
}

async function markAll() {
  await notifStore.markAllRead()
}

function goTask(n) {
  notifOpen.value = false
  if (n.task_id) {
    router.push({ path: '/tasks', query: { focus: n.task_id } })
  } else {
    router.push('/tasks')
  }
}

function logout() {
  userMenuOpen.value = false
  if (!confirm('确定退出登录？')) return
  userStore.logout()
  notifStore.stopPolling()
  notifStore.unread = 0
  notifStore.items = []
  router.replace('/login')
}

onMounted(async () => {
  await userStore.refreshMe()
  try {
    const projects = await api.projects.list()
    // 预热无副作用；仅用于验证连通
  } catch {
    /* 忽略 */
  }
  notifStore.startPolling()
  // 移动端须在用户手势后解锁 AudioContext，否则轮询提醒无声音
  const unlock = () => primeAudio()
  window.addEventListener('touchstart', unlock, { once: true, passive: true })
  window.addEventListener('pointerdown', unlock, { once: true })
})

watch(
  () => route.fullPath,
  () => {
    notifOpen.value = false
  },
)

onBeforeUnmount(() => notifStore.stopPolling())
</script>

<style scoped>
.app-frame {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}
.header-left {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
}
.icon-btn {
  border: none;
  background: transparent;
  color: var(--text);
  padding: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}
.bell-wrap {
  position: relative;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text);
}
.header-right {
  display: flex;
  align-items: center;
  gap: 14px;
}
.me-wrap {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}
.me-avatar {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  background: var(--primary-grad);
  color: #fff;
  font-size: 13px;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.me-avatar.lg {
  width: 46px;
  height: 46px;
  font-size: 18px;
}
.me-card {
  display: flex;
  align-items: center;
  gap: 12px;
  background: #f6f8ff;
  border-radius: 12px;
  padding: 12px;
}
.badge {
  position: absolute;
  top: 0;
  right: -4px;
  min-width: 16px;
  height: 16px;
  padding: 0 4px;
  border-radius: 8px;
  background: var(--danger);
  color: #fff;
  font-size: 10px;
  line-height: 16px;
  text-align: center;
}
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>