<template>
  <div class="page">
    <div class="toolbar">
      <el-input
        v-model="keyword"
        placeholder="按项目名称筛选归档项目"
        :prefix-icon="Search"
        clearable
        style="width: 300px"
        @input="load"
      />
      <el-button :icon="Refresh" circle @click="load" />
    </div>

    <div class="scroll-area">
    <el-row :gutter="16">
      <el-col v-for="p in projects" :key="p.id" :span="8" style="margin-bottom: 16px">
        <el-card shadow="hover" class="proj-card" @click="openProject(p)">
          <div class="proj-name">
            {{ p.name }}
            <el-tag size="small" type="info" style="margin-left: 6px">已归档</el-tag>
          </div>
          <div class="proj-desc">{{ p.description || '暂无描述' }}</div>
          <hr />
          <div class="proj-meta">负责人：{{ p.manager_name }}</div>
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
            <el-button link type="danger" size="small" @click.stop="removeProject(p)">永久删除</el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>
    <el-empty v-if="!loading && projects.length === 0" description="暂无归档项目" />
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Refresh, Search } from '@element-plus/icons-vue'
import { api } from '../api'

const router = useRouter()
const keyword = ref('')
const projects = ref([])
const loading = ref(false)

async function load() {
  loading.value = true
  try {
    projects.value = await api.projects.archived({ name: keyword.value.trim() || undefined })
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    loading.value = false
  }
}

function openProject(p) {
  router.push(`/projects/${p.id}`)
}

function removeProject(p) {
  ElMessageBox.confirm(
    `确定永久删除项目「${p.name}」？其下所有任务、成员、统计记录将被一并删除，且不可恢复。`,
    '永久删除',
    { type: 'warning', confirmButtonText: '确认删除' },
  )
    .then(async () => {
      await api.projects.remove(p.id)
      ElMessage.success('项目已永久删除')
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
.proj-desc {
  color: #909399;
  font-size: 13px;
  margin-top: 6px;
  height: 40px;
  overflow: hidden;
}
.proj-meta {
  color: #606266;
  font-size: 13px;
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