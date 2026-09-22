<template>
  <div class="page">
    <div class="card filter-card" style="padding: 12px">
      <input
        v-model="keyword"
        class="input"
        type="search"
        placeholder="按项目名称筛选归档项目"
        @input="load"
      />
      <button class="btn btn-ghost" style="margin-left: 8px; flex-shrink: 0" @click="load">刷新</button>
    </div>

    <div v-if="loading" class="empty">加载中…</div>
    <div v-else-if="projects.length === 0" class="card empty" style="padding: 30px 0">
      <div class="empty-icon">🗂️</div>暂无归档项目
    </div>

    <div v-for="p in projects" :key="p.id" class="card proj-card">
      <div class="row" @click="openProject(p)">
        <div class="proj-mark">{{ p.name.slice(0, 1) }}</div>
        <div style="min-width: 0; flex: 1">
          <div class="proj-name ellipsis">
            {{ p.name }}
            <span class="tag tag-archived">已归档</span>
          </div>
          <div class="muted ellipsis" style="margin-top: 4px">{{ p.description || '暂无描述' }}</div>
        </div>
      </div>
      <div class="row muted" style="margin-top: 10px; font-size: 12px">
        <span>负责人 {{ p.manager_name }}</span>
        <span>{{ p.member_count }} 成员 · {{ p.task_count }} 任务</span>
      </div>
      <div class="row" style="margin-top: 10px">
        <button class="btn btn-ghost" style="padding: 6px 12px; font-size: 12px" @click.stop="openProject(p)">查看详情</button>
        <button class="btn btn-danger-outline" style="padding: 6px 12px; font-size: 12px" @click.stop="removeProject(p)">永久删除</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api'
import { toast } from '../utils/toast'

const router = useRouter()
const keyword = ref('')
const projects = ref([])
const loading = ref(false)

async function load() {
  loading.value = true
  try {
    projects.value = await api.projects.archived({
      name: keyword.value.trim() || undefined,
    })
  } catch (e) {
    alert(e.message)
  } finally {
    loading.value = false
  }
}

function openProject(p) {
  router.push(`/projects/${p.id}`)
}

function removeProject(p) {
  if (!confirm(`确定永久删除项目「${p.name}」？其下所有任务、成员、统计记录将被一并删除，且不可恢复。`)) return
  api.projects
    .remove(p.id)
    .then(() => {
      toast('项目已永久删除')
      load()
    })
    .catch((e) => alert(e.message))
}

onMounted(load)
</script>

<style scoped>
.filter-card {
  display: flex;
  align-items: center;
}
.proj-card {
  cursor: pointer;
  position: relative;
  overflow: hidden;
}
.proj-card::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, #9ca3af, #d1d5db);
}
.proj-mark {
  width: 42px;
  height: 42px;
  border-radius: 12px;
  background: linear-gradient(135deg, #9ca3af, #6b7280);
  color: #fff;
  font-size: 18px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.proj-name {
  font-size: 16px;
  font-weight: 700;
}
.tag-archived {
  background: rgba(156, 163, 175, 0.15);
  color: #6b7280;
  margin-left: 6px;
}
</style>