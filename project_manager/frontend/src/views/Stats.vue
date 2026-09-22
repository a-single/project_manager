<template>
  <div class="page">
    <el-page-header @back="$router.back()">
      <template #content>
        <span style="font-weight: 600">任务统计 - {{ project?.name || '项目' }}</span>
      </template>
    </el-page-header>

    <el-card shadow="never" style="margin-top: 16px; flex: none">
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
        <el-select v-model="userId" placeholder="全部人员" clearable style="width: 200px">
          <el-option v-for="m in members" :key="m.user_id" :label="m.username" :value="m.user_id" />
        </el-select>
        <el-button type="primary" :icon="Search" :loading="loading" @click="query">查询</el-button>
      </div>
      <div class="tip">
        统计口径：在所选时间段内<b>完成</b>的任务（按完成时间落在时间段内计），耗时为完成时间与派发时间之差。
      </div>
    </el-card>

    <div class="scroll-area">
    <el-row :gutter="16" style="margin-top: 16px">
      <el-col :span="24">
        <el-card shadow="never">
          <template #header><span>甘特图：任务完成时间轴</span></template>
          <div ref="ganttRef" class="chart gantt-chart"></div>
          <el-empty v-if="records.length === 0" description="该时间段内暂无完成的任务" />
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16" style="margin-top: 16px">
      <el-col :span="24">
        <el-card shadow="never">
          <template #header><span>条形图：各人员完成数量</span></template>
          <div ref="countRef" class="chart bar-chart"></div>
          <el-empty v-if="records.length === 0" description="暂无数据" />
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16" style="margin-top: 16px">
      <el-col :span="24">
        <el-card shadow="never">
          <template #header><span>条形图：人员工作时长（小时）</span></template>
          <div ref="durationRef" class="chart bar-chart"></div>
          <el-empty v-if="records.length === 0" description="暂无数据" />
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16" style="margin-top: 16px">
      <el-col :span="24">
        <el-card shadow="never">
          <template #header><span>条形图：人员超时任务数量</span></template>
          <div ref="overdueRef" class="chart bar-chart"></div>
          <el-empty v-if="overdueData.length === 0" description="暂无超时任务" />
        </el-card>
      </el-col>
    </el-row>
    </div>
  </div>
</template>

<script setup>
import { nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import * as echarts from 'echarts'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Search } from '@element-plus/icons-vue'
import { api } from '../api'
import { fmtDate, fmtDuration } from '../utils/format'

const route = useRoute()
const projectId = Number(route.params.id)

const project = ref(null)
const members = ref([])
const dateRange = ref([])
const userId = ref(null)
const records = ref([])
const loading = ref(false)

const ganttRef = ref()
const countRef = ref()
const durationRef = ref()
const overdueRef = ref()
let ganttChart = null
let countChart = null
let durationChart = null
let overdueChart = null

const overdueData = ref([])

async function loadMeta() {
  project.value = await api.projects.get(projectId)
  members.value = await api.projects.members(projectId)
}

function defaultRange() {
  const end = new Date()
  const start = new Date()
  start.setDate(start.getDate() - 29)
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
    records.value = await api.stats.tasks({
      project_id: projectId,
      start: dateRange.value[0],
      end: dateRange.value[1],
      ...(userId.value ? { user_id: userId.value } : {}),
    })
    overdueData.value = await api.stats.overdueCounts(projectId)
    await nextTick()
    drawAll()
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    loading.value = false
  }
}

function drawAll() {
  drawGantt()
  drawCount()
  drawDuration()
  drawOverdue()
}

function drawGantt() {
  if (!ganttRef.value) return
  ganttChart = ganttChart || echarts.init(ganttRef.value)
  const names = [...new Set(records.value.map((r) => r.assignee_name))]
  const nameIndex = new Map(names.map((n, i) => [n, i]))
  const data = records.value.map((r, i) => [
    nameIndex.get(r.assignee_name),
    r.created_at.getTime ? r.created_at : new Date(r.created_at),
    new Date(r.completed_at),
    i,
  ])
  const dataItems = data.map((d) => ({
    value: d,
    itemStyle: { color: '#6ea8fe' },
    emphasis: { itemStyle: { color: '#66b1ff' } },
  }))
  ganttChart.setOption(
    {
      tooltip: {
        formatter: (params) => {
          const [, catIdx, , , ] = params.data.value
          const [, start, end, i] = params.data.value
          const r = records.value[i]
          return `${r.assignee_name}<br/><b>${r.title}</b><br/>派发：${fmtDate(start)}<br/>完成：${fmtDate(end)}<br/>耗时：${fmtDuration(r.duration_minutes)}`
        },
      },
      grid: { left: 80, right: 40, top: 20, bottom: 60 },
      xAxis: { type: 'time' },
      yAxis: {
        type: 'category',
        data: names,
        inverse: true,
      },
      dataZoom: [{ type: 'slider', bottom: 10 }],
      series: [
        {
          type: 'custom',
          renderItem: (params, api) => {
            const catIndex = api.value(0)
            const start = api.coord([api.value(1), catIndex])
            const end = api.coord([api.value(2), catIndex])
            const height = Math.max(api.size([0, 1])[1] * 0.5, 6)
            const rect = {
              x: start[0],
              y: start[1] - height / 2,
              width: Math.max(end[0] - start[0], 2),
              height,
            }
            const clip = echarts.graphic.clipRectByRect(rect, {
              x: params.coordSys.x,
              y: params.coordSys.y,
              width: params.coordSys.width,
              height: params.coordSys.height,
            })
            return {
              type: 'rect',
              shape: clip,
              style: api.style(),
            }
          },
          encode: { x: [1, 2], y: 0 },
          data: dataItems,
        },
      ],
    },
    true,
  )
}

function drawCount() {
  if (!countRef.value) return
  countChart = countChart || echarts.init(countRef.value)
  const agg = {}
  records.value.forEach((r) => {
    agg[r.assignee_name] = (agg[r.assignee_name] || 0) + 1
  })
  const names = Object.keys(agg)
  countChart.setOption(
    {
      tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
      grid: { left: 60, right: 20, top: 20, bottom: 30 },
      xAxis: { type: 'category', data: names },
      yAxis: { type: 'value', minInterval: 1 },
      series: [
        {
          type: 'bar',
          data: names.map((n) => agg[n]),
          label: { show: true, position: 'top' },
          itemStyle: { color: '#6ea8fe', borderRadius: [3, 3, 0, 0] },
          barMaxWidth: 40,
        },
      ],
    },
    true,
  )
}

function drawDuration() {
  if (!durationRef.value) return
  durationChart = durationChart || echarts.init(durationRef.value)
  const agg = {}
  records.value.forEach((r) => {
    agg[r.assignee_name] = (agg[r.assignee_name] || 0) + (r.duration_minutes || 0) / 60
  })
  const names = Object.keys(agg)
  durationChart.setOption(
    {
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'shadow' },
        formatter: (params) => {
          const p = params[0]
          return `${p.name}<br/>总耗时：${p.value.toFixed(1)} 小时`
        },
      },
      grid: { left: 60, right: 20, top: 20, bottom: 30 },
      xAxis: { type: 'category', data: names },
      yAxis: { type: 'value' },
      series: [
        {
          type: 'bar',
          data: names.map((n) => Number(agg[n].toFixed(1))),
          label: { show: true, position: 'top', formatter: '{c}' },
          itemStyle: { color: '#67c23a', borderRadius: [3, 3, 0, 0] },
          barMaxWidth: 40,
        },
      ],
    },
    true,
  )
}

function drawOverdue() {
  if (!overdueRef.value) return
  overdueChart = overdueChart || echarts.init(overdueRef.value)
  const data = overdueData.value.map((d) => d.count)
  const names = overdueData.value.map((d) => d.assignee_name)
  overdueChart.setOption(
    {
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'shadow' },
        formatter: (params) => {
          const p = params[0]
          return `${p.name}<br/>超时任务：${p.value} 个`
        },
      },
      grid: { left: 60, right: 20, top: 20, bottom: 30 },
      xAxis: { type: 'category', data: names },
      yAxis: { type: 'value', minInterval: 1 },
      series: [
        {
          type: 'bar',
          data,
          label: { show: true, position: 'top', formatter: '{c}' },
          itemStyle: { color: '#f56c6c', borderRadius: [3, 3, 0, 0] },
          barMaxWidth: 40,
        },
      ],
    },
    true,
  )
}

function resizeCharts() {
  ganttChart?.resize()
  countChart?.resize()
  durationChart?.resize()
  overdueChart?.resize()
}

let chartObserver = null

onMounted(async () => {
  await loadMeta()
  defaultRange()
  await query()
  window.addEventListener('resize', resizeCharts)
  chartObserver = new ResizeObserver(() => resizeCharts())
  if (ganttRef.value) chartObserver.observe(ganttRef.value)
  if (countRef.value) chartObserver.observe(countRef.value)
  if (durationRef.value) chartObserver.observe(durationRef.value)
  if (overdueRef.value) chartObserver.observe(overdueRef.value)
  resizeCharts()
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', resizeCharts)
  chartObserver?.disconnect()
  ganttChart?.dispose()
  countChart?.dispose()
  durationChart?.dispose()
  overdueChart?.dispose()
})
</script>

<style scoped>
.page > :deep(.el-page-header) {
  flex: none;
}
.filter-bar {
  display: flex;
  gap: 12px;
  align-items: center;
  flex-wrap: wrap;
}
.tip {
  margin-top: 12px;
  color: #909399;
  font-size: 13px;
}
.card-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.chart {
  width: 100%;
}
.gantt-chart {
  height: 400px;
}
.bar-chart {
  height: 300px;
}
</style>