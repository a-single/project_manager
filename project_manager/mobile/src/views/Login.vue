<template>
  <div class="login-page">
    <div class="login-glow g1"></div>
    <div class="login-glow g2"></div>
    <button class="server-btn" title="服务器设置" @click="openServerSettings">
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="12" cy="12" r="3"></circle>
        <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 1 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 1 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 1 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 1 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"></path>
      </svg>
    </button>
    <div class="login-card">
      <div class="login-logo">
        <div class="logo-mark">
          <svg viewBox="0 0 24 24" width="30" height="30" style="color: #fff" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round">
            <path d="M4 20V10"></path>
            <path d="M10 20V4"></path>
            <path d="M16 20v-8"></path>
            <path d="M22 20H2"></path>
          </svg>
        </div>
        <h1>运维项目管理工作平台</h1>
        <p class="muted">工作任务的派发、反馈与统计管理</p>
      </div>

      <form @submit.prevent="submit">
        <div class="field">
          <input v-model.trim="username" class="input" placeholder="用户名" autocomplete="username" />
        </div>
        <div class="field">
          <input v-model.trim="password" class="input" type="password" placeholder="密码" autocomplete="current-password" />
        </div>
        <button class="btn btn-primary btn-block" :disabled="loading" style="margin-top: 8px">
          {{ loading ? '登录中…' : '登 录' }}
        </button>
      </form>
      <p v-if="error" class="login-error">{{ error }}</p>
      <p class="login-tip">提示：左上角齿轮可设置服务器地址</p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '../stores/user'
import { toast } from '../utils/toast'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const username = ref('')
const password = ref('')
const loading = ref(false)
const error = ref('')

/** 左上角“服务器设置”按钮：安卓壳通过 JSBridge 弹出系统设置对话框 */
function openServerSettings() {
  const bridge = window.Android
  if (bridge && typeof bridge.showServerSettings === 'function') {
    bridge.showServerSettings()
  } else {
    toast('该功能需在安卓 App 内使用')
  }
}

async function submit() {
  if (!username.value || !password.value) {
    error.value = '请输入用户名和密码'
    return
  }
  loading.value = true
  error.value = ''
  try {
    await userStore.login(username.value, password.value)
    const redirect = (route.query.redirect || '/').toString()
    router.replace(redirect.startsWith('/') ? redirect : '/')
  } catch (e) {
    error.value = e.message || '登录失败'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
  background: linear-gradient(160deg, #eef2ff, #e3f1fb 55%, #eef7ff);
  padding: 20px;
}
.server-btn {
  position: absolute;
  top: calc(14px + env(safe-area-inset-top));
  left: 14px;
  width: 36px;
  height: 36px;
  border: none;
  background: rgba(255, 255, 255, 0.9);
  border-radius: 10px;
  color: var(--text);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 12px rgba(79, 110, 247, 0.18);
  cursor: pointer;
  z-index: 2;
}
.login-glow {
  position: absolute;
  border-radius: 50%;
  filter: blur(70px);
}
.g1 {
  width: 260px;
  height: 260px;
  background: rgba(147, 197, 253, 0.55);
  top: -60px;
  left: -50px;
}
.g2 {
  width: 220px;
  height: 220px;
  background: rgba(125, 211, 252, 0.45);
  bottom: -50px;
  right: -30px;
}
.login-card {
  width: 100%;
  max-width: 360px;
  background: rgba(255, 255, 255, 0.95);
  border-radius: 20px;
  padding: 30px 24px 20px;
  border: 1px solid rgba(148, 163, 184, 0.2);
  box-shadow: 0 20px 50px rgba(79, 110, 247, 0.15);
  position: relative;
  z-index: 1;
}
.login-logo {
  text-align: center;
  margin-bottom: 24px;
}
.logo-mark {
  width: 56px;
  height: 56px;
  margin: 0 auto 12px;
  border-radius: 16px;
  background: linear-gradient(135deg, #6ea8fe, #38bdf8);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 8px 20px rgba(110, 168, 254, 0.4);
}
.login-logo h1 {
  font-size: 18px;
  margin-bottom: 6px;
  background: linear-gradient(90deg, #6ea8fe, #39c1d4);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
}
.login-error {
  color: var(--danger);
  font-size: 13px;
  margin-top: 10px;
  text-align: center;
}
.login-tip {
  color: #94a3b8;
  font-size: 12px;
  text-align: center;
  margin-top: 16px;
}
</style>