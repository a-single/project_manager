<template>
  <el-container class="layout">
    <el-aside width="220px" class="aside">
      <div class="logo">
        <el-icon class="logo-icon"><Odometer /></el-icon>
        <span class="logo-text">运维项目管理工作平台</span>
      </div>
      <el-menu
        :default-active="activeMenu"
        router
      >
        <el-menu-item index="/">
          <el-icon><HomeFilled /></el-icon><span>工作台</span>
        </el-menu-item>
        <el-menu-item index="/tasks">
          <el-icon><List /></el-icon><span>我的任务</span>
        </el-menu-item>
        <el-menu-item index="/projects">
          <el-icon><FolderOpened /></el-icon><span>项目管理</span>
        </el-menu-item>
        <!-- 项目经理/管理员：日报导出菜单替换为归档项目；普通员工保留日报导出 -->
        <el-menu-item v-if="userStore.isManager" index="/archived">
          <el-icon><Box /></el-icon><span>归档项目</span>
        </el-menu-item>
        <el-menu-item v-else index="/report">
          <el-icon><Document /></el-icon><span>日报导出</span>
        </el-menu-item>
        <el-menu-item v-if="userStore.isAdmin" index="/users">
          <el-icon><User /></el-icon><span>用户管理</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header class="header">
        <div class="header-title">{{ route.meta.title || '' }}</div>
        <div class="header-right">
          <NotificationBell />
          <el-dropdown @command="handleCommand">
            <span class="user-entry">
              <el-icon><UserFilled /></el-icon>
              {{ displayName }}
              <el-tag size="small" :type="tagType" class="role-tag">{{ userStore.roleLabel }}</el-tag>
              <el-icon><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile">个人设置</el-dropdown-item>
                <el-dropdown-item command="logout" divided>退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>

      <el-main class="main">
        <router-view />
      </el-main>
    </el-container>

    <el-dialog v-model="profileVisible" title="个人设置" width="420px">
      <el-form label-width="80px">
        <el-form-item label="用户名">
          <el-input v-model="profileForm.username" />
        </el-form-item>
        <el-form-item label="姓名" required>
          <el-input v-model="profileForm.full_name" placeholder="请输入姓名" />
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input v-model="profileForm.email" placeholder="选填" />
        </el-form-item>
        <el-form-item label="电话">
          <el-input v-model="profileForm.phone" placeholder="选填" />
        </el-form-item>
        <el-form-item label="新密码">
          <el-input v-model="profileForm.password" type="password" show-password placeholder="留空则不修改" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="profileVisible = false">取消</el-button>
        <el-button type="primary" @click="saveProfile">保存</el-button>
      </template>
    </el-dialog>
  </el-container>
</template>

<script setup>
import { computed, onMounted, onUnmounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useUserStore } from '../stores/user'
import { useNotificationStore } from '../stores/notification'
import NotificationBell from './NotificationBell.vue'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const notificationStore = useNotificationStore()

const activeMenu = computed(() => {
  if (route.path.startsWith('/projects') || route.path.startsWith('/stats')) return '/projects'
  if (route.path === '/archived') return '/archived'
  return route.path
})

const tagType = computed(() => {
  const map = { admin: 'danger', pm: 'warning', dev: 'primary', tester: 'success', ops: 'info' }
  return map[userStore.user?.role] || 'info'
})

const profileVisible = ref(false)
const profileForm = reactive({ username: '', full_name: '', email: '', phone: '', password: '' })

const displayName = computed(
  () => userStore.user?.full_name || userStore.user?.username || '',
)

function handleCommand(cmd) {
  if (cmd === 'logout') {
    userStore.logout()
    router.replace('/login')
  } else if (cmd === 'profile') {
    const u = userStore.user || {}
    profileForm.username = u.username || ''
    profileForm.full_name = u.full_name || ''
    profileForm.email = u.email || ''
    profileForm.phone = u.phone || ''
    profileForm.password = ''
    profileVisible.value = true
  }
}

async function saveProfile() {
  if (!profileForm.full_name.trim()) {
    ElMessage.warning('姓名不能为空')
    return
  }
  try {
    await userStore.updateMe({
      username: profileForm.username.trim(),
      full_name: profileForm.full_name.trim(),
      email: profileForm.email.trim() || undefined,
      phone: profileForm.phone.trim() || undefined,
      password: profileForm.password || undefined,
    })
    ElMessage.success('已保存')
    profileVisible.value = false
  } catch (e) {
    ElMessage.error(e.message)
  }
}

onMounted(() => notificationStore.startPolling(8000))
onUnmounted(() => notificationStore.stopPolling())
</script>

<style scoped>
.layout {
  height: 100vh;
}
/* 侧边栏：浅色渐变 + 细点纹理 */
.aside {
  background: linear-gradient(180deg, #f7f9ff 0%, #eef2ff 55%, #e8edfb 100%);
  background-image: radial-gradient(rgba(79, 110, 247, 0.06) 1px, transparent 1px),
    linear-gradient(180deg, #f7f9ff 0%, #eef2ff 55%, #e8edfb 100%);
  background-size: 18px 18px, auto;
  border-right: 1px solid rgba(15, 23, 42, 0.06);
}
.logo {
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  border-bottom: 1px solid rgba(15, 23, 42, 0.08);
}
.logo-icon {
  font-size: 22px;
  color: #3b82f6;
  background: rgba(79, 110, 247, 0.12);
  padding: 6px;
  border-radius: 8px;
}
.logo-text {
  color: #1e3a8a;
  font-size: 15px;
  font-weight: 700;
  letter-spacing: 0.5px;
  background: linear-gradient(90deg, #2b5be8, #0ea5e9);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
}
.aside :deep(.el-menu) {
  border-right: none;
  background: transparent !important;
  padding: 8px;
}
.aside :deep(.el-menu-item) {
  border-radius: 10px;
  margin-bottom: 4px;
  height: 46px;
  color: #51608a;
}
.aside :deep(.el-menu-item:hover) {
  background: rgba(79, 110, 247, 0.08);
  color: #2b5be8;
}
.aside :deep(.el-menu-item.is-active) {
  background: linear-gradient(90deg, rgba(79, 110, 247, 0.16), rgba(125, 211, 252, 0.12));
  color: #2b5be8 !important;
  box-shadow: inset 3px 0 0 #4f6ef7;
}
/* 顶栏：毛玻璃 */
.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid rgba(15, 23, 42, 0.08);
  background: rgba(255, 255, 255, 0.72);
  backdrop-filter: blur(14px);
  -webkit-backdrop-filter: blur(14px);
  position: sticky;
  top: 0;
  z-index: 10;
}
.header-title {
  font-size: 15px;
  font-weight: 700;
  color: var(--app-text-main);
}
.header-right {
  display: flex;
  align-items: center;
  gap: 20px;
}
.user-entry {
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  color: var(--app-text-main);
  padding: 6px 10px;
  border-radius: 8px;
  transition: background 0.2s;
}
.user-entry:hover {
  background: rgba(110, 168, 254, 0.08);
}
.role-tag {
  margin-left: 2px;
}
/* 主内容区：浅色渐变 + 网格纹理。
   根容器不产生滚动条，所有滚动仅在页面内部列表区进行。 */
.main {
  background-color: #f3f5fb;
  background-image: linear-gradient(rgba(110, 168, 254, 0.035) 1px, transparent 1px),
    linear-gradient(90deg, rgba(110, 168, 254, 0.035) 1px, transparent 1px);
  background-size: 26px 26px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  padding: 20px;
}
/* 页面根：纵向弹性布局，高度占满 main，放不下时由内部 .scroll-area 滚动 */
.main :deep(.page) {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}
/* 通用卡片型页面：卡片撑满，列表在 body 内滚动 */
.main :deep(.page-card) {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}
.main :deep(.page-card > .el-card__header) {
  flex: none;
}
.main :deep(.page-card > .el-card__body) {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
/* 通用列表滚动区：仅在内部滚动 */
.main :deep(.scroll-area) {
  flex: 1;
  min-height: 0;
  overflow: auto;
  padding-right: 4px;
}
</style>