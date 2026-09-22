<template>
  <div class="page">
    <el-card class="welcome" shadow="never">
      <div class="welcome-row">
        <div>
          <h2 class="welcome-name">{{ greeting }}，{{ userStore.user?.username }}</h2>
          <p class="sub">
            欢迎回来，当前角色：<el-tag size="small" effect="dark" :type="tagType">{{ userStore.roleLabel }}</el-tag>
          </p>
        </div>
        <el-button class="welcome-btn" @click="goToTasks">查看我的任务</el-button>
      </div>
    </el-card>

    <!-- ============ 项目经理 / 管理员视图 ============ -->
    <template v-if="userStore.isManager">
      <el-row :gutter="16" style="margin-top: 16px">
        <el-col :span="6">
          <el-card shadow="never" class="stat-card stat-1" @click="goProjects">
            <div class="stat-inner">
              <div class="stat-icon"><el-icon><FolderOpened /></el-icon></div>
              <div class="stat-body"><el-statistic title="未关闭项目" :value="projectCount" /></div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card shadow="never" class="stat-card stat-2" @click="pmTab = 'confirm'" :class="{ active: pmTab === 'confirm' }">
            <div class="stat-inner">
              <div class="stat-icon"><el-icon><CircleCheck /></el-icon></div>
              <div class="stat-body"><el-statistic title="待确认任务" :value="pmStats.confirm" /></div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card shadow="never" class="stat-card stat-3" @click="pmTab = 'open'" :class="{ active: pmTab === 'open' }">
            <div class="stat-inner">
              <div class="stat-icon"><el-icon><Loading /></el-icon></div>
              <div class="stat-body"><el-statistic title="未完成任务" :value="pmStats.open" /></div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card shadow="never" class="stat-card stat-4" @click="pmTab = 'overdue'" :class="{ active: pmTab === 'overdue' }">
            <div class="stat-inner">
              <div class="stat-icon"><el-icon><Warning /></el-icon></div>
              <div class="stat-body"><el-statistic title="已超时任务" :value="pmStats.overdue" /></div>
            </div>
          </el-card>
        </el-col>
      </el-row>

      <el-card shadow="never" class="page-card" style="margin-top: 16px">
        <template #header>
          <div class="card-head">
            <span>{{ pmTabTitle }}（{{ pmTabList.length }}）</span>
            <div>
              <el-radio-group v-model="pmTab" size="small" style="margin-right: 12px">
                <el-radio-button value="confirm">待确认</el-radio-button>
                <el-radio-button value="open">未完成</el-radio-button>
                <el-radio-button value="overdue">已超时</el-radio-button>
                <el-radio-button value="milestone">里程碑</el-radio-button>
              </el-radio-group>
              <el-button link type="primary" @click="goArchive">归档项目 →</el-button>
            </div>
          </div>
        </template>
        <div class="scroll-area">
        <el-empty v-if="pmTabList.length === 0" :description="pmTabTitle + '暂无数据'" />
        <el-table v-else :data="pmTabList" @row-click="row => openProject(row)">
          <el-table-column prop="title" label="任务标题" min-width="170" />
          <el-table-column prop="project_name" label="所属项目" width="130" />
          <el-table-column prop="assignee_name" label="被派发人" width="100" />
          <el-table-column label="状态" width="140">
            <template #default="{ row }">
              <span class="status-inline">
                <el-tag :type="statusTag(row.status).type" size="small">{{ statusTag(row.status).label }}</el-tag>
                <span v-if="row.is_milestone" class="mile-inline">| 里程碑</span>
              </span>
            </template>
          </el-table-column>
          <el-table-column label="预计完成" width="150">
            <template #default="{ row }">{{ row.due_at ? fmtDate(row.due_at) : '-' }}</template>
          </el-table-column>
          <el-table-column label="要求附件" width="95">
            <template #default="{ row }">
              <el-tag v-if="row.attachment_required" type="warning" size="small">需要</el-tag>
              <span v-else>-</span>
            </template>
          </el-table-column>
          <el-table-column label="派发时间" width="150">
            <template #default="{ row }">{{ fmtDate(row.created_at) }}</template>
          </el-table-column>
        </el-table>
        </div>
      </el-card>
    </template>

    <!-- ============ 普通工作人员视图 ============ -->
    <template v-else>
      <el-card shadow="never" class="page-card" style="margin-top: 16px">
        <template #header>
          <div class="card-head">
            <span>我的待处理任务（{{ pendingTasks.length }}）</span>
            <el-button link type="primary" @click="goToTasks">全部任务 →</el-button>
          </div>
        </template>
        <div class="scroll-area">
        <el-empty v-if="pendingTasks.length === 0" description="太棒了，暂无待处理任务" />
        <el-table v-else :data="pendingTasks" @row-click="(row) => goToTasks(row)">
          <el-table-column prop="title" label="任务标题" min-width="180" />
          <el-table-column prop="project_name" label="所属项目" width="140" />
          <el-table-column label="状态" width="110">
            <template #default="{ row }">
              <el-tag :type="statusTag(row.status).type" size="small">{{ statusTag(row.status).label }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="要求附件" width="100">
            <template #default="{ row }">
              <el-tag v-if="row.attachment_required" type="warning" size="small">需要</el-tag>
              <span v-else>-</span>
            </template>
          </el-table-column>
          <el-table-column label="派发时间" width="160">
            <template #default="{ row }">{{ fmtDate(row.created_at) }}</template>
          </el-table-column>
        </el-table>
        </div>
      </el-card>

      <el-row :gutter="16" style="margin-top: 16px">
        <el-col :span="8">
          <el-card shadow="never" class="stat-card stat-1">
            <div class="stat-inner">
              <div class="stat-icon"><el-icon><Tickets /></el-icon></div>
              <div class="stat-body"><el-statistic title="我的总任务" :value="stats.total" /></div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="8">
          <el-card shadow="never" class="stat-card stat-2">
            <div class="stat-inner">
              <div class="stat-icon"><el-icon><CircleCheck /></el-icon></div>
              <div class="stat-body"><el-statistic title="已完成" :value="stats.done" /></div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="8">
          <el-card shadow="never" class="stat-card stat-3">
            <div class="stat-inner">
              <div class="stat-icon"><el-icon><Loading /></el-icon></div>
              <div class="stat-body"><el-statistic title="处理中" :value="stats.pending" /></div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </template>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api'
import { useUserStore } from '../stores/user'
import { fmtDate } from '../utils/format'

const router = useRouter()
const userStore = useUserStore()

const tasks = ref([])
const pmTab = ref('confirm')
const projectCount = ref(0)

const PM_TABS = {
  confirm: { title: '待确认任务', filter: (t) => t.status === 'completed' },
  open: { title: '未完成任务', filter: (t) => !t.is_overdue && (t.status === 'pending' || t.status === 'rejected') },
  overdue: { title: '已超时任务', filter: (t) => t.is_overdue },
  milestone: { title: '项目里程碑', filter: (t) => t.is_milestone },
}

const tagType = computed(() => {
  const map = { admin: 'danger', pm: 'warning', dev: 'primary', tester: 'success', ops: 'info' }
  return map[userStore.user?.role] || 'info'
})

const greeting = computed(() => {
  const h = new Date().getHours()
  if (h < 6) return '夜深了，注意休息'
  if (h < 12) return '早上好'
  if (h < 14) return '中午好'
  if (h < 18) return '下午好'
  return '晚上好'
})

const STATUS_MAP = {
  pending: { label: '待处理', type: 'primary' },
  completed: { label: '待确认', type: 'warning' },
  approved: { label: '已确认', type: 'success' },
  rejected: { label: '已驳回', type: 'danger' },
  overdue: { label: '已超时', type: 'danger' },
  late: { label: '已延毕', type: 'warning' },
}

function statusTag(status) {
  return STATUS_MAP[status] || { label: status, type: 'info' }
}

// ---- PM 视角 ----
const pmStats = computed(() => ({
  confirm: tasks.value.filter((t) => t.status === 'completed').length,
  open: tasks.value.filter((t) => !t.is_overdue && (t.status === 'pending' || t.status === 'rejected')).length,
  overdue: tasks.value.filter((t) => t.is_overdue).length,
  milestone: tasks.value.filter((t) => t.is_milestone).length,
}))

const pmTabTitle = computed(() => PM_TABS[pmTab.value].title)
const pmTabList = computed(() => tasks.value.filter(PM_TABS[pmTab.value].filter).slice(0, 20))

// ---- 员工视角 ----
const pendingTasks = computed(() =>
  tasks.value.filter((t) => t.status === 'pending' || t.status === 'rejected'),
)
const stats = computed(() => ({
  total: tasks.value.length,
  done: tasks.value.filter((t) => t.status === 'approved' || t.status === 'completed').length,
  pending: pendingTasks.value.length,
}))

function goToTasks() {
  router.push('/tasks')
}

function goProjects() {
  router.push('/projects')
}

function openProject(row) {
  router.push(`/projects/${row.project_id}`)
}

function goArchive() {
  router.push('/archived')
}

onMounted(async () => {
  // 项目经理/管理员拉取所管理项目的任务；普通员工拉取自己的任务
  tasks.value = await api.tasks.list({ scope: userStore.isManager ? 'managed' : 'mine' })
  if (userStore.isManager) {
    try {
      projectCount.value = (await api.projects.list()).length
    } catch (e) {
      /* 忽略 */
    }
  }
})
</script>

<style scoped>
.welcome {
  border: none;
  background: linear-gradient(120deg, #5a92e8 0%, #6ea8fe 55%, #93b8ff 100%);
  border-radius: 16px;
  box-shadow: 0 16px 40px rgba(110, 168, 254, 0.32);
  flex: none;
}
.page :deep(.el-row) {
  flex: none;
}
.welcome-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.welcome-name {
  margin: 0;
  color: #fff;
  font-size: 22px;
}
.sub {
  color: rgba(255, 255, 255, 0.85);
  margin: 8px 0 0;
}
.welcome-btn {
  background: rgba(255, 255, 255, 0.16);
  border: 1px solid rgba(255, 255, 255, 0.35);
  color: #fff;
  border-radius: 10px;
}
.welcome-btn:hover {
  background: rgba(255, 255, 255, 0.28);
  color: #fff;
}
.card-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.stat-card {
  position: relative;
  overflow: hidden;
  cursor: pointer;
  transition: transform 0.25s ease, box-shadow 0.25s ease, border-color 0.2s;
}
.stat-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 12px 28px rgba(110, 168, 254, 0.18);
}
.stat-card::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 4px;
}
.stat-1::before {
  background: linear-gradient(180deg, #6ea8fe, #38bdf8);
}
.stat-2::before {
  background: linear-gradient(180deg, #f59e0b, #f97316);
}
.stat-3::before {
  background: linear-gradient(180deg, #22d3ee, #38bdf8);
}
.stat-4::before {
  background: linear-gradient(180deg, #ef4444, #f97316);
}
.stat-card.active {
  border-color: #6ea8fe;
}
.stat-inner {
  display: flex;
  align-items: center;
  gap: 14px;
  padding-left: 6px;
}
.stat-icon {
  width: 46px;
  height: 46px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
  color: #fff;
}
.stat-1 .stat-icon {
  background: linear-gradient(135deg, #6ea8fe, #38bdf8);
}
.stat-2 .stat-icon {
  background: linear-gradient(135deg, #f59e0b, #f97316);
}
.stat-3 .stat-icon {
  background: linear-gradient(135deg, #22d3ee, #38bdf8);
}
.stat-4 .stat-icon {
  background: linear-gradient(135deg, #ef4444, #f87171);
}
.status-inline {
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
.stat-card :deep(.el-statistic__number) {
  color: var(--app-text-main);
  font-weight: 700;
}
.stat-card :deep(.el-statistic__head) {
  color: var(--app-text-sub);
  font-size: 13px;
}
</style>