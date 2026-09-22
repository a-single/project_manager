<template>
  <div v-if="task" class="task-sheet">
    <div class="sheet-title">
      <span>任务详情</span>
      <button class="btn btn-ghost" style="padding: 4px 10px; font-size: 12px" @click="$emit('close')">关闭</button>
    </div>

    <div class="ts-head">
      <span class="tag" :class="statusCls">{{ statusLabel }}</span>
      <span v-if="task.is_milestone" class="tag tag-ms">里程碑</span>
      <h3 style="margin-top: 8px; font-size: 16px">{{ task.title }}</h3>
    </div>

    <div class="ts-info">
      <div class="ts-row"><span class="muted">所属项目</span><span>{{ task.project_name }}</span></div>
      <div class="ts-row"><span class="muted">派发人</span><span>{{ task.assigner_name }}</span></div>
      <div class="ts-row"><span class="muted">被派发人</span><span>{{ task.assignee_name }}</span></div>
      <div class="ts-row"><span class="muted">派发时间</span><span>{{ fmtDate(task.created_at) }}</span></div>
      <div class="ts-row"><span class="muted">预计完成</span><span>{{ task.due_at ? fmtDate(task.due_at) : '未设置' }}</span></div>
      <div class="ts-row" v-if="task.completed_at"><span class="muted">提交时间</span><span>{{ fmtDate(task.completed_at) }}</span></div>
      <div class="ts-row"><span class="muted">附件产物</span><span>{{ task.attachment_required ? '需要' : '未指定' }}</span></div>
    </div>

    <div class="ts-section">
      <div class="muted" style="margin-bottom: 6px">任务要求</div>
      <p style="white-space: pre-wrap; line-height: 1.6">{{ task.description || '无' }}</p>
    </div>

    <div v-if="task.status === 'rejected'" class="ts-alert danger">
      <b>已驳回，原因：</b>{{ task.review_comment }}
    </div>
    <div v-else-if="task.status === 'approved' && task.review_comment" class="ts-alert success">
      <b>确认意见：</b>{{ task.review_comment }}
    </div>
    <div v-else-if="task.status === 'completed'" class="ts-alert warning">已提交，等待项目经理确认</div>

    <div v-if="task.comment" class="ts-section">
      <div class="muted" style="margin-bottom: 6px">完成留言</div>
      <p style="white-space: pre-wrap; line-height: 1.6">{{ task.comment }}</p>
    </div>

    <div class="ts-section">
      <div class="muted" style="margin-bottom: 6px">附件（{{ task.attachments.length }}）</div>
      <div v-if="task.attachments.length === 0" class="muted">无附件</div>
      <div v-for="a in task.attachments" :key="a.id" class="ts-attach" @click="download(a)">
        📎 {{ a.file_name }}
        <span class="muted">（{{ fmtSize(a.file_size) }}）</span>
      </div>
    </div>

    <div v-if="archived" class="ts-alert warning">
      项目已归档，所有任务状态已锁定，仅可查看
    </div>

    <!-- 操作区 -->
    <div class="ts-actions" v-if="!archived">
      <!-- 工作人员：完成 / 重新提交 -->
      <template v-if="isAssignee && (task.status === 'pending' || task.status === 'rejected' || task.status === 'overdue')">
        <div v-if="task.status === 'rejected'" class="ts-alert danger" style="margin-bottom: 10px">
          已被驳回，请按驳回原因重新提交
        </div>
        <div v-else-if="task.is_overdue" class="ts-alert warning" style="margin-bottom: 10px">
          该任务已超过预计完成时间，提交后项目经理确认将标记为「已延毕」
        </div>
        <div class="field">
          <label>留言说明{{ needComment ? '（未提交附件时必填）' : '' }}</label>
          <textarea v-model="comment" class="textarea" :placeholder="task.attachment_required ? '请说明工作完成情况' : '未提交附件时留言为必填'"></textarea>
        </div>
        <div class="field">
          <label>提交附件（非必须，可多选）</label>
          <label class="file-btn">
            <input type="file" multiple style="display: none" @change="onFiles" />
            📁 选择文件（已选 {{ files.length }} 个）
          </label>
          <div v-for="(f, i) in files" :key="i" class="file-list">
            {{ f.name }} <span class="muted">{{ fmtSize(f.size) }}</span>
          </div>
        </div>
        <div class="act-row">
          <button class="btn btn-danger-outline" @click="$emit('close')">取消</button>
          <button class="btn btn-primary" :disabled="submitting" @click="submitComplete">
            {{ submitting ? '提交中…' : task.status === 'rejected' ? '确认重新提交' : '完成任务' }}
          </button>
        </div>
      </template>

      <!-- 项目经理：确认 / 驳回 -->
      <template v-else-if="isReviewer && task.status === 'completed'">
        <div class="ts-alert warning" style="margin-bottom: 10px">工作人员已提交，请审核该任务</div>
        <div class="act-row">
          <button class="btn btn-danger-outline" @click="rejectMode = !rejectMode">驳回</button>
          <button class="btn btn-primary" :disabled="reviewing" @click="doApprove">
            {{ reviewing ? '处理中…' : '确认完成' }}
          </button>
        </div>
        <div v-if="rejectMode" style="margin-top: 12px">
          <textarea v-model="rejectComment" class="textarea" placeholder="请填写驳回原因（必填）" style="margin-bottom: 10px"></textarea>
          <button class="btn btn-danger btn-block" :disabled="reviewing" @click="doReject">
            {{ reviewing ? '处理中…' : '确认驳回' }}
          </button>
        </div>
      </template>

      <template v-else>
        <div class="muted" style="text-align: center; padding: 6px 0">当前状态下无需操作</div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { api } from '../api'
import { useUserStore } from '../stores/user'
import { fmtDate, fmtSize } from '../utils/format'

const props = defineProps({
  task: { type: Object, required: true },
  archived: { type: Boolean, default: false },
})
const emit = defineEmits(['close', 'saved'])
const userStore = useUserStore()

const comment = ref('')
const files = ref([])
const submitting = ref(false)
const reviewMode = ref(false)
const rejectMode = ref(false)
const rejectComment = ref('')
const reviewing = ref(false)

const STATUS = {
  pending: { label: '待处理', cls: 'tag-primary' },
  completed: { label: '待确认', cls: 'tag-warning' },
  approved: { label: '已确认', cls: 'tag-success' },
  rejected: { label: '已驳回', cls: 'tag-danger' },
  overdue: { label: '已超时', cls: 'tag-danger' },
  late: { label: '已延毕', cls: 'tag-warning' },
}

// 超时/延毕为实时计算展示态：先按 is_overdue，再按 is_late
const statusLabel = computed(() => {
  if (props.task.is_overdue) return '已超时'
  if (props.task.is_late) return '已延毕'
  return STATUS[props.task.status]?.label || props.task.status
})
const statusCls = computed(() => {
  if (props.task.is_overdue) return 'tag-danger'
  if (props.task.is_late) return 'tag-warning'
  return STATUS[props.task.status]?.cls || 'tag'
})

const archived = computed(() => props.archived)
const isAssignee = computed(() => props.task.assignee_id === userStore.user?.id)
const isReviewer = computed(() =>
  userStore.isAdmin || props.task.assigner_id === userStore.user?.id,
)
const needComment = computed(() => files.value.length === 0)

function onFiles(e) {
  files.value = Array.from(e.target.files || [])
}

function download(a) {
  window.location.href = api.tasks.attachmentUrl(a.id)
}

async function submitComplete() {
  if (files.value.length === 0 && !comment.value.trim()) {
    alert('未提交附件时，留言说明为必填')
    return
  }
  submitting.value = true
  try {
    const fd = new FormData()
    fd.append('comment', comment.value.trim())
    files.value.forEach((f) => fd.append('files', f))
    const updated = await api.tasks.complete(props.task.id, fd)
    emit('saved', updated)
  } catch (e) {
    alert(e.message)
  } finally {
    submitting.value = false
  }
}

async function doApprove() {
  reviewing.value = true
  try {
    const updated = await api.tasks.approve(props.task.id)
    emit('saved', updated)
  } catch (e) {
    alert(e.message)
  } finally {
    reviewing.value = false
  }
}

async function doReject() {
  if (!rejectComment.value.trim()) {
    alert('请填写驳回原因')
    return
  }
  reviewing.value = true
  try {
    const updated = await api.tasks.reject(props.task.id, rejectComment.value.trim())
    emit('saved', updated)
  } catch (e) {
    alert(e.message)
  } finally {
    reviewing.value = false
  }
}
</script>

<style scoped>
.ts-head {
  margin-bottom: 12px;
}
.ts-info {
  background: #f7f8fc;
  border-radius: 10px;
  padding: 10px 12px;
  font-size: 13px;
}
.ts-row {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  padding: 3px 0;
}
.ts-section {
  margin-top: 14px;
}
.ts-alert {
  margin-top: 12px;
  border-radius: 10px;
  padding: 10px 12px;
  font-size: 13px;
  line-height: 1.5;
}
.ts-alert.danger {
  background: rgba(245, 108, 108, 0.1);
  color: #dc2626;
}
.ts-alert.success {
  background: rgba(34, 197, 94, 0.1);
  color: #15803d;
}
.ts-alert.warning {
  background: rgba(245, 158, 11, 0.1);
  color: #b45309;
}
.ts-attach {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 10px;
  background: #f6f8ff;
  border-radius: 8px;
  margin-bottom: 6px;
  font-size: 13px;
  color: var(--primary);
}
.tag-ms {
  background: rgba(245, 158, 11, 0.12);
  color: #b45309;
  margin-left: 6px;
}
.ts-actions {
  margin-top: 16px;
  border-top: 1px dashed var(--line);
  padding-top: 14px;
}
.act-row {
  display: flex;
  gap: 10px;
}
.act-row .btn {
  flex: 1;
}
.file-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 22px 10px;
  border: 1.5px dashed rgba(110, 168, 254, 0.4);
  border-radius: 12px;
  background: #f6f8ff;
  color: var(--primary);
  font-size: 14px;
  cursor: pointer;
}
.file-list {
  display: flex;
  justify-content: space-between;
  padding: 6px 2px;
  font-size: 13px;
}
</style>