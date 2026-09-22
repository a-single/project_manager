<template>
  <el-card shadow="never" class="page page-card">
    <template #header>
    <div class="toolbar">
      <el-radio-group v-model="statusTab" @change="load">
        <el-radio-button value="all">全部</el-radio-button>
        <el-radio-button value="pending">待处理</el-radio-button>
        <el-radio-button value="overdue">已超时</el-radio-button>
        <el-radio-button value="rejected">已驳回</el-radio-button>
        <el-radio-button value="completed">待确认</el-radio-button>
        <el-radio-button value="approved">已确认</el-radio-button>
        <el-radio-button value="late">已延毕</el-radio-button>
      </el-radio-group>
      <el-button type="primary" :icon="Refresh" circle @click="load" />
    </div>
    </template>

    <div class="scroll-area">
    <el-table :data="filteredTasks" v-loading="loading" @row-click="rowView">
      <el-table-column prop="title" label="任务标题" min-width="180" />
      <el-table-column prop="project_name" label="所属项目" width="130" />
      <el-table-column label="要求附件" width="95">
        <template #default="{ row }">
          <el-tag v-if="row.attachment_required" type="warning" size="small">需要</el-tag>
          <span v-else>-</span>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="95">
        <template #default="{ row }">
          <el-tag :type="statusTag(row.status).type" size="small">
            {{ statusTag(row.status).label }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="驳回原因" min-width="140" show-overflow-tooltip>
        <template #default="{ row }">
          <span v-if="row.status === 'rejected'" class="reject-text">{{ row.review_comment }}</span>
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
          <el-button link type="primary" size="small" @click.stop="rowView(row)">查看</el-button>
          <el-button
            v-if="row.status === 'pending' || row.status === 'rejected' || row.status === 'overdue'"
            link
            :type="row.status === 'rejected' ? 'warning' : 'success'"
            size="small"
            @click.stop="openComplete(row)"
          >
            {{ row.status === 'rejected' ? '重新提交' : '完成工作' }}
          </el-button>
          <span v-else-if="row.status === 'completed'" class="wait-tip">待项目经理确认</span>
        </template>
      </el-table-column>
    </el-table>
    </div>

    <!-- 任务详情 -->
    <el-dialog v-model="viewVisible" title="任务详情" width="680px">
      <el-descriptions v-if="current" :column="2" border>
        <el-descriptions-item label="任务标题" :span="2">{{ current.title }}</el-descriptions-item>
        <el-descriptions-item label="所属项目">{{ current.project_name }}</el-descriptions-item>
        <el-descriptions-item label="派发人">{{ current.assigner_name }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="statusTag(current.status).type" size="small">{{ statusTag(current.status).label }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="要求附件">
          <el-tag v-if="current.attachment_required" type="warning" size="small">需要反馈附件产物</el-tag>
          <span v-else>未指定</span>
        </el-descriptions-item>
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
          v-if="current.status === 'approved' || current.status === 'late'"
          label="确认意见" :span="2"
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
          <span class="attach-meta">（{{ fmtSize(a.file_size) }} · {{ a.uploader_name }} · {{ fmtDate(a.uploaded_at) }}）</span>
        </div>
      </div>
    </el-dialog>

    <!-- 完成 / 重新提交 -->
    <el-dialog v-model="completeVisible" :title="completeTitle" width="560px">
      <div v-if="current" class="complete-task">
        任务：<b>{{ current.title }}</b>
        <el-tag v-if="current.attachment_required" type="warning" size="small" style="margin-left: 8px">
          需要反馈附件产物
        </el-tag>
        <el-alert
          v-if="current.status === 'rejected'"
          type="error"
          :closable="false"
          show-icon
          title="此任务曾被驳回，请根据驳回原因重新提交"
          style="margin-top: 10px"
        >
          <template #default>{{ current.review_comment }}</template>
        </el-alert>
      </div>
      <el-form label-position="top">
        <el-form-item label="提交附件（非必须，可多选）">
          <el-upload
            v-model:file-list="fileList"
            multiple
            drag
            :auto-upload="false"
            :limit="10"
          >
            <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
            <div class="el-upload__text">拖拽文件到此处，或点击选择</div>
          </el-upload>
        </el-form-item>
        <el-form-item label="留言说明">
          <el-input
            v-model="comment"
            type="textarea"
            :rows="4"
            :placeholder="fileList.length === 0 ? '未提交附件时，留言说明为必填' : '可填写工作说明（选填）'"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="completeVisible = false">取消</el-button>
        <el-button type="success" :loading="submitting" @click="submitComplete">
          {{ current?.status === 'rejected' ? '确认重新提交' : '确认完成' }}
        </el-button>
      </template>
    </el-dialog>
  </el-card>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Refresh, Paperclip, UploadFilled } from '@element-plus/icons-vue'
import { api } from '../api'
import { fmtDate, fmtSize } from '../utils/format'

const route = useRoute()
const loading = ref(false)
const statusTab = ref('all')
const tasks = ref([])

const current = ref(null)
const viewVisible = ref(false)
const completeVisible = ref(false)
const fileList = ref([])
const comment = ref('')
const submitting = ref(false)

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

const completeTitle = computed(() =>
  current.value?.status === 'rejected' ? '重新提交任务' : '完成工作',
)

const filteredTasks = computed(() => {
  if (statusTab.value === 'all') return tasks.value
  return tasks.value.filter((t) => t.status === statusTab.value)
})

async function load() {
  loading.value = true
  try {
    tasks.value = await api.tasks.list({ scope: 'mine' })
    const focus = route.query.focus
    if (focus) {
      const target = tasks.value.find((t) => t.id === Number(focus))
      if (target) rowView(target)
    }
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    loading.value = false
  }
}

function rowView(row) {
  current.value = row
  viewVisible.value = true
}

function openComplete(row) {
  current.value = row
  fileList.value = []
  comment.value = ''
  completeVisible.value = true
}

async function submitComplete() {
  if (fileList.value.length === 0 && !comment.value.trim()) {
    ElMessage.warning('未提交附件时，留言说明为必填')
    return
  }
  submitting.value = true
  try {
    const fd = new FormData()
    fd.append('comment', comment.value.trim())
    fileList.value.forEach((f) => {
      if (f.raw) fd.append('files', f.raw)
    })
    const updated = await api.tasks.complete(current.value.id, fd)
    ElMessage.success(
      current.value.status === 'rejected'
        ? '已重新提交，等待项目经理确认'
        : '任务已提交，等待项目经理确认',
    )
    completeVisible.value = false
    const idx = tasks.value.findIndex((t) => t.id === updated.id)
    if (idx >= 0) tasks.value[idx] = updated
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    submitting.value = false
  }
}

async function download(a) {
  try {
    await api.tasks.download(a.id, a.file_name)
  } catch (e) {
    ElMessage.error(e.message)
  }
}

onMounted(load)
</script>

<style scoped>
.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.preserve {
  white-space: pre-wrap;
  word-break: break-all;
}
.reject-text {
  color: #f56c6c;
}
.wait-tip {
  color: #909399;
  font-size: 12px;
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
.complete-task {
  margin-bottom: 12px;
  padding: 10px;
  background: #f5f7fa;
  border-radius: 4px;
}
</style>