<template>
  <div class="page" v-if="project">
    <div class="card head-card">
      <div class="row">
        <div class="proj-mark">{{ project.name.slice(0, 1) }}</div>
        <div style="min-width: 0">
          <div class="proj-name ellipsis">
            {{ project.name }}
            <span v-if="project.archived" class="tag tag-archived">已归档（只读）</span>
          </div>
          <div class="muted ellipsis" style="margin-top: 4px">{{ project.description || '暂无描述' }}</div>
        </div>
      </div>
      <div class="row muted" style="margin-top: 12px">
        <span>负责人 {{ project.manager_name }}</span>
        <span>成员 {{ members.length }} 人</span>
      </div>
      <div v-if="canManage" class="row" style="margin-top: 12px">
        <button v-if="!project.archived" class="btn btn-danger-outline btn-sm" @click="archiveProject">
          关闭项目
        </button>
        <template v-else>
          <button class="btn btn-ghost btn-sm" @click="unarchiveProject">恢复项目</button>
          <button class="btn btn-danger-outline btn-sm" @click="deleteProject">永久删除</button>
        </template>
      </div>
    </div>

    <!-- 任务 -->
    <div class="row" style="margin: 4px 2px 8px">
      <span style="font-weight: 700">项目任务（{{ taskList.length }}）</span>
      <div class="btn-group">
        <span v-if="canManage" class="muted primary-text" @click="exportTasks">⬇ 导出</span>
        <span class="muted primary-text" @click="openMembers">👥 项目成员</span>
        <span v-if="canManage && !project.archived" class="muted primary-text" @click="openDispatch">＋ 派发任务</span>
      </div>
    </div>

    <div class="chips" style="margin: 0 2px 10px">
      <span
        v-for="c in statusChips"
        :key="c.value"
        class="chip"
        :class="{ active: taskFilter === c.value }"
        @click="taskFilter = c.value"
      >{{ c.label }}</span>
    </div>

    <div v-if="taskList.length > 0" class="card progress-card">
      <div class="progress-label">
        <span>项目时间进度</span>
        <b>{{ progress.percent.toFixed(0) }}%</b>
      </div>
      <div class="progress-track">
        <div class="progress-fill" :style="{ width: progress.percent + '%' }"></div>
        <span
          v-for="f in progress.flags"
          :key="f.task_id"
          class="progress-flag"
          :style="{ left: f.left + '%' }"
          :title="f.title"
        >🚩</span>
      </div>
    </div>

    <div v-if="taskList.length === 0" class="card empty" style="padding: 24px 0">
      <div class="empty-icon">📋</div>暂无任务
    </div>
    <div v-else class="task-scroll">
      <div v-for="t in pagedTasks" :key="t.id" class="card task-card" @click="openTask(t)">
        <div class="row">
          <span class="status-pair">
            <span :class="['tag', STATUS[t.status]?.cls]">{{ STATUS[t.status]?.label }}</span>
            <span v-if="t.is_milestone" class="mile-inline">| 里程碑</span>
          </span>
          <span class="muted" style="margin-left: auto">{{ fmtDate(t.created_at) }}</span>
        </div>
        <div class="ellipsis" style="font-size: 15px; font-weight: 600; margin-top: 8px">{{ t.title }}</div>
        <div class="row muted" style="margin-top: 8px">
          <span class="ellipsis">{{ t.assignee_name }} 负责</span>
          <span>
            <span v-if="t.attachment_required" class="tag tag-warning" style="margin-right: 4px">需附件</span>
            <span v-if="t.due_at" class="muted">{{ fmtDate(t.due_at) }}</span>
          </span>
        </div>
      </div>
      <div class="pager">
        <span>每页</span>
        <span class="chip" :class="{ active: pageSize === n }" v-for="n in [5, 10, 20]" :key="n" @click="setPageSize(n)">{{ n }}</span>
        <span class="pager-info">{{ page }} / {{ totalPages || 1 }}</span>
        <button class="btn btn-ghost" style="padding: 4px 10px; font-size: 12px" :disabled="page <= 1" @click="page--">上一页</button>
        <button class="btn btn-ghost" style="padding: 4px 10px; font-size: 12px" :disabled="page >= totalPages" @click="page++">下一页</button>
      </div>
    </div>

    <!-- 项目成员（模态框） -->
    <div v-if="membersVisible" class="sheet-mask" @click="membersVisible = false"></div>
    <div class="sheet" v-if="membersVisible">
      <div class="sheet-title">
        <span>项目成员（{{ members.length }}）</span>
        <span class="muted primary-text" v-if="canManage && !project.archived" @click="openAddMember">＋ 添加成员</span>
      </div>
      <div v-for="m in members" :key="m.id" class="member-row">
        <div class="member-ava">{{ (m.full_name || m.username || '?').slice(0, 1) }}</div>
        <div style="min-width: 0; flex: 1">
          <div class="ellipsis">{{ m.full_name || m.username }}</div>
          <div class="muted">{{ ROLE_LABELS[m.role] || m.role }}</div>
          <div class="muted contact-line">
            <span class="copyable" v-if="m.email" @click.stop="copyEmail(m.email)">📧 {{ m.email }}</span>
            <span class="copyable" v-if="m.phone" style="margin-left: 8px" @click.stop="copyPhone(m.phone)">📱 {{ m.phone }}</span>
            <span v-if="!m.email && !m.phone">未填写联系方式</span>
          </div>
        </div>
        <span v-if="canManage && !project.archived" class="del" @click="removeMember(m)">✕</span>
      </div>
      <div v-if="members.length === 0" class="muted" style="text-align: center; padding: 20px 0">暂无成员</div>
    </div>

    <!-- 添加成员 -->
    <div v-if="addVisible" class="sheet-mask" @click="addVisible = false"></div>
    <div class="sheet" v-if="addVisible && candidates">
      <div class="sheet-title">
        <span>添加成员</span>
        <button class="btn btn-ghost" style="padding: 4px 10px; font-size: 12px" @click="addVisible = false">关闭</button>
      </div>
      <div v-if="candidates.length === 0" class="muted" style="text-align: center; padding: 20px 0">
        暂无可添加人员（仅可添加开发/测试/运维角色）
      </div>
      <div v-for="c in candidates" :key="c.user_id" class="cand-row" @click="addMember(c)">
        <div class="member-ava">{{ (c.full_name || c.username || '?').slice(0, 1) }}</div>
        <div style="flex: 1; min-width: 0">
          <div class="ellipsis">{{ c.full_name || c.username }}</div>
          <div class="muted">{{ ROLE_LABELS[c.role] || c.role }}</div>
        </div>
        <span class="add-btn">＋</span>
      </div>
    </div>

    <!-- 派发任务 -->
    <div v-if="dispatchVisible" class="sheet-mask" @click="dispatchVisible = false"></div>
    <div class="sheet" v-if="dispatchVisible">
      <div class="sheet-title">
        <span>派发任务</span>
        <button class="btn btn-ghost" style="padding: 4px 10px; font-size: 12px" @click="dispatchVisible = false">关闭</button>
      </div>
      <div class="field">
        <label>派发给</label>
        <select v-model="taskForm.assignee_id" class="select">
          <option :value="null" disabled>请选择工作人员</option>
          <option v-for="m in members" :key="m.user_id" :value="m.user_id">
            {{ m.full_name || m.username }}（{{ ROLE_LABELS[m.role] || m.role }}）
          </option>
        </select>
      </div>
      <div class="field">
        <label>任务标题（必填）</label>
        <input v-model.trim="taskForm.title" class="input" placeholder="一句话描述任务" />
      </div>
      <div class="field">
        <label>任务要求（语言描述）</label>
        <textarea v-model.trim="taskForm.description" class="textarea" placeholder="详细说明工作要求"></textarea>
      </div>
      <div class="field">
        <label>预计完成时间（精确到分钟，可选）</label>
        <input v-model="taskForm.due_at" type="datetime-local" class="input" />
        <div class="muted" style="font-size: 12px; margin-top: 4px">到期未完成将自动标记为“已超时”</div>
      </div>
      <label class="check-line" style="padding-top: 2px">
        <input v-model="taskForm.is_milestone" type="checkbox" />
        <span>标记为项目里程碑任务</span>
      </label>
      <label class="check-line">
        <input v-model="taskForm.attachment_required" type="checkbox" />
        <span>需要工作人员反馈附件产物（可勾选也可不勾，由工作人员自行提交）</span>
      </label>
      <button class="btn btn-primary btn-block" style="margin-top: 10px" :disabled="dispatching" @click="dispatch">
        {{ dispatching ? '派发中…' : '确认派发' }}
      </button>
    </div>

    <!-- 任务弹层 -->
    <div v-if="current" class="sheet-mask" @click="current = null"></div>
    <div class="sheet" v-if="current">
      <TaskSheet :task="current" :archived="!!project.archived" @close="current = null" @saved="onTaskSaved" />
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useUserStore } from '../stores/user'
import { api } from '../api'
import { fmtDate } from '../utils/format'
import { toast } from '../utils/toast'
import TaskSheet from '../components/TaskSheet.vue'

const route = useRoute()
const projectId = Number(route.params.id)
const userStore = useUserStore()

const project = ref(null)
const members = ref([])
const tasks = ref([])
const candidates = ref([])
const current = ref(null)
const taskFilter = ref('all')
const membersVisible = ref(false)
const page = ref(1)
const pageSize = ref(10)

const statusChips = [
  { value: 'all', label: '全部' },
  { value: 'doing', label: '进行中' },
  { value: 'done', label: '已完成' },
  { value: 'overdue', label: '已超时' },
]

const taskList = computed(() => {
  let list = tasks.value
  const f = taskFilter.value
  if (f === 'doing') {
    list = list.filter((t) => !t.is_overdue && (t.status === 'pending' || t.status === 'rejected'))
  } else if (f === 'done') {
    list = list.filter((t) => t.status === 'completed' || t.status === 'approved' || t.status === 'late')
  } else if (f === 'overdue') {
    list = list.filter((t) => t.is_overdue || t.is_late)
  }
  // 按预计完成时间从近到远排序（未设置预计时间的排在最后）
  return [...list].sort((a, b) => {
    const da = a.due_at ? new Date(a.due_at).getTime() : Infinity
    const db = b.due_at ? new Date(b.due_at).getTime() : Infinity
    return da - db
  })
})

const totalPages = computed(() => Math.max(1, Math.ceil(taskList.value.length / pageSize.value)))
const pagedTasks = computed(() => {
  const start = (page.value - 1) * pageSize.value
  return taskList.value.slice(start, start + pageSize.value)
})
watch(taskFilter, () => (page.value = 1))

function setPageSize(n) {
  pageSize.value = n
  page.value = 1
}

// 项目时间进度：以项目任务的时间范围（最早创建/预计完成 → 最晚预计完成）为轴线
const progress = computed(() => {
  const all = tasks.value
  if (!all.length) return { percent: 0, flags: [] }
  const dueList = all.map((t) => (t.due_at ? new Date(t.due_at).getTime() : null)).filter(Boolean)
  const createdList = all.map((t) => new Date(t.created_at).getTime())
  if (!dueList.length) return { percent: 0, flags: [] }
  const start = Math.min(...createdList, ...dueList)
  const end = Math.max(...dueList)
  const now = Date.now()
  let percent = end > start ? ((now - start) / (end - start)) * 100 : 0
  percent = Math.max(0, Math.min(100, percent))
  const flags = all
    .filter((t) => t.is_milestone && t.due_at)
    .map((t) => ({
      task_id: t.id,
      title: t.title,
      left: Math.max(0, Math.min(100, ((new Date(t.due_at).getTime() - start) / (end - start)) * 100)),
    }))
  return { percent, flags }
})

async function openMembers() {
  membersVisible.value = true
  try {
    members.value = await api.projects.members(projectId)
  } catch (e) {
    /* 忽略 */
  }
}

const addVisible = ref(false)
const dispatchVisible = ref(false)
const dispatching = ref(false)
const taskForm = reactive({
  assignee_id: null,
  title: '',
  description: '',
  attachment_required: false,
  due_at: '',
  is_milestone: false,
})

const STATUS = {
  pending: { label: '待处理', cls: 'tag-primary' },
  completed: { label: '待确认', cls: 'tag-warning' },
  approved: { label: '已确认', cls: 'tag-success' },
  rejected: { label: '已驳回', cls: 'tag-danger' },
  overdue: { label: '已超时', cls: 'tag-danger' },
  late: { label: '已延毕', cls: 'tag-warning' },
}
const ROLE_LABELS = {
  admin: '管理员',
  pm: '项目经理',
  dev: '开发人员',
  tester: '测试人员',
  ops: '运维人员',
}

const canManage = computed(() =>
  userStore.isAdmin || project.value?.manager_id === userStore.user?.id,
)

async function copyText(text) {
  if (!text) return
  const fallback = () => {
    const ta = document.createElement('textarea')
    ta.value = text
    ta.style.position = 'fixed'
    ta.style.opacity = '0'
    document.body.appendChild(ta)
    ta.select()
    document.execCommand('copy')
    document.body.removeChild(ta)
  }
  try {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      await navigator.clipboard.writeText(text)
    } else {
      fallback()
    }
    return true
  } catch (e) {
    try {
      fallback()
      return true
    } catch (e2) {
      return false
    }
  }
}

async function copyPhone(phone) {
  const ok = await copyText(phone)
  toast(ok ? '手机号已复制：' + phone : '复制失败，请长按手动复制')
}

async function copyEmail(email) {
  const ok = await copyText(email)
  toast(ok ? '邮箱已复制：' + email : '复制失败，请长按手动复制')
}

/** 导出当前筛选结果的 CSV */
function exportTasks() {
  const list = taskList.value
  if (list.length === 0) {
    toast('当前筛选结果为空')
    return
  }
  const esc = (v) => {
    const s = v == null ? '' : String(v)
    return /[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s
  }
  const head = ['任务', '被派发人', '状态', '里程碑', '预计完成时间', '派发时间', '提交时间', '要求附件']
  const rows = list.map((t) => [
    t.title,
    t.assignee_name,
    STATUS[t.status]?.label || t.status,
    t.is_milestone ? '是' : '否',
    t.due_at ? fmtDate(t.due_at) : '',
    fmtDate(t.created_at),
    t.completed_at ? fmtDate(t.completed_at) : '',
    t.attachment_required ? '需要' : '',
  ])
  const content = '\uFEFF' + [head, ...rows].map((r) => r.map(esc).join(',')).join('\r\n')
  const blob = new Blob([content], { type: 'text/csv;charset=utf-8' })
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob)
  a.download = `项目任务_${project.value?.name || projectId}_${new Date().toISOString().slice(0, 10)}.csv`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  setTimeout(() => URL.revokeObjectURL(a.href), 3000)
  toast(`已导出 ${rows.length} 条任务`)
}

async function load() {
  try {
    const [p, ms, t] = await Promise.all([
      api.projects.get(projectId),
      api.projects.members(projectId),
      api.tasks.list({ project_id: projectId, scope: 'member' }),
    ])
    project.value = p
    members.value = ms
    tasks.value = t
  } catch (e) {
    alert(e.message)
  }
}

async function openAddMember() {
  addVisible.value = true
  try {
    candidates.value = await api.projects.candidates(projectId)
  } catch (e) {
    alert(e.message)
  }
}

async function addMember(c) {
  try {
    await api.projects.setMember(projectId, { user_id: c.user_id })
    addVisible.value = false
    await load()
    alert('已添加成员')
  } catch (e) {
    alert(e.message)
  }
}

async function removeMember(m) {
  if (!confirm(`确定将「${m.full_name || m.username}」移出项目？未完成任务将保留`)) return
  try {
    await api.projects.removeMember(projectId, m.user_id)
    await load()
  } catch (e) {
    alert(e.message)
  }
}

function openDispatch() {
  taskForm.assignee_id = null
  taskForm.title = ''
  taskForm.description = ''
  taskForm.attachment_required = false
  taskForm.due_at = ''
  taskForm.is_milestone = false
  dispatchVisible.value = true
}

async function dispatch() {
  if (!taskForm.assignee_id) {
    alert('请选择派发对象')
    return
  }
  if (!taskForm.title) {
    alert('请输入任务标题')
    return
  }
  dispatching.value = true
  try {
    await api.tasks.create(projectId, {
      assignee_id: taskForm.assignee_id,
      title: taskForm.title,
      description: taskForm.description,
      attachment_required: taskForm.attachment_required,
      due_at: taskForm.due_at || undefined,
      is_milestone: taskForm.is_milestone,
    })
    dispatchVisible.value = false
    await load()
    alert('任务已派发，已通知对方')
  } catch (e) {
    alert(e.message)
  } finally {
    dispatching.value = false
  }
}

function archiveProject() {
  if (!confirm(`确定关闭项目「${project.value?.name}」？关闭后：任务不可派发、所有任务状态锁定、普通成员不可见，仅你可查看。`)) return
  api.projects
    .archive(projectId)
    .then(async () => {
      await load()
      alert('项目已关闭归档')
    })
    .catch((e) => alert(e.message))
}

function unarchiveProject() {
  if (!confirm(`确定恢复项目「${project.value?.name}」？`)) return
  api.projects
    .unarchive(projectId)
    .then(async () => {
      await load()
      alert('项目已恢复')
    })
    .catch((e) => alert(e.message))
}

function deleteProject() {
  if (!confirm(`确定永久删除项目「${project.value?.name}」？其下所有任务、成员、统计记录将被一并删除，且不可恢复。`)) return
  api.projects
    .remove(projectId)
    .then(() => {
      toast('项目已永久删除')
      router.replace('/archived')
    })
    .catch((e) => alert(e.message))
}

function openTask(t) {
  current.value = t
}

async function onTaskSaved(updated) {
  const idx = tasks.value.findIndex((t) => t.id === updated.id)
  if (idx >= 0) tasks.value[idx] = updated
  current.value = null
  alert(
    updated.status === 'approved'
      ? '已确认完成，任务结束'
      : updated.status === 'rejected'
        ? '已驳回，已通知对方'
        : '已提交，等待项目经理确认',
  )
}

onMounted(load)
</script>

<style scoped>
.head-card {
  position: relative;
  overflow: hidden;
}
.head-card::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, #6ea8fe, #38bdf8, #22d3ee);
}
.proj-mark {
  width: 46px;
  height: 46px;
  border-radius: 12px;
  background: linear-gradient(135deg, #6ea8fe, #38bdf8);
  color: #fff;
  font-size: 20px;
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
.member-card {
  padding: 6px 14px;
}
.member-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 0;
  border-bottom: 1px solid var(--line);
}
.member-row:last-child {
  border-bottom: none;
}
.member-ava {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  background: linear-gradient(135deg, #6ea8fe, #38bdf8);
  color: #fff;
  font-size: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.del {
  color: var(--danger);
  font-size: 16px;
  padding: 4px 6px;
}
.cand-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 2px;
  border-bottom: 1px solid var(--line);
  cursor: pointer;
}
.add-btn {
  width: 26px;
  height: 26px;
  border-radius: 50%;
  background: rgba(110, 168, 254, 0.12);
  color: var(--primary);
  font-size: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.check-line {
  display: flex;
  gap: 8px;
  align-items: flex-start;
  font-size: 13px;
  color: var(--sub);
  padding: 4px 2px 10px;
}
.task-card {
  cursor: pointer;
}
.tag-archived {
  background: rgba(156, 163, 175, 0.15);
  color: #6b7280;
  margin-left: 6px;
  vertical-align: middle;
}
.tag-milestone {
  background: rgba(245, 158, 11, 0.12);
  color: #b45309;
  margin-left: 6px;
}
.status-pair {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  white-space: nowrap;
}
.mile-inline {
  color: #f59e0b;
  font-size: 12px;
  font-weight: 600;
}
.btn-group {
  display: flex;
  gap: 12px;
}
.btn-sm {
  padding: 6px 12px;
  font-size: 12px;
}
.progress-card {
  padding: 12px 14px;
  background: #f8faff;
  border: 1px solid rgba(79, 110, 247, 0.12);
}
.progress-label {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 13px;
  color: var(--sub);
  margin-bottom: 8px;
}
.progress-label b {
  color: var(--primary);
  font-size: 15px;
}
.progress-track {
  position: relative;
  height: 12px;
  border-radius: 6px;
  background: #e3e9fb;
  overflow: visible;
}
.progress-fill {
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  border-radius: 6px;
  background: var(--primary-grad);
}
.progress-flag {
  position: absolute;
  top: -13px;
  transform: translateX(-50%);
  font-size: 18px;
  line-height: 1;
}
.task-scroll {
  max-height: 64vh;
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
  padding-right: 2px;
}
.pager {
  display: flex;
  align-items: center;
  gap: 6px;
  justify-content: flex-end;
  margin-top: 4px;
  font-size: 13px;
  color: var(--sub);
}
.pager .chip {
  padding: 4px 8px;
  font-size: 12px;
}
.pager .chip.active {
  background: var(--primary-grad);
  color: #fff;
}
.pager-info {
  margin: 0 2px;
}
.contact-line {
  margin-top: 2px;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}
.copyable {
  color: var(--primary);
  text-decoration: underline dashed;
  cursor: pointer;
  position: relative;
}
.chips {
  display: flex;
  gap: 8px;
  overflow-x: auto;
  padding-bottom: 4px;
}
.chip {
  flex-shrink: 0;
  padding: 6px 12px;
  border-radius: 999px;
  background: #fff;
  border: 1px solid var(--line);
  color: var(--sub);
  font-size: 13px;
  cursor: pointer;
}
.chip.active {
  background: var(--primary-grad);
  border-color: transparent;
  color: #fff;
}
</style>