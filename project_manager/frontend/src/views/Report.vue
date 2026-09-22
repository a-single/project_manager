<template>
  <el-card shadow="never" class="page page-card">
    <template #header>
      <div class="card-head">
        <span>我的任务记录（用于日报 / 周报）</span>
        <div class="filter-bar">
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            value-format="YYYY-MM-DD"
            :disabled-date="(d) => d > new Date()"
          />
          <el-button type="primary" :icon="Search" :loading="loading" @click="query">查询</el-button>
          <el-button type="success" :icon="Download" :disabled="records.length === 0" @click="exportCsv">
            导出 CSV
          </el-button>
        </div>
      </div>
    </template>

    <div class="scroll-area">
    <div class="tip">
      记录范围：派发时间或完成时间落在所选时间段内的任务，可直接导出用作日报/周报（CSV 可用 Excel 打开）。
    </div>

    <el-table :data="records" v-loading="loading">
      <el-table-column prop="title" label="任务" min-width="180" />
      <el-table-column prop="project_name" label="所属项目" width="140" />
      <el-table-column label="状态" width="90">
        <template #default="{ row }">
          <el-tag :type="row.status === 'completed' ? 'success' : 'primary'" size="small">
            {{ row.status === 'completed' ? '已完成' : '待处理' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="派发时间" width="155">
        <template #default="{ row }">{{ fmtDate(row.created_at) }}</template>
      </el-table-column>
      <el-table-column label="完成时间" width="155">
        <template #default="{ row }">{{ fmtDate(row.completed_at) }}</template>
      </el-table-column>
      <el-table-column label="耗时" width="120">
        <template #default="{ row }">{{ fmtDuration(row.duration_minutes) }}</template>
      </el-table-column>
      <el-table-column prop="comment" label="完成留言" min-width="160" show-overflow-tooltip />
    </el-table>
    <el-empty v-if="records.length === 0" description="该时间段内暂无任务记录" />
    </div>
  </el-card>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Download, Search } from '@element-plus/icons-vue'
import { api } from '../api'
import { exportCSV, fmtDate, fmtDuration } from '../utils/format'

const dateRange = ref([])
const records = ref([])
const loading = ref(false)

function defaultRange() {
  const end = new Date()
  const start = new Date()
  if (end.getDay() === 1) {
    start.setDate(end.getDate() - 6)
  } else {
    start.setDate(end.getDate() - end.getDay() + 1)
  }
  const f = (d) => {
    const p = (n) => String(n).padStart(2, '0')
    return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`
  }
  dateRange.value = [f(start), f(end)]
}

async function query() {
  if (!dateRange.value || dateRange.value.length !== 2) {
    ElMessage.warning('请选择时间段')
    return
  }
  loading.value = true
  try {
    records.value = await api.report.mine({
      start: dateRange.value[0],
      end: dateRange.value[1],
    })
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    loading.value = false
  }
}

function exportCsv() {
  const [start, end] = dateRange.value
  exportCSV(
    `任务记录_${start}_${end}.csv`,
    ['任务', '所属项目', '状态', '派发时间', '完成时间', '耗时', '完成留言'],
    records.value.map((r) => [
      r.title,
      r.project_name,
      r.status === 'completed' ? '已完成' : '待处理',
      fmtDate(r.created_at),
      fmtDate(r.completed_at),
      fmtDuration(r.duration_minutes),
      r.comment,
    ]),
  )
  ElMessage.success('已导出')
}

onMounted(async () => {
  defaultRange()
  await query()
})
</script>

<style scoped>
.card-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}
.filter-bar {
  display: flex;
  gap: 12px;
  align-items: center;
  flex-wrap: wrap;
}
.tip {
  margin-bottom: 12px;
  color: #909399;
  font-size: 13px;
}
</style>