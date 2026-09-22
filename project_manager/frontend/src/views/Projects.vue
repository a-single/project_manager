<template>
  <div class="page">
    <div class="toolbar">
      <el-input v-model="keyword" placeholder="搜索项目名称" :prefix-icon="Search" clearable style="width: 260px" />
      <el-button v-if="userStore.isManager" type="primary" :icon="Plus" @click="createVisible = true">
        新建项目
      </el-button>
    </div>

    <div class="scroll-area">
    <el-row :gutter="16">
      <el-col v-for="p in filtered" :key="p.id" :span="8" style="margin-bottom: 16px">
        <el-card shadow="hover" class="proj-card shadow-hover" @click="openProject(p)">
          <div class="proj-name">{{ p.name }}</div>
          <div class="proj-desc">{{ p.description || '暂无描述' }}</div>
          <hr />
          <div class="proj-meta">
            <span>负责人：{{ p.manager_name }}</span>
            <span>创建：{{ fmtDate(p.created_at) }}</span>
          </div>
          <el-row class="proj-stats" :gutter="8">
            <el-col :span="8" class="stat">
              <div class="stat-num">{{ p.member_count }}</div>
              <div class="stat-label">成员</div>
            </el-col>
            <el-col :span="8" class="stat">
              <div class="stat-num">{{ p.task_count }}</div>
              <div class="stat-label">任务</div>
            </el-col>
            <el-col :span="8" class="stat">
              <div class="stat-num warn">{{ p.pending_task_count }}</div>
              <div class="stat-label">待处理</div>
            </el-col>
          </el-row>
          <div class="proj-ops">
            <el-button link type="primary" size="small" @click.stop="openProject(p)">查看详情</el-button>
            <el-button
              v-if="canManage(p)"
              link
              type="warning"
              size="small"
              @click.stop="archiveProject(p)"
            >
              关闭
            </el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>
    <el-empty v-if="filtered.length === 0" description="暂无项目" />
    </div>

    <el-dialog v-model="createVisible" title="新建项目" width="460px">
      <el-form label-width="80px">
        <el-form-item label="项目名称" required>
          <el-input v-model="createForm.name" placeholder="请输入项目名称" />
        </el-form-item>
        <el-form-item label="项目描述">
          <el-input v-model="createForm.description" type="textarea" :rows="3" placeholder="可选" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createVisible = false">取消</el-button>
        <el-button type="primary" :loading="creating" @click="createProject">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search } from '@element-plus/icons-vue'
import { api } from '../api'
import { useUserStore } from '../stores/user'
import { fmtDate } from '../utils/format'

const router = useRouter()
const userStore = useUserStore()

const keyword = ref('')
const projects = ref([])
const createVisible = ref(false)
const creating = ref(false)
const createForm = reactive({ name: '', description: '' })

const filtered = computed(() =>
  projects.value.filter((p) => p.name.includes(keyword.value.trim())),
)

function canManage(p) {
  return userStore.isAdmin || p.manager_id === userStore.user?.id
}

async function load() {
  projects.value = await api.projects.list()
}

function openProject(p) {
  router.push(`/projects/${p.id}`)
}

function createProject() {
  if (!createForm.name.trim()) {
    ElMessage.warning('请输入项目名称')
    return
  }
  creating.value = true
  api.projects
    .create({ name: createForm.name.trim(), description: createForm.description })
    .then(() => {
      ElMessage.success('项目已创建')
      createVisible.value = false
      createForm.name = ''
      createForm.description = ''
      load()
    })
    .catch((e) => ElMessage.error(e.message))
    .finally(() => (creating.value = false))
}

function archiveProject(p) {
  ElMessageBox.confirm(
    `确定关闭项目「${p.name}」？关闭后：任务不可派发、所有任务状态锁定、普通成员不可见，仅你可查看。`,
    '关闭项目',
    { type: 'warning', confirmButtonText: '确认关闭' },
  )
    .then(async () => {
      await api.projects.archive(p.id)
      ElMessage.success('项目已关闭归档，可在「归档项目」中查看')
      load()
    })
    .catch(() => {})
}

onMounted(load)
</script>

<style scoped>
.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  flex: none;
}
.scroll-area {
  flex: 1;
  min-height: 0;
  overflow: auto;
  padding-right: 4px;
}
.proj-card {
  cursor: pointer;
  height: 100%;
  position: relative;
  overflow: hidden;
  transition: transform 0.25s ease, box-shadow 0.25s ease;
}
.proj-card::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  right: 0;
  height: 4px;
  background: linear-gradient(90deg, #6ea8fe, #38bdf8, #22d3ee);
}
.proj-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 16px 36px rgba(110, 168, 254, 0.2);
}
.proj-name {
  margin-top: 4px;
  font-size: 16px;
  font-weight: 700;
  color: var(--app-text-main);
}
.proj-meta {
  color: #606266;
  font-size: 13px;
  display: flex;
  justify-content: space-between;
}
.proj-desc {
  color: #909399;
  font-size: 13px;
  margin-top: 6px;
  height: 40px;
  overflow: hidden;
}
.proj-stats {
  text-align: center;
  margin-top: 8px;
}
.stat-num {
  font-size: 20px;
  font-weight: 600;
}
.stat-num.warn {
  color: #e6a23c;
}
.stat-label {
  color: #909399;
  font-size: 12px;
}
.proj-ops {
  margin-top: 8px;
  text-align: right;
}
</style>