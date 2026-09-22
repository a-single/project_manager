<template>
  <div class="page">
    <div class="card filter-card">
      <div class="field">
        <label>选择项目</label>
        <select v-model="projectId" class="select" @change="loadMeta">
          <option v-for="p in projectOptions" :key="p.id" :value="p.id">{{ p.name }}</option>
        </select>
      </div>
      <div class="field">
        <label>人员过滤</label>
        <div class="person-chips">
          <span
            class="chip"
            :class="{ active: userFilter === -1 }"
            @click="userFilter = -1"
          >全部</span>
          <span
            v-for="m in members"
            :key="m.id"
            class="chip"
            :class="{ active: userFilter === m.id }"
            @click="toggleUser(m.id)"
          >{{ m.full_name || m.username }}</span>
        </div>
      </div>
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
      <p v-if="projectOptions.length === 0" style="text-align: center; margin-top: 10px" class="muted">
        当前账号暂无可查看的项目（需加入项目后才能统计）
      </p>
    </div>

    <template v-if="records.length > 0">
      <div class="card">
        <div class="chart-title">甘特图 · 任务完成时间轴</div>
        <div ref="ganttRef" class="chart-box gantt"></div>
      </div>
      <div class="card">
        <div class="chart-title">条形图 · 各人员完成数量</div>
        <div ref="countRef" class="chart-box"></div>
      </div>
      <div class="card">
        <div class="chart-title">条形图 · 人员工作时长</div>
        <div ref="durationRef" class="chart-box"></div>
      </div>
      <div class="card">
        <div class="chart-title">条形图 · 人员超时任务数量</div>
        <div ref="overdueRef" class="chart-box"></div>
        <div v-if="overdueData.length === 0" class="muted" style="margin-top: 8px">当前项目暂无超时任务</div>
      </div>
    </template>

    <div v-else-if="!loading && projectOptions.length > 0" class="card empty" style="padding: 28px 0">
      <div class="empty-icon">📊</div>该时间段内暂无完成的任务
    </div>
  </div>
</template>

<script setup>
import { nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import * as echarts from 'echarts/core'
import { BarChart, CustomChart } from 'echarts/charts'
import { GridComponent, TooltipComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import { api } from '../api'

echarts.use([BarChart, CustomChart, GridComponent, TooltipComponent, CanvasRenderer])

const projectId = ref(null)
const projectOptions = ref([])
const members = ref([])
const userFilter = ref(-1)
const startDate = ref('')
const endDate = ref('')
const records = ref([])
const loading = ref(false)

const ganttRef = ref(null)
const countRef = ref(null)
const durationRef = ref(null)
const overdueRef = ref(null)
let ganttChart = null
let countChart = null
let durationChart = null
let overdueChart = null

const overdueData = ref([])

function toggleUser(id) {
  userFilter.value = userFilter.value === id ? -1 : id
}

function defaultRange() {
  const end = new Date()
  const start = new Date()
  start.setDate(start.getDate() - 29)
  startDate.value = toYMD(start)
  endDate.value = toYMD(end)
}

function toYMD(d) {
  const p = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`
}

async function loadMeta() {
  if (!projectId.value) return
  try {
    members.value = await api.projects.members(projectId.value)
  } catch (e) {
    alert(e.message)
  }
}

async function query() {
  if (!projectId.value) {
    alert('请选择项目')
    return
  }
  if (!startDate.value || !endDate.value) {
    alert('请选择起止日期')
    return
  }
  loading.value = true
  try {
    const params = {
      project_id: projectId.value,
      start: startDate.value,
      end: endDate.value,
    }
    if (userFilter.value !== -1) params.user_id = userFilter.value
    records.value = await api.stats.tasks(params)
    overdueData.value = await api.stats.overdueCounts(projectId.value)
    await nextTick()
    renderCharts()
  } catch (e) {
    alert(e.message)
  } finally {
    loading.value = false
  }
}

async function renderCharts() {
  renderGantt()
  renderBarCount()
  renderBarDuration()
  renderBarOverdue()
}

function renderGantt() {
  const byUser = {}
  records.value.forEach((r) => {
    if (!byUser[r.assignee_name]) byUser[r.assignee_name] = []
    byUser[r.assignee_name].push(r)
  })
  const users = Object.keys(byUser).sort((a, b) => byUser[b].length - byUser[a].length)
  const idxMap = {}
  users.forEach((u, i) => (idxMap[u] = i))

  const times = records.value.flatMap((r) => [new Date(r.created_at).getTime(), new Date(r.completed_at).getTime()])
  let min = Math.min(...times)
  let max = Math.max(...times)
  if (min === max) {
    min -= 3600 * 1000
    max += 3600 * 1000
  }

  const seriesData = records.value.map((r, i) => ({
    name: r.title,
    dataIndex: i,
    // custom 系列要求 value 为数组维度(encode 按索引引用): [assignee, start, end]
    value: [
      r.assignee_name,
      new Date(r.created_at).getTime(),
      new Date(r.completed_at).getTime(),
    ],
  }))

  if (ganttChart) ganttChart.dispose()
  ganttChart = echarts.init(ganttRef.value)
  ganttChart.setOption({
    tooltip: {
      formatter: (p) => {
        if (!p.data) return ''
        const v = p.data.value
        return `${v[0]}<br/><b>${p.data.name}</b><br/>开始：${fmtTime(v[1])}<br/>完成：${fmtTime(v[2])}`
      },
    },
    grid: { left: 70, right: 16, top: 24, bottom: 20 },
    xAxis: { type: 'time', min, max },
    yAxis: { type: 'category', data: users, axisLabel: { fontSize: 11 } },
    series: [
      {
        type: 'custom',
        renderItem(params, apiOpt) {
          // 官方 custom 用法：api.value(idx) 按 encode 维度取值
          const assignee = apiOpt.value(0)
          const start = apiOpt.coord([apiOpt.value(1), assignee])
          const end = apiOpt.coord([apiOpt.value(2), assignee])
          const height = apiOpt.size([0, 1])[1] * 0.6
          return {
            type: 'rect',
            shape: { x: start[0] + 4, y: start[1] - height / 2, width: Math.max(end[0] - start[0] - 8, 4), height, r: 4 },
            style: { fill: 'rgba(110,168,254,0.85)' },
          }
        },
        encode: { x: [1, 2], y: 0 },
        data: seriesData,
      },
    ],
  })
}

function fmtTime(ts) {
  if (!ts) return '-'
  const d = new Date(ts)
  if (isNaN(d.getTime())) return '-'
  const p = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())} ${p(d.getHours())}:${p(d.getMinutes())}`
}

function fmtDurMin(mins) {
  if (mins == null) return '-'
  if (mins < 60) return `${Math.round(mins)} 分钟`
  return `${Math.floor(mins / 60)} 小时 ${Math.round(mins % 60)} 分`
}

function aggregate(fn) {
  const map = {}
  records.value.forEach((r) => {
    if (!map[r.assignee_name]) map[r.assignee_name] = 0
    map[r.assignee_name] += fn(r)
  })
  return Object.entries(map)
    .map(([name, v]) => ({ name, v }))
    .sort((a, b) => b.v - a.v)
}

function renderBarCount() {
  const data = aggregate(() => 1)
  if (countChart) countChart.dispose()
  countChart = echarts.init(countRef.value)
  countChart.setOption({
    tooltip: {},
    grid: { left: 56, right: 16, top: 16, bottom: 20 },
    xAxis: { type: 'value', minInterval: 1 },
    yAxis: { type: 'category', data: data.map((d) => d.name), axisLabel: { fontSize: 11 } },
    series: [
      {
        type: 'bar',
        data: data.map((d) => d.v),
        barWidth: 14,
        itemStyle: {
          color: { type: 'linear', x: 0, y: 0, x2: 1, y2: 0, colorStops: [{ offset: 0, color: '#6ea8fe' }, { offset: 1, color: '#38bdf8' }] },
          borderRadius: 7,
        },
        label: { show: true, position: 'right' },
      },
    ],
  })
}

function renderBarDuration() {
  const data = aggregate((r) => r.duration_minutes || 0).map((d) => ({
    name: d.name,
    // 每人累计工作时长(小时)，不足 0.1 小时的按 0.1 小时展示
    v: Math.max(Math.round((d.v / 60) * 10) / 10, 0.1),
  }))
  if (durationChart) durationChart.dispose()
  durationChart = echarts.init(durationRef.value)
  durationChart.setOption({
    tooltip: {},
    grid: { left: 56, right: 16, top: 16, bottom: 20 },
    xAxis: { type: 'value' },
    yAxis: { type: 'category', data: data.map((d) => d.name), axisLabel: { fontSize: 11 } },
    series: [
      {
        type: 'bar',
        data: data.map((d) => d.v),
        barWidth: 14,
        itemStyle: {
          color: { type: 'linear', x: 0, y: 0, x2: 1, y2: 0, colorStops: [{ offset: 0, color: '#22c55e' }, { offset: 1, color: '#a3e635' }] },
          borderRadius: 7,
        },
        label: { show: true, position: 'right', formatter: (p) => p.value + 'h' },
      },
    ],
  })
}

function renderBarOverdue() {
  const data = overdueData.value
  if (overdueChart) overdueChart.dispose()
  overdueChart = echarts.init(overdueRef.value)
  overdueChart.setOption({
    tooltip: {},
    grid: { left: 56, right: 16, top: 16, bottom: 20 },
    xAxis: { type: 'value', minInterval: 1 },
    yAxis: { type: 'category', data: data.map((d) => d.assignee_name), axisLabel: { fontSize: 11 } },
    series: [
      {
        type: 'bar',
        data: data.map((d) => d.count),
        barWidth: 14,
        itemStyle: {
          color: { type: 'linear', x: 0, y: 0, x2: 1, y2: 0, colorStops: [{ offset: 0, color: '#f87171' }, { offset: 1, color: '#ef4444' }] },
          borderRadius: 7,
        },
        label: { show: true, position: 'right' },
      },
    ],
  })
}

async function resize() {
  ganttChart?.resize()
  countChart?.resize()
  durationChart?.resize()
  overdueChart?.resize()
}

onMounted(async () => {
  try {
    projectOptions.value = await api.projects.list()
  } catch (e) {
    alert(e.message)
    return
  }
  if (projectOptions.value.length === 0) return
  projectId.value = projectOptions.value[0].id
  await loadMeta()
  defaultRange()
  await query()
  window.addEventListener('resize', resize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', resize)
  ganttChart?.dispose()
  countChart?.dispose()
  durationChart?.dispose()
  overdueChart?.dispose()
})
</script>

<style scoped>
.chart-title {
  font-weight: 700;
  margin-bottom: 10px;
}
.person-chips {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
.chip {
  padding: 6px 12px;
  border-radius: 999px;
  background: #f1f3f9;
  font-size: 13px;
  cursor: pointer;
  color: var(--sub);
}
.chip.active {
  background: var(--primary-grad);
  color: #fff;
}
.gantt {
  height: 300px;
}
</style>