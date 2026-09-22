<template>
  <div class="page">
    <el-page-header @back="$router.back()">
      <template #content>
        <span style="font-weight: 600">{{ project?.name }}</span>
        <el-tag v-if="project?.archived" size="small" type="info" effect="dark" style="margin-left: 8px">已归档（只读）</el-tag>
        <el-tag size="small" style="margin-left: 8px">{{ managerRoleLabel }}</el-tag>
      </template>
      <template #extra>
        <el-button class="btn-members" type="primary" :icon="UserFilled" @click="openMembers">
          项目成员
        </el-button>
        <el-button v-if="canManage && !project?.archived" type="primary" :icon="Plus" @click="taskVisible = true">
          派发任务
        </el-button>
        <el-button v-if="canManage" type="success" :icon="DataAnalysis" @click="$router.push(`/stats/${project.id}`)">
          任务统计
        </el-button>
        <el-tooltip v-if="canManage" :content="project?.archived ? '恢复归档项目' : '关闭项目，任务将锁定'">
          <el-button
            v-if="!project?.archived"
            type="danger"
            plain
            :icon="Lock"
            @click="archiveProject"
          >关闭项目</el-button>
          <el-button
            v-else
            type="warning"
            plain
            :icon="Unlock"
            @click="unarchiveProject"
          >恢复项目</el-button>
        </el-tooltip>
        <el-button
          v-if="canManage && project?.archived"
          type="danger"
          :icon="Delete"
          @click="deleteProject"
        >永久删除</el-button>
      </template>
    </el-page-header>

    <!-- 项目任务（独占一行） -->
    <el-card shadow="never" class="page-card" style="margin-top: 16px">
      <template #header>
          <div class="card-head">
            <span>项目任务（{{ taskList.length }}）</span>
            <div class="task-ops">
              <el-radio-group v-model="taskScope" size="small" @change="loadTasks">
                <el-radio-button value="member">全部</el-radio-button>
                <el-radio-button value="mine">我的</el-radio-button>
              </el-radio-group>
              <el-radio-group v-model="statusFilter" size="small">
                <el-radio-button value="all">全部状态</el-radio-button>
                <el-radio-button value="doing">进行中</el-radio-button>
                <el-radio-button value="done">已完成</el-radio-button>
                <el-radio-button value="overdue">已超时</el-radio-button>
              </el-radio-group>
              <el-tooltip content="手动刷新任务状态" placement="top">
                <el-button
                  type="primary"
                  size="small"
                  :icon="Refresh"
                  circle
                  :loading="loading"
                  @click="loadTasks"
                />
              </el-tooltip>
              <el-tooltip v-if="canManage" content="导出当前筛选结果（CSV）" placement="top">
                <el-button
                  type="success"
                  size="small"
                  :icon="Download"
                  circle
                  :disabled="taskList.length === 0"
                  @click="exportTasks"
                />
              </el-tooltip>
            </div>
          </div>
        </template>
        <div class="progress-block" v-if="tasks.length > 0">
          <div class="progress-label">
            <span>项目时间进度</span>
            <b>{{ progress.percent.toFixed(0) }}%</b>
          </div>
          <div class="progress-track">
            <div class="progress-fill" :style="{ width: progress.percent + '%' }"></div>
            <el-tooltip
              v-for="f in progress.flags"
              :key="f.task_id"
              :content="f.title"
              placement="top"
            >
              <span class="progress-flag" :style="{ left: f.left + '%' }">🚩</span>
            </el-tooltip>
          </div>
        </div>
        <div class="scroll-area">
        <el-table :data="pagedTasks" v-loading="loading">
        <el-table-column prop="title" label="任务" min-width="180" />
        <el-table-column prop="assignee_name" label="被派发人" width="100" />
        <el-table-column label="状态" width="140">
          <template #default="{ row }">
            <span class="status-inline">
              <el-tag :type="statusTag(row.status).type" size="small">
                {{ statusTag(row.status).label }}
              </el-tag>
              <span v-if="row.is_milestone" class="mile-inline">| 里程碑</span>
            </span>
          </template>
        </el-table-column>
        <el-table-column label="预计完成" width="160" sortable prop="due_at">
          <template #default="{ row }">{{ row.due_at ? fmtDate(row.due_at) : '-' }}</template>
        </el-table-column>
        <el-table-column label="驳回原因" min-width="130" show-overflow-tooltip>
          <template #default="{ row }">
            <span v-if="row.status === 'rejected'" class="reject-text">{{ row.review_comment }}</span>
            <span v-else>-</span>
          </template>
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
        <el-table-column label="提交时间" width="150">
          <template #default="{ row }">{{ fmtDate(row.completed_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="viewTask(row)">查看</el-button>
            <template v-if="userStore.isAdmin || row.assigner_id === userStore.user?.id">
              <el-button
                v-if="row.status === 'completed' && !project?.archived"
                link
                type="success"
                size="small"
                @click="approveTask(row)"
              >
                确认
              </el-button>
              <el-button
                v-if="row.status === 'completed' && !project?.archived"
                link
                type="danger"
                size="small"
                @click="openReject(row)"
              >
                驳回
              </el-button>
            </template>
            <el-button
              v-if="(row.status === 'pending' || row.status === 'rejected' || row.status === 'overdue') && row.assignee_id === userStore.user?.id && !project?.archived"
              link
              type="warning"
              size="small"
              @click="completeFromList(row)"
            >
              {{ row.status === 'rejected' ? '重新提交' : '完成' }}
            </el-button>
          </template>
        </el-table-column>
        </el-table>
        <div class="pager-row">
          <el-pagination
            background
            layout="total, sizes, prev, pager, next"
            :total="taskList.length"
            :page-sizes="[5, 10, 20]"
            v-model:current-page="page"
            v-model:page-size="pageSize"
          />
        </div>
        <el-empty v-if="taskList.length === 0" description="暂无任务" :image-size="60" />
        </div>
      </el-card>

    <!-- 项目成员（模态框） -->
    <el-dialog v-model="membersVisible" title="项目成员" width="760px">
      <template #header>
        <div class="card-head">
          <span>项目成员（{{ members.length }}）</span>
          <el-button v-if="canManage && !project?.archived" link type="primary" :icon="UserFilled" @click="openMemberPicker()">
            添加成员
          </el-button>
        </div>
      </template>
      <div class="member-head" :style="memberGridStyle">
        <span>成员</span>
        <span>邮箱</span>
        <span>电话</span>
        <span v-if="canManage && !project?.archived"></span>
      </div>
      <div v-for="m in members" :key="m.user_id" class="member-row" :style="memberGridStyle">
        <div class="member-cell">
          <el-avatar :size="26">{{ (m.full_name || m.username).slice(0, 1).toUpperCase() }}</el-avatar>
          <span class="member-name">{{ m.full_name || m.username }}</span>
          <el-tag size="small" :type="roleTag(m.role)">{{ m.role_label }}</el-tag>
        </div>
        <div class="member-cell">{{ m.email || '-' }}</div>
        <div class="member-cell">{{ m.phone || '-' }}</div>
        <div v-if="canManage && !project?.archived" class="member-cell act">
          <el-button
            link
            type="danger"
            size="small"
            @click="removeMember(m)"
          >
            移除
          </el-button>
        </div>
      </div>
      <el-empty v-if="members.length === 0" description="暂无成员" :image-size="60" />
    </el-dialog>

    <!-- 派发任务 -->
    <el-dialog v-model="taskVisible" title="派发任务" width="560px">
      <el-form label-width="100px">
        <el-form-item label="被派发人" required>
          <el-select v-model="taskForm.assignee_id" placeholder="选择项目成员" style="width: 100%">
            <el-option
              v-for="m in members"
              :key="m.user_id"
              :label="`${m.username}（${m.role_label}）`"
              :value="m.user_id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="任务标题" required>
          <el-input v-model="taskForm.title" placeholder="一句话描述工作内容" maxlength="200" />
        </el-form-item>
        <el-form-item label="工作说明">
          <el-input v-model="taskForm.description" type="textarea" :rows="4" placeholder="详细要求、验收标准等（可选）" />
        </el-form-item>
        <el-form-item label="预计完成时间">
          <el-date-picker
            v-model="taskForm.due_at"
            type="datetime"
            placeholder="选择预计完成时间"
            format="YYYY-MM-DD HH:mm"
            value-format="YYYY-MM-DDTHH:mm"
            style="width: 100%"
          />
          <div class="check-tip">到期未完成将自动标记为“已超时”</div>
        </el-form-item>
        <el-form-item label="里程碑">
          <el-checkbox v-model="taskForm.is_milestone">标记为项目里程碑任务</el-checkbox>
        </el-form-item>
        <el-form-item label="附件产物">
          <el-checkbox v-model="taskForm.attachment_required">
            <span class="check-tip">指定需要反馈的附件产物（附件提交仍非硬性，未提交时必须填写留言）</span>
          </el-checkbox>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="taskVisible = false">取消</el-button>
        <el-button type="primary" :loading="creatingTask" @click="createTask">派发并通知</el-button>
      </template>
    </el-dialog>

    <!-- 添加成员 -->
    <el-dialog v-model="memberPicker" title="添加项目成员" width="460px">
      <div v-for="c in candidates" :key="c.user_id" class="candidate-row">
        <el-avatar :size="28">{{ (c.full_name || c.username).slice(0, 1).toUpperCase() }}</el-avatar>
        <span class="cand-name">{{ c.full_name || c.username }}</span>
        <el-tag size="small" :type="roleTag(c.role)">{{ c.role_label }}</el-tag>
        <el-button type="primary" size="small" @click="addMember(c)">加入项目</el-button>
      </div>
      <el-empty v-if="candidates.length === 0" description="暂无可添加人员" :image-size="60" />
    </el-dialog>

    <!-- 任务详情 -->
    <el-dialog v-model="viewVisible" title="任务详情" width="640px">
      <el-descriptions v-if="current" :column="2" border>
        <el-descriptions-item label="任务标题" :span="2">{{ current.title }}</el-descriptions-item>
        <el-descriptions-item label="被派发人">{{ current.assignee_name }}</el-descriptions-item>
        <el-descriptions-item label="派发人">{{ current.assigner_name }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="statusTag(current.status).type" size="small">
            {{ statusTag(current.status).label }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="要求附件">
          <el-tag v-if="current.attachment_required" type="warning" size="small">需要</el-tag>
          <span v-else>未指定</span>
        </el-descriptions-item>
        <el-descriptions-item label="里程碑">
          <el-tag v-if="current.is_milestone" type="warning" size="small">里程碑任务</el-tag>
          <span v-else>否</span>
        </el-descriptions-item>
        <el-descriptions-item label="预计完成时间">{{ current.due_at ? fmtDate(current.due_at) : '未设置' }}</el-descriptions-item>
        <el-descriptions-item label="派发时间">{{ fmtDate(current.created_at) }}</el-descriptions-item>
        <el-descriptions-item label="提交时间">{{ fmtDate(current.completed_at) }}</el-descriptions-item>
        <el-descriptions-item label="任务要求" :span="2">
          <div class="preserve">{{ current.description || '无' }}</div>
        </el-descriptions-item>
        <el-descriptions-item v-if="current.comment" label="完成留言" :span="2">
          <div class="preserve">{{ current.comment }}</div>
        </el-descriptions-item>
        <el-descriptions-item v-if="current.status === 'rejected'" label="驳回原因" :span="2">
          <el-alert type="error" :closable="false" :title="current.review_comment" />
        </el-descriptions-item>
        <el-descriptions-item
          v-if="current.status === 'approved' && current.review_comment"
          label="确认意见"
          :span="2"
        >
          <span class="preserve">{{ current.review_comment }}</span>
        </el-descriptions-item>
      </el-descriptions>
      <div v-if="current" class="attach-block">
        <div class="attach-title">附件产物（{{ current.attachments.length }}）</div>
        <div v-if="current.attachments.length === 0" class="attach-empty">无附件</div>
        <div v-for="a in current.attachments" :key="a.id" class="attach-item">
          <el-icon><Paperclip /></el-icon>
          <el-link type="primary" @click="download(a)">{{ a.file_name }}</el-link>
          <span class="attach-meta">（{{ fmtSize(a.file_size) }} · {{ a.uploader_name }}）</span>
        </div>
      </div>
    </el-dialog>

    <!-- 驳回任务 -->
    <el-dialog v-model="rejectVisible" title="驳回任务" width="480px">
      <div v-if="current" class="complete-task">
        任务：<b>{{ current.title }}</b>（{{ current.assignee_name }}）
      </div>
      <el-input
        v-model="rejectComment"
        type="textarea"
        :rows="4"
        maxlength="500"
        show-word-limit
        placeholder="请填写驳回原因（必填），工作人员将收到通知并重新提交"
      />
      <template #footer>
        <el-button @click="rejectVisible = false">取消</el-button>
        <el-button
          type="danger"
          :loading="reviewing"
          @click="submitReject"
        >
          确认驳回
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { DataAnalysis, Delete, Download, Lock, Paperclip, Plus, Refresh, Unlock, UserFilled } from '@element-plus/icons-vue'
import { api } from '../api'
import { useUserStore } from '../stores/user'
import { exportCSV, fmtDate, fmtSize } from '../utils/format'

const route = useRoute()
const router = useRouter()
const projectId = Number(route.params.id)
const userStore = useUserStore()

const project = ref(null)
const members = ref([])
const candidates = ref([])
const tasks = ref([])
const current = ref(null)
const loading = ref(false)
const taskScope = ref('member')
const statusFilter = ref('all')
const membersVisible = ref(false)
const page = ref(1)
const pageSize = ref(10)

const taskVisible = ref(false)
const creatingTask = ref(false)
const taskForm = reactive({
  assignee_id: null,
  title: '',
  description: '',
  attachment_required: false,
  due_at: null,
  is_milestone: false,
})

const memberPicker = ref(false)
const viewVisible = ref(false)

const rejectVisible = ref(false)
const rejectComment = ref('')
const reviewing = ref(false)

const canManage = computed(() =>
  userStore.isAdmin || project.value?.manager_id === userStore.user?.id,
)

// 成员列：有管理权（未归档时有"移除"列）为 4 列，普通成员只看 3 列
const memberGridStyle = computed(() => {
  const cols = canManage.value && !project.value?.archived ? '3fr 3fr 3fr 2fr' : '1fr 1fr 1fr'
  return { gridTemplateColumns: cols }
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

const managerRoleLabel = computed(() =>
  project.value ? `${project.value.manager_name} 负责` : '',
)

const taskList = computed(() => {
  let list =
    taskScope.value === 'mine'
      ? tasks.value.filter((t) => t.assignee_id === userStore.user?.id)
      : tasks.value
  const f = statusFilter.value
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

const pagedTasks = computed(() => {
  const start = (page.value - 1) * pageSize.value
  return taskList.value.slice(start, start + pageSize.value)
})

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

watch(statusFilter, () => (page.value = 1))

function roleTag(role) {
  const map = { admin: 'danger', pm: 'warning', dev: 'primary', tester: 'success', ops: 'info' }
  return map[role] || 'info'
}

async function load() {
  project.value = await api.projects.get(projectId)
  members.value = await api.projects.members(projectId)
  loadTasks()
}

async function loadTasks() {
  loading.value = true
  try {
    tasks.value = await api.tasks.list({ project_id: projectId, scope: 'member' })
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    loading.value = false
  }
}

/** 导出当前筛选结果的 CSV */
function exportTasks() {
  const list = taskList.value
  if (list.length === 0) {
    ElMessage.warning('当前筛选结果为空')
    return
  }
  const rows = list.map((t) => [
    t.title,
    t.assignee_name,
    STATUS_MAP[t.status]?.label || t.status,
    t.is_milestone ? '是' : '否',
    t.due_at ? fmtDate(t.due_at) : '',
    fmtDate(t.created_at),
    t.completed_at ? fmtDate(t.completed_at) : '',
    t.attachment_required ? '需要' : '',
    t.review_comment || '',
  ])
  exportCSV(
    `项目任务_${project.value?.name || projectId}_${new Date().toISOString().slice(0, 10)}.csv`,
    ['任务', '被派发人', '状态', '里程碑', '预计完成时间', '派发时间', '提交时间', '要求附件', '驳回/确认意见'],
    rows,
  )
  ElMessage.success(`已导出 ${rows.length} 条任务`)
}

async function loadCandidates() {
  try {
    candidates.value = await api.projects.candidates(projectId)
  } catch (e) {
    ElMessage.error('加载可添加人员失败：' + e.message)
    candidates.value = []
  }
}

function openMemberPicker() {
  memberPicker.value = true
  loadCandidates()
}

async function openMembers() {
  membersVisible.value = true
  try {
    members.value = await api.projects.members(projectId)
  } catch (e) {
    /* 忽略 */
  }
}

function addMember(c) {
  api.projects
    .addMember(projectId, c.user_id)
    .then(() => {
      ElMessage.success('已加入项目')
      memberPicker.value = false
      load()
    })
    .catch((e) => ElMessage.error(e.message))
}

function removeMember(m) {
  ElMessageBox.confirm(`确定将「${m.username}」移出项目？`, '确认', { type: 'warning' })
    .then(async () => {
      await api.projects.removeMember(projectId, m.user_id)
      ElMessage.success('已移出')
      load()
    })
    .catch(() => {})
}

function archiveProject() {
  ElMessageBox.confirm(
    `确定关闭项目「${project.value?.name}」？关闭后：任务不可派发、所有任务状态锁定、普通成员不可见，仅你可查看。`,
    '关闭项目',
    { type: 'warning', confirmButtonText: '确认关闭' },
  )
    .then(async () => {
      await api.projects.archive(projectId)
      ElMessage.success('项目已关闭归档')
      load()
    })
    .catch(() => {})
}

function unarchiveProject() {
  ElMessageBox.confirm(`确定恢复项目「${project.value?.name}」？`, '恢复项目', { type: 'info' })
    .then(async () => {
      await api.projects.unarchive(projectId)
      ElMessage.success('项目已恢复')
      load()
    })
    .catch(() => {})
}

function deleteProject() {
  ElMessageBox.confirm(
    `确定永久删除项目「${project.value?.name}」？其下所有任务、成员、统计记录将被一并删除，且不可恢复。`,
    '永久删除',
    { type: 'warning', confirmButtonText: '确认删除' },
  )
    .then(async () => {
      await api.projects.remove(projectId)
      ElMessage.success('项目已永久删除')
      router.push('/archived')
    })
    .catch(() => {})
}

function createTask() {
  if (!taskForm.assignee_id) {
    ElMessage.warning('请选择被派发人')
    return
  }
  if (!taskForm.title.trim()) {
    ElMessage.warning('请输入任务标题')
    return
  }
  creatingTask.value = true
  api.tasks
    .create(projectId, {
      assignee_id: taskForm.assignee_id,
      title: taskForm.title.trim(),
      description: taskForm.description,
      attachment_required: taskForm.attachment_required,
      due_at: taskForm.due_at || undefined,
      is_milestone: taskForm.is_milestone,
    })
    .then(() => {
      ElMessage.success('任务已派发并通知被派发人')
      taskVisible.value = false
      taskForm.assignee_id = null
      taskForm.title = ''
      taskForm.description = ''
      taskForm.attachment_required = false
      taskForm.due_at = null
      taskForm.is_milestone = false
      loadTasks()
    })
    .catch((e) => ElMessage.error(e.message))
    .finally(() => (creatingTask.value = false))
}

function viewTask(row) {
  current.value = row
  viewVisible.value = true
}

function updateTask(updated) {
  const idx = tasks.value.findIndex((t) => t.id === updated.id)
  if (idx >= 0) tasks.value[idx] = updated
}

async function approveTask(row) {
  try {
    await ElMessageBox.confirm(
      `确认「${row.assignee_name}」提交的任务《${row.title}》完成？确认后任务结束。`,
      '确认任务完成',
      { type: 'success' },
    )
  } catch (e) {
    return
  }
  try {
    const updated = await api.tasks.approve(row.id)
    ElMessage.success('已确认，任务结束')
    updateTask(updated)
  } catch (e) {
    ElMessage.error(e.message)
  }
}

function openReject(row) {
  current.value = row
  rejectComment.value = ''
  rejectVisible.value = true
}

async function submitReject() {
  if (!rejectComment.value.trim()) {
    ElMessage.warning('请填写驳回原因')
    return
  }
  reviewing.value = true
  try {
    const updated = await api.tasks.reject(current.value.id, rejectComment.value.trim())
    ElMessage.success('已驳回，工作人员将收到通知')
    rejectVisible.value = false
    updateTask(updated)
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    reviewing.value = false
  }
}

function completeFromList(row) {
  if (!userStore.isAdmin && row.assignee_id !== userStore.user?.id) return
  ElMessageBox.confirm(
    `请到「我的任务」中对《${row.title}》提交留言与附件${row.status === 'rejected' ? '（任务已被驳回，请注意查阅驳回原因）' : ''}。`,
    row.status === 'rejected' ? '重新提交任务' : '完成任务',
    { type: 'info' },
  )
    .then(() => router.push('/tasks'))
    .catch(() => {})
}

function download(a) {
  api.tasks.download(a.id, a.file_name).catch((e) => ElMessage.error(e.message))
}

onMounted(load)
</script>

<style scoped>
.page > :deep(.el-page-header) {
  flex: none;
}
.card-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.task-ops {
  display: flex;
  align-items: center;
  gap: 10px;
}
.reject-text {
  color: #f56c6c;
}
.status-inline {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  white-space: nowrap;
}
.mile-inline {
  color: #f59e0b;
  font-weight: 600;
  font-size: 12px;
}
.progress-block {
  margin-bottom: 14px;
  padding: 12px 14px;
  background: #f8faff;
  border: 1px solid rgba(79, 110, 247, 0.12);
  border-radius: 10px;
}
.progress-label {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 13px;
  color: var(--app-text-sub);
  margin-bottom: 8px;
}
.progress-label b {
  color: #2b5be8;
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
  background: linear-gradient(90deg, #6ea8fe, #38bdf8);
}
.progress-flag {
  position: absolute;
  top: -14px;
  transform: translateX(-50%);
  font-size: 18px;
  cursor: pointer;
  line-height: 1;
}
.pager-row {
  display: flex;
  justify-content: flex-end;
  margin-top: 12px;
}
.scroll-area {
  flex: 1;
  min-height: 0;
  overflow: auto;
}
.btn-members {
  background: linear-gradient(135deg, #2b5be8, #1e40af);
  border-color: transparent;
  box-shadow: 0 4px 12px rgba(43, 91, 232, 0.3);
}
.btn-members:hover {
  background: linear-gradient(135deg, #1e3a8a, #1e40af);
  border-color: transparent;
}
.member-head,
.member-row {
  display: grid;
  grid-template-columns: 3fr 3fr 3fr 2fr;
  align-items: center;
  gap: 12px;
}
.member-head {
  padding: 8px 0;
  color: #909399;
  font-size: 12px;
  border-bottom: 1px solid #f0f2f5;
}
.member-row {
  padding: 10px 0;
  border-bottom: 1px solid #f5f5f5;
}
.member-cell {
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 8px;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
  color: #333;
  font-size: 13px;
}
.member-name {
  font-weight: 600;
}
.member-cell.act {
  justify-content: flex-end;
}
.member-info {
  display: none;
}
.desc {
  color: #606266;
  white-space: pre-wrap;
}
.meta {
  color: #909399;
  font-size: 13px;
  margin-top: 8px;
}
.check-tip {
  color: #909399;
  font-size: 12px;
}
.candidate-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 0;
  border-bottom: 1px solid #f5f5f5;
}
.cand-name {
  flex: 1;
  font-weight: 600;
}
.preserve {
  white-space: pre-wrap;
  word-break: break-all;
}
.attach-block {
  margin-top: 16px;
}
.attach-title {
  font-weight: 600;
  margin-bottom: 8px;
}
.attach-empty {
  color: #909399;
}
.attach-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 0;
}
.attach-meta {
  color: #909399;
  font-size: 12px;
}
</style>