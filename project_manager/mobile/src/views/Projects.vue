<template>
  <div class="page">
    <div class="row" style="margin-bottom: 10px">
      <span style="font-weight: 700">我的项目（{{ projects.length }}）</span>
      <span v-if="userStore.isPM">
        <button class="btn btn-primary" style="padding: 6px 14px; font-size: 13px" @click="createOpen = true">＋ 新建</button>
      </span>
    </div>

    <div v-if="loading" class="empty">加载中…</div>
    <div v-else-if="projects.length === 0" class="empty">
      <div class="empty-icon">🗂️</div>暂无项目
    </div>

    <div v-for="p in projects" :key="p.id" class="card proj-card" @click="goDetail(p.id)">
      <div class="proj-head">
        <div class="proj-mark">{{ p.name.slice(0, 1) }}</div>
        <div style="min-width: 0; flex: 1">
          <div class="proj-name ellipsis">{{ p.name }}</div>
          <div class="muted ellipsis">{{ p.description || '暂无描述' }}</div>
        </div>
        <button
          v-if="canManage(p)"
          class="btn btn-danger-outline"
          style="padding: 6px 12px; font-size: 12px; flex-shrink: 0"
          @click.stop="archiveProject(p)"
        >关闭</button>
      </div>
      <div class="row muted" style="margin-top: 10px">
        <span>负责人 {{ p.manager_name }}</span>
        <span v-if="p.task_count != null">任务 {{ p.task_count }}</span>
      </div>
      <div class="row muted" style="margin-top: 4px; font-size: 12px">
        <span>成员 {{ p.member_count ?? p.members?.length ?? 0 }} 人</span>
        <span>创建 {{ fmtDate(p.created_at) }}</span>
      </div>
    </div>

    <div v-if="userStore.isPM && projects.length === 0" class="card" style="padding: 16px">
      <div class="muted" style="margin-bottom: 10px">建立第一个项目，将成员纳入项目后即可派发任务</div>
      <button class="btn btn-outline btn-block" @click="createOpen = true">新建项目</button>
    </div>

    <!-- 新建项目 -->
    <div v-if="createOpen" class="sheet-mask" @click="createOpen = false"></div>
    <div class="sheet" v-if="createOpen">
      <div class="sheet-title">
        <span>新建项目</span>
        <button class="btn btn-ghost" style="padding: 4px 10px; font-size: 12px" @click="createOpen = false">关闭</button>
      </div>
      <div class="field">
        <label>项目名称（必填）</label>
        <input v-model.trim="form.name" class="input" placeholder="请输入项目名称" />
      </div>
      <div class="field">
        <label>项目描述</label>
        <textarea v-model.trim="form.description" class="textarea" placeholder="项目简介（选填）"></textarea>
      </div>
      <button class="btn btn-primary btn-block" :disabled="creating" @click="create">
        {{ creating ? '创建中…' : '创建项目' }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../stores/user'
import { api } from '../api'
import { fmtDate } from '../utils/format'

const router = useRouter()
const userStore = useUserStore()
const projects = ref([])
const loading = ref(false)
const createOpen = ref(false)
const creating = ref(false)
const form = reactive({ name: '', description: '' })

function goDetail(id) {
  router.push(`/projects/${id}`)
}

function canManage(p) {
  return userStore.isAdmin || p.manager_id === userStore.user?.id
}

function archiveProject(p) {
  if (!confirm(`确定关闭项目「${p.name}」？关闭后：任务不可派发、任务状态锁定、普通成员不可见。`)) return
  api.projects
    .archive(p.id)
    .then(() => {
      alert('项目已关闭归档，可在底部「归档」中查看')
      load()
    })
    .catch((e) => alert(e.message))
}

async function load() {
  loading.value = true
  try {
    projects.value = await api.projects.list()
  } catch (e) {
    alert(e.message)
  } finally {
    loading.value = false
  }
}

async function create() {
  if (!form.name) {
    alert('请输入项目名称')
    return
  }
  creating.value = true
  try {
    await api.projects.create(form.name, form.description)
    createOpen.value = false
    form.name = ''
    form.description = ''
    alert('项目创建成功')
    load()
  } catch (e) {
    alert(e.message)
  } finally {
    creating.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.proj-card {
  cursor: pointer;
  overflow: hidden;
  position: relative;
}
.proj-card::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, #6ea8fe, #38bdf8, #22d3ee);
}
.proj-head {
  display: flex;
  gap: 12px;
  align-items: center;
}
.proj-mark {
  width: 42px;
  height: 42px;
  border-radius: 12px;
  background: linear-gradient(135deg, #6ea8fe, #38bdf8);
  color: #fff;
  font-size: 18px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.proj-name {
  font-size: 15px;
  font-weight: 700;
}
</style>