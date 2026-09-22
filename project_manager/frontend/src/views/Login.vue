<template>
  <div class="login-page">
    <el-card class="login-card">
      <div class="login-title">运维项目管理工作平台</div>
      <el-form :model="form" :rules="rules" ref="formRef" @keyup.enter="submit">
        <el-form-item prop="username">
          <el-input v-model="form.username" placeholder="用户名" size="large" :prefix-icon="User" />
        </el-form-item>
        <el-form-item prop="password">
          <el-input
            v-model="form.password"
            type="password"
            show-password
            placeholder="密码"
            size="large"
            :prefix-icon="Lock"
          />
        </el-form-item>
        <el-button type="primary" size="large" class="login-btn" :loading="loading" @click="submit">
          登 录
        </el-button>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock } from '@element-plus/icons-vue'
import { api } from '../api'
import { useUserStore } from '../stores/user'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const formRef = ref()
const loading = ref(false)
const form = reactive({ username: '', password: '' })
const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

async function submit() {
  await formRef.value.validate()
  loading.value = true
  try {
    const res = await api.login({ username: form.username, password: form.password })
    userStore.setAuth(res.token, res.user)
    ElMessage.success('登录成功')
    const redirect = route.query.redirect
    router.replace(redirect || '/')
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: radial-gradient(900px 420px at 15% 12%, rgba(147, 197, 253, 0.45), transparent 60%),
    radial-gradient(700px 380px at 85% 85%, rgba(125, 211, 252, 0.35), transparent 60%),
    linear-gradient(150deg, #eef2ff 0%, #e3f1fb 52%, #eef7ff 100%);
  overflow: hidden;
  position: relative;
}
.login-page::before,
.login-page::after {
  content: '';
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.5;
}
.login-page::before {
  width: 320px;
  height: 320px;
  background: #bcd6fd;
  top: -80px;
  left: -60px;
}
.login-page::after {
  width: 280px;
  height: 280px;
  background: #a5e1f7;
  bottom: -90px;
  right: -40px;
}
.login-card {
  width: 400px;
  border-radius: 18px;
  border: 1px solid rgba(148, 163, 184, 0.22);
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(16px);
  box-shadow: 0 24px 60px rgba(79, 110, 247, 0.16);
  position: relative;
  z-index: 1;
  padding: 8px 4px;
}
.login-title {
  font-size: 22px;
  font-weight: 800;
  text-align: center;
  margin-bottom: 26px;
  background: linear-gradient(90deg, #6ea8fe, #39c1d4);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  letter-spacing: 1px;
}
.login-btn {
  width: 100%;
  border-radius: 10px;
  font-size: 15px;
  letter-spacing: 4px;
}
.login-card :deep(.el-input__wrapper) {
  border-radius: 10px;
}
</style>