<template>
  <div class="page">
    <div class="row" style="margin-bottom: 10px">
      <div class="chips">
        <span
          v-for="c in chips"
          :key="c.value"
          class="chip"
          :class="{ active: filter === c.value }"
          @click="setFilter(c.value)"
        >
          {{ c.label }}
          <em v-if="countBy(c.value)">{{ countBy(c.value) }}</em>
        </span>
      </div>
      <button class="btn btn-ghost" style="padding: 6px 10px; font-size: 12px; flex-shrink: 0" @click="load">
        刷新
      </button>
    </div>

    <div v-if="loading" class="empty">加载中…</div>
    <div v-else-if="filtered.length === 0" class="empty">
      <div class="empty-icon">📭</div>暂无任务（切换状态筛选查看）
    </div>

    <div v-for="t in filtered" :key="t.id" class="card task-card" @click="openTask(t)">
      <div class="row">
        <span class="tag" :class="STATUS[t.status]?.cls">{{ STATUS[t.status]?.label }}</span>
        <span class="muted">{{ fmtDate(t.created_at) }}</span>
      </div>
      <div class="task-title ellipsis">{{ t.title }}</div>
      <div class="row muted" style="margin-top: 8px">
        <span class="ellipsis" style="max-width: 60%">项目：{{ t.project_name }}</span>
        <span>
          <span v-if="t.attachment_required" class="tag tag-warning" style="margin-right: 4px">需附件</span>
          <span v-if="t.status === 'rejected'" class="tag tag-danger">被驳回</span>
        </span>
      </div>
    </div>

    <div v-if="current" class="sheet-mask" @click="closeTask"></div>
    <div class="sheet" v-if="current">
      <TaskSheet :task="current" @close="closeTask" @saved="onSaved" />
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { api } from '../api'
import { fmtDate } from '../utils/format'
import TaskSheet from '../components/TaskSheet.vue'

const route = useRoute()
const tasks = ref([])
const loading = ref(false)
const filter = ref('all')
const current = ref(null)

const STATUS = {
  pending: { label: '待处理', cls: 'tag-primary' },
  completed: { label: '待确认', cls: 'tag-warning' },
  approved: { label: '已确认', cls: 'tag-success' },
  rejected: { label: '已驳回', cls: 'tag-danger' },
  overdue: { label: '已超时', cls: 'tag-danger' },
  late: { label: '已延毕', cls: 'tag-warning' },
}

const chips = [
  { value: 'all', label: '全部' },
  { value: 'pending', label: '待处理' },
  { value: 'overdue', label: '已超时' },
  { value: 'rejected', label: '已驳回' },
  { value: 'completed', label: '待确认' },
  { value: 'approved', label: '已确认' },
  { value: 'late', label: '已延毕' },
]

const filtered = computed(() => {
  if (filter.value === 'all') return tasks.value
  if (filter.value === 'overdue') return tasks.value.filter((t) => t.is_overdue || t.is_late)
  return tasks.value.filter((t) => t.status === filter.value)
})

function countBy(v) {
  if (v === 'all') return tasks.value.length
  if (v === 'overdue') return tasks.value.filter((t) => t.is_overdue || t.is_late).length
  return tasks.value.filter((t) => t.status === v).length
}

function setFilter(v) {
  filter.value = v
}

async function load() {
  loading.value = true
  try {
    tasks.value = await api.tasks.list({ scope: 'mine' })
    const focus = Number(route.query.focus)
    if (focus) {
      const target = tasks.value.find((t) => t.id === focus)
      if (target) current.value = target
    }
  } catch (e) {
    alert(e.message)
  } finally {
    loading.value = false
  }
}

function openTask(t) {
  current.value = t
}

function closeTask() {
  current.value = null
}

function onSaved(updated) {
  const idx = tasks.value.findIndex((t) => t.id === updated.id)
  if (idx >= 0) tasks.value[idx] = updated
  current.value = null
  alert(updated.status === 'approved' ? '已确认完成，任务结束' : updated.status === 'rejected' ? '已驳回，已通知对方' : '已提交，等待项目经理确认')
}

onMounted(load)
</script>

<style scoped>
.chips {
  display: flex;
  gap: 8px;
  overflow-x: auto;
  padding-bottom: 4px;
  flex: 1;
}
.chip {
  flex-shrink: 0;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 6px 12px;
  border-radius: 999px;
  background: #fff;
  border: 1px solid var(--line);
  color: var(--sub);
  font-size: 13px;
  cursor: pointer;
}
.chip em {
  font-style: normal;
  font-size: 11px;
  background: rgba(110, 168, 254, 0.1);
  color: var(--primary);
  border-radius: 999px;
  padding: 0 5px;
}
.chip.active {
  background: var(--primary-grad);
  border-color: transparent;
  color: #fff;
}
.chip.active em {
  background: rgba(255, 255, 255, 0.25);
  color: #fff;
}
.task-card {
  cursor: pointer;
}
.task-title {
  font-size: 15px;
  font-weight: 600;
  margin-top: 8px;
}
</style>