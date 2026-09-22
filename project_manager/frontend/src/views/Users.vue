<template>
  <el-card shadow="never" class="page page-card">
    <template #header>
      <div class="card-head">
        <span>用户管理</span>
        <el-button type="primary" :icon="Plus" @click="openCreate">新建用户</el-button>
      </div>
    </template>

    <div class="scroll-area">
    <el-table :data="users" v-loading="loading">
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="full_name" label="姓名" width="120" />
      <el-table-column prop="username" label="用户名" width="150" />
      <el-table-column label="角色" width="110">
        <template #default="{ row }">
          <el-tag :type="roleTag(row.role)">{{ row.role_label }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="email" label="邮箱" min-width="160" show-overflow-tooltip />
      <el-table-column prop="phone" label="电话" width="130" show-overflow-tooltip />
      <el-table-column label="创建时间" width="165">
        <template #default="{ row }">{{ fmtDate(row.created_at) }}</template>
      </el-table-column>
      <el-table-column label="操作" min-width="200">
        <template #default="{ row }">
          <template v-if="row.role !== 'admin'">
            <el-button link type="primary" size="small" @click="openEdit(row)">调整角色/信息</el-button>
            <el-button link type="danger" size="small" @click="removeUser(row)">删除</el-button>
          </template>
          <span v-else style="color: #909399">系统内置</span>
        </template>
      </el-table-column>
    </el-table>
    </div>

    <el-dialog v-model="createVisible" title="新建用户" width="460px">
      <el-form label-width="80px">
        <el-form-item label="姓名" required>
          <el-input v-model="createForm.full_name" maxlength="50" placeholder="必填" />
        </el-form-item>
        <el-form-item label="用户名" required>
          <el-input v-model="createForm.username" maxlength="50" />
        </el-form-item>
        <el-form-item label="初始密码" required>
          <el-input v-model="createForm.password" show-password maxlength="64" />
        </el-form-item>
        <el-form-item label="角色" required>
          <el-select v-model="createForm.role" style="width: 100%">
            <el-option v-for="r in businessRoles" :key="r.value" :label="r.label" :value="r.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input v-model="createForm.email" maxlength="100" placeholder="选填" />
        </el-form-item>
        <el-form-item label="电话">
          <el-input v-model="createForm.phone" maxlength="30" placeholder="选填" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="createUser">创建</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="editVisible" title="调整角色 / 基本信息" width="460px">
      <el-form label-width="80px">
        <el-form-item label="姓名" required>
          <el-input v-model="editForm.full_name" maxlength="50" />
        </el-form-item>
        <el-form-item label="用户名">
          <span>{{ editForm.username }}</span>
        </el-form-item>
        <el-form-item label="角色">
          <el-select v-model="editForm.role" style="width: 100%">
            <el-option v-for="r in businessRoles" :key="r.value" :label="r.label" :value="r.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input v-model="editForm.email" maxlength="100" />
        </el-form-item>
        <el-form-item label="电话">
          <el-input v-model="editForm.phone" maxlength="30" />
        </el-form-item>
        <el-form-item label="新密码">
          <el-input v-model="editForm.password" show-password placeholder="留空则不修改" maxlength="64" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="saveEdit">保存</el-button>
      </template>
    </el-dialog>
  </el-card>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { api } from '../api'
import { fmtDate } from '../utils/format'

const users = ref([])
const loading = ref(false)
const createVisible = ref(false)
const editVisible = ref(false)
const submitting = ref(false)

const businessRoles = [
  { value: 'pm', label: '项目经理' },
  { value: 'dev', label: '开发人员' },
  { value: 'tester', label: '测试人员' },
  { value: 'ops', label: '运维人员' },
]

const createForm = reactive({ username: '', password: '', full_name: '', email: '', phone: '', role: 'dev' })
const editForm = reactive({ id: null, username: '', full_name: '', role: 'dev', email: '', phone: '', password: '' })

function roleTag(role) {
  const map = { admin: 'danger', pm: 'warning', dev: 'primary', tester: 'success', ops: 'info' }
  return map[role] || 'info'
}

async function load() {
  loading.value = true
  try {
    users.value = await api.users.list()
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    loading.value = false
  }
}

function openCreate() {
  createForm.username = ''
  createForm.password = ''
  createForm.full_name = ''
  createForm.email = ''
  createForm.phone = ''
  createForm.role = 'dev'
  createVisible.value = true
}

function createUser() {
  if (!createForm.full_name.trim()) {
    ElMessage.warning('姓名不能为空')
    return
  }
  if (!createForm.username.trim() || !createForm.password) {
    ElMessage.warning('用户名和初始密码不能为空')
    return
  }
  submitting.value = true
  api.users
    .create({
      username: createForm.username.trim(),
      password: createForm.password,
      full_name: createForm.full_name.trim(),
      email: createForm.email.trim() || undefined,
      phone: createForm.phone.trim() || undefined,
      role: createForm.role,
    })
    .then(() => {
      ElMessage.success('用户已创建')
      createVisible.value = false
      load()
    })
    .catch((e) => ElMessage.error(e.message))
    .finally(() => (submitting.value = false))
}

function openEdit(row) {
  editForm.id = row.id
  editForm.username = row.username
  editForm.full_name = row.full_name || ''
  editForm.role = row.role
  editForm.email = row.email || ''
  editForm.phone = row.phone || ''
  editForm.password = ''
  editVisible.value = true
}

function saveEdit() {
  if (!editForm.full_name.trim()) {
    ElMessage.warning('姓名不能为空')
    return
  }
  submitting.value = true
  api.users
    .update(editForm.id, {
      role: editForm.role,
      full_name: editForm.full_name.trim(),
      email: editForm.email.trim() || undefined,
      phone: editForm.phone.trim() || undefined,
      ...(editForm.password ? { password: editForm.password } : {}),
    })
    .then(() => {
      ElMessage.success('已保存')
      editVisible.value = false
      load()
    })
    .catch((e) => ElMessage.error(e.message))
    .finally(() => (submitting.value = false))
}

function removeUser(row) {
  ElMessageBox.confirm(`确定删除用户「${row.username}」？`, '删除确认', { type: 'warning' })
    .then(async () => {
      await api.users.remove(row.id)
      ElMessage.success('已删除')
      load()
    })
    .catch(() => {})
}

onMounted(load)
</script>

<style scoped>
.card-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>