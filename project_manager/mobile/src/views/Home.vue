<template>
  <div class="page">
    <div class="welcome-card">
      <div class="row">
        <div>
          <div class="welcome-hi">{{ greeting() }}，{{ userStore.user?.full_name || userStore.user?.username }}</div>
          <div class="welcome-sub">{{ welcomeRole }}欢迎回来</div>
        </div>
        <span class="tag tag-primary">{{ userStore.roleLabel }}</span>
      </div>
    </div>

    <!-- ===== 项目经理 / 管理员视图 ===== -->
    <template v-if="userStore.isPM">
      <div class="stat-grid pm2">
        <div class="stat card sc-c-proj" @click="go('/projects')">
          <div class="stat-num">{{ projectCount }}</div>
          <div class="stat-label">未关闭项目</div>
        </div>
        <div class="stat card sc-c-todo" @click="pmTab = 'confirm'">
          <div class="stat-num">{{ pmStats.confirm }}</div>
          <div class="stat-label">待确认任务</div>
        </div>
        <div class="stat card sc-c-open" @click="pmTab = 'open'">
          <div class="stat-num">{{ pmStats.open }}</div>
          <div class="stat-label">未完成任务</div>
        </div>
        <div class="stat card sc-c-over" @click="pmTab = 'overdue'">
          <div class="stat-num">{{ pmStats.overdue }}</div>
          <div class="stat-label">已超时任务</div>
        </div>
      </div>

      <div class="row" style="margin: 4px 0 10px">
        <span style="font-weight: 700">快捷操作</span>
      </div>
      <div class="quick-grid">
        <div class="quick card" @click="go('/projects')">
          <span class="qi qi-blue">🗂️</span>
          <span>项目管理</span>
        </div>
        <div class="quick card" @click="go('/archived')">
          <span class="qi qi-gray">📦</span>
          <span>归档项目</span>
        </div>
        <div class="quick card" @click="go('/stats')">
          <span class="qi qi-indigo">📊</span>
          <span>任务统计</span>
        </div>
      </div>

      <div class="chips" style="margin: 2px 0 10px">
        <span
          v-for="c in pmChips"
          :key="c.value"
          class="chip"
          :class="{ active: pmTab === c.value }"
          @click="pmTab = c.value"
        >{{ c.label }}</span>
      </div>

      <div v-if="pmTabList.length > 0">
        <div v-for="t in pmTabList" :key="t.id" class="card task-card" @click="openProject(t)">
          <div class="row">
            <span class="status-pair">
              <span :class="['tag', STATUS[t.status]?.cls]">{{ STATUS[t.status]?.label }}</span>
              <span v-if="t.is_milestone" class="mile-inline">| 里程碑</span>
            </span>
            <span class="muted" style="margin-left: auto">{{ fmtDate(t.created_at) }}</span>
          </div>
          <div class="ellipsis" style="font-size: 15px; font-weight: 600; margin-top: 8px">{{ t.title }}</div>
          <div class="row muted" style="margin-top: 6px">
            <span class="ellipsis">{{ t.project_name }} · {{ t.assignee_name }}</span>
            <span v-if="t.due_at" class="muted">{{ fmtDate(t.due_at) }} 到期</span>
          </div>
        </div>
      </div>
      <div v-else class="card empty" style="padding: 26px 0">
        <div class="empty-icon">🎯</div>{{ pmTabLabel }}暂无数据
      </div>
    </template>

    <!-- ===== 普通工作人员视图 ===== -->
    <template v-else>
      <div class="stat-grid">
        <div class="stat card sc-blue" @click="go('/tasks')">
          <div class="stat-num">{{ stats.total }}</div>
          <div class="stat-label">全部任务</div>
        </div>
        <div class="stat card sc-green" @click="go('/tasks')">
          <div class="stat-num">{{ stats.active }}</div>
          <div class="stat-label">处理中</div>
        </div>
        <div class="stat card sc-orange" @click="go('/tasks')">
          <div class="stat-num">{{ stats.done }}</div>
          <div class="stat-label">已完成</div>
        </div>
      </div>

      <div class="row" style="margin: 4px 0 10px">
        <span style="font-weight: 700">快捷操作</span>
      </div>
      <div class="quick-grid">
        <div class="quick card" @click="go('/projects')">
          <span class="qi qi-blue">🗂️</span>
          <span>项目管理</span>
        </div>
        <div class="quick card" @click="go('/report')">
          <span class="qi qi-green">📄</span>
          <span>日报导出</span>
        </div>
      </div>
    </template>

    <!-- 员工：我的待处理列表 -->
    <template v-if="!userStore.isPM">
      <div class="row" style="margin: 4px 0 10px">
        <span style="font-weight: 700">我的待处理（{{ pendingTasks.length }}）</span>
        <span class="muted primary-text" @click="go('/tasks')">查看全部 →</span>
      </div>

      <div v-if="pendingTasks.length === 0" class="card empty" style="padding: 28px 0">
        <div class="empty-icon">🎉</div>太棒了，暂无待处理任务
      </div>
      <div v-else>
        <div v-for="t in pendingTasks" :key="t.id" class="card task-card" @click="go('/tasks?focus=' + t.id)">
          <div class="row">
            <span :class="['tag', STATUS[t.status]?.cls]">{{ STATUS[t.status]?.label }}</span>
            <span class="muted">{{ fmtDate(t.created_at) }}</span>
          </div>
          <div class="ellipsis" style="font-size: 15px; font-weight: 600; margin-top: 8px">{{ t.title }}</div>
          <div class="muted ellipsis" style="margin-top: 6px">项目：{{ t.project_name }}</div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { computed, ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../stores/user'
import { api } from '../api'
import { fmtDate } from '../utils/format'

const router = useRouter()
const userStore = useUserStore()
const tasks = ref([])
const projectCount = ref(0)
const pmTab = ref('confirm')

const PM_TABS = {
  confirm: { label: '待确认任务', filter: (t) => t.status === 'completed' },
  open: { label: '未完成任务', filter: (t) => !t.is_overdue && (t.status === 'pending' || t.status === 'rejected') },
  overdue: { label: '已超时任务', filter: (t) => t.is_overdue },
  milestone: { label: '项目里程碑', filter: (t) => t.is_milestone },
}

const pmChips = [
  { value: 'confirm', label: '待确认' },
  { value: 'open', label: '未完成' },
  { value: 'overdue', label: '已超时' },
  { value: 'milestone', label: '里程碑' },
]

const STATUS = {
  pending: { label: '待处理', cls: 'tag-primary' },
  completed: { label: '待确认', cls: 'tag-warning' },
  approved: { label: '已确认', cls: 'tag-success' },
  rejected: { label: '已驳回', cls: 'tag-danger' },
  overdue: { label: '已超时', cls: 'tag-danger' },
  late: { label: '已延毕', cls: 'tag-warning' },
}

const stats = computed(() => ({
  total: tasks.value.length,
  active: tasks.value.filter((t) => t.status === 'pending' || t.status === 'rejected').length,
  done: tasks.value.filter((t) => t.status === 'completed').length,
}))

const pendingTasks = computed(() =>
  tasks.value.filter((t) => t.status === 'pending' || t.status === 'rejected').slice(0, 5),
)

// PM 视角统计
const pmStats = computed(() => ({
  confirm: tasks.value.filter((t) => t.status === 'completed').length,
  open: tasks.value.filter((t) => !t.is_overdue && (t.status === 'pending' || t.status === 'rejected')).length,
  overdue: tasks.value.filter((t) => t.is_overdue).length,
  milestone: tasks.value.filter((t) => t.is_milestone).length,
}))

const pmTabLabel = computed(() => PM_TABS[pmTab.value].label)
const pmTabList = computed(() => tasks.value.filter(PM_TABS[pmTab.value].filter).slice(0, 10))

const welcomeRole = computed(() => {
  const role = userStore.user?.role
  if (role === 'admin') return '管理员 · '
  if (role === 'pm') return '项目经理 · '
  return '工作人员 · '
})

function greeting() {
  const h = new Date().getHours()
  if (h < 6) return '凌晨好'
  if (h < 12) return '早上好'
  if (h < 14) return '中午好'
  if (h < 18) return '下午好'
  return '晚上好'
}

function go(path) {
  router.push(path.startsWith('/') ? path : '/' + path)
}

function openProject(t) {
  router.push(`/projects/${t.project_id}`)
}

async function load() {
  try {
    tasks.value = await api.tasks.list({ scope: userStore.isPM ? 'managed' : 'mine' })
    if (userStore.isPM) {
      try {
        projectCount.value = (await api.projects.list()).length
      } catch (e) {
        /* 忽略 */
      }
    }
  } catch (e) {
    /* 静默 */
  }
}

onMounted(load)
</script>

<style scoped>
.welcome-card {
  border-radius: 16px;
  padding: 18px 16px;
  background: linear-gradient(120deg, #5a92e8, #6ea8fe 60%, #93b8ff);
  color: #fff;
  margin-bottom: 12px;
  box-shadow: 0 10px 26px rgba(110, 168, 254, 0.3);
}
.welcome-hi {
  font-size: 17px;
  font-weight: 700;
}
.welcome-sub {
  font-size: 12px;
  margin-top: 5px;
  color: rgba(255, 255, 255, 0.85);
}
.welcome-card :deep(.tag-primary) {
  background: rgba(255, 255, 255, 0.2);
  color: #fff;
}
.stat-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
  margin-bottom: 14px;
}
.stat-grid.pm2 {
  grid-template-columns: repeat(2, 1fr);
}
.stat {
  text-align: center;
  padding: 14px 6px;
  cursor: pointer;
}
.stat-num {
  font-size: 22px;
  font-weight: 800;
}
.stat-label {
  font-size: 12px;
  color: var(--sub);
  margin-top: 4px;
}
.sc-blue::before,
.sc-c-open::before {
  content: '';
  display: block;
  width: 26px;
  height: 4px;
  border-radius: 2px;
  margin: 0 auto 8px;
  background: linear-gradient(90deg, #6ea8fe, #38bdf8);
}
.sc-green::before {
  content: '';
  display: block;
  width: 26px;
  height: 4px;
  border-radius: 2px;
  margin: 0 auto 8px;
  background: linear-gradient(90deg, #22c55e, #a3e635);
}
.sc-orange::before,
.sc-c-todo::before {
  content: '';
  display: block;
  width: 26px;
  height: 4px;
  border-radius: 2px;
  margin: 0 auto 8px;
  background: linear-gradient(90deg, #f59e0b, #f97316);
}
.sc-c-proj::before {
  content: '';
  display: block;
  width: 26px;
  height: 4px;
  border-radius: 2px;
  margin: 0 auto 8px;
  background: linear-gradient(90deg, #6ea8fe, #22d3ee);
}
.sc-c-over::before {
  content: '';
  display: block;
  width: 26px;
  height: 4px;
  border-radius: 2px;
  margin: 0 auto 8px;
  background: linear-gradient(90deg, #ef4444, #f87171);
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
.quick-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
  margin-bottom: 14px;
}
.quick {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: var(--text);
  cursor: pointer;
  padding: 14px 6px;
}
.qi {
  width: 40px;
  height: 40px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
}
.qi-blue {
  background: rgba(110, 168, 254, 0.1);
}
.qi-green {
  background: rgba(34, 197, 94, 0.1);
}
.qi-gray {
  background: rgba(156, 163, 175, 0.12);
}
.qi-indigo {
  background: rgba(56, 189, 248, 0.12);
}
.task-card {
  cursor: pointer;
}
.tag-mile {
  background: rgba(139, 92, 246, 0.12);
  color: #7c3aed;
  margin-left: 6px;
}
</style>