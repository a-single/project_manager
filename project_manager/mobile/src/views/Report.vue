<template>
  <div class="page">
    <div class="card filter-card">
      <div class="field">
        <label>起止日期</label>
        <div style="display: flex; gap: 8px">
          <input v-model="startDate" type="date" class="input" style="flex: 1" />
          <input v-model="endDate" type="date" class="input" style="flex: 1" />
        </div>
      </div>
      <button class="btn btn-primary btn-block" :disabled="loading" @click="query">
        {{ loading ? '查询中…' : '查 询' }}
      </button>
    </div>

    <template v-if="records.length > 0">
      <div class="card" style="padding: 12px">
        <div class="muted" style="margin-bottom: 8px">
          {{ startDate }} ~ {{ endDate }} · 完成任务 {{ records.length }} 项<br />
          总耗时 {{ totalDuration }}
        </div>
        <div style="display: flex; gap: 8px">
          <button class="btn btn-outline" style="flex: 1; font-size: 13px; padding: 8px" @click="copyText">
            📋 复制日报文本
          </button>
          <button class="btn btn-primary" style="flex: 1; font-size: 13px; padding: 8px" @click="downloadCsv">
            ⬇ 导出 CSV
          </button>
        </div>
      </div>

      <div class="card" style="padding: 4px 14px">
        <div v-for="(r, i) in records" :key="i" class="rep-row">
          <div class="rep-main">
            <div class="ellipsis">{{ r.title }}</div>
            <div class="muted ellipsis">{{ r.project_name }} · 完成于 {{ fmtDate(r.completed_at) }}</div>
          </div>
          <span class="tag tag-success">{{ fmtDuration(durationOf(r)) }}</span>
        </div>
      </div>
    </template>

    <div v-else-if="!loading" class="card empty" style="padding: 28px 0">
      <div class="empty-icon">📄</div>该时间段内暂无任务记录
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { api } from '../api'
import { fmtDate, fmtDuration } from '../utils/format'

const startDate = ref('')
const endDate = ref('')
const records = ref([])
const loading = ref(false)

const totalDuration = computed(() =>
  fmtDuration(records.value.reduce((s, r) => s + durationOf(r), 0)),
)

function durationOf(r) {
  if (r.duration_minutes != null) return r.duration_minutes
  if (!r.completed_at || !r.created_at) return 0
  return Math.max(1, Math.round((new Date(r.completed_at) - new Date(r.created_at)) / 60000))
}

function toYMD(d) {
  const p = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`
}

function defaultRange() {
  const end = new Date()
  const start = new Date()
  start.setDate(start.getDate() - 29)
  startDate.value = toYMD(start)
  endDate.value = toYMD(end)
}

async function query() {
  if (!startDate.value || !endDate.value) {
    alert('请选择起止日期')
    return
  }
  loading.value = true
  try {
    records.value = await api.report.mine({
      start: startDate.value,
      end: endDate.value,
    })
  } catch (e) {
    alert(e.message)
  } finally {
    loading.value = false
  }
}

function buildText() {
  const lines = []
  lines.push(`工作报告（${startDate.value} ~ ${endDate.value}）`)
  const total = records.value.reduce((s, r) => s + durationOf(r), 0)
  lines.push(`完成工作任务共 ${records.value.length} 项，总耗时 ${fmtDuration(total)}`)
  records.value.forEach((r, i) => {
    lines.push(`${i + 1}. 【${r.project_name}】${r.title}（完成于 ${fmtDate(r.completed_at)}，耗时 ${fmtDuration(durationOf(r))}）`)
  })
  return lines.join('\n')
}

async function copyText() {
  try {
    await navigator.clipboard.writeText(buildText())
    alert('日报文本已复制到剪贴板')
  } catch {
    const ta = document.createElement('textarea')
    ta.value = buildText()
    document.body.appendChild(ta)
    ta.select()
    document.execCommand('copy')
    document.body.removeChild(ta)
    alert('日报文本已复制到剪贴板')
  }
}

async function downloadCsv() {
  const head = '序号,项目,任务,完成时间,耗时(分钟)'
  const rows = records.value.map((r, i) => `${i + 1},${r.project_name},${JSON.stringify(r.title)},${fmtDate(r.completed_at)},${durationOf(r)}`)
  const content = '\uFEFF' + [head, ...rows].join('\n')
  const blob = new Blob([content], { type: 'text/csv;charset=utf-8' })
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob)
  a.download = `日报_${startDate.value}_${endDate.value}.csv`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  setTimeout(() => URL.revokeObjectURL(a.href), 3000)
  alert('已开始导出；若无效，可使用「复制日报文本」代替')
}

onMounted(defaultRange)
</script>

<style scoped>
.rep-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 10px 0;
  border-bottom: 1px solid var(--line);
}
.rep-row:last-child {
  border-bottom: none;
}
.rep-main {
  min-width: 0;
}
</style>