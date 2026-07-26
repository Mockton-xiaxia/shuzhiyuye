<template>
  <div class="page-card">
    <div class="bar">
      <h2 class="page-title">经营分析</h2>
      <el-button @click="load">刷新</el-button>
    </div>
    <div class="charts">
      <div ref="lineEl" class="chart" />
      <div ref="pieEl" class="chart" />
    </div>
    <el-table :data="table" stripe style="margin-top:12px">
      <el-table-column prop="month" label="月份" />
      <el-table-column prop="income" label="收入" />
      <el-table-column prop="cost" label="成本" />
      <el-table-column prop="profit" label="利润" />
    </el-table>
  </div>
</template>

<script setup>
import { nextTick, onMounted, onUnmounted, ref } from 'vue'
import * as echarts from 'echarts'
import http from '@/api/http'

const lineEl = ref(null)
const pieEl = ref(null)
const table = ref([])
let lineChart
let pieChart

async function load() {
  const res = await http.get('/ledger/analysis')
  const d = res.data || {}
  table.value = d.list || (Array.isArray(d) ? d : [])
  await nextTick()
  if (!lineChart && lineEl.value) lineChart = echarts.init(lineEl.value)
  if (!pieChart && pieEl.value) pieChart = echarts.init(pieEl.value)
  lineChart?.setOption({
    color: ['#0b6e4f', '#c45c26', '#2ea7ff'],
    tooltip: { trigger: 'axis' },
    legend: { data: ['收入', '成本', '利润'] },
    grid: { left: 40, right: 20, top: 40, bottom: 30 },
    xAxis: { type: 'category', data: d.months || table.value.map((x) => x.month) },
    yAxis: { type: 'value' },
    series: [
      { name: '收入', type: 'bar', data: d.income || table.value.map((x) => x.income) },
      { name: '成本', type: 'bar', data: d.cost || table.value.map((x) => x.cost) },
      { name: '利润', type: 'line', data: d.profit || table.value.map((x) => x.profit) },
    ],
  })
  pieChart?.setOption({
    color: ['#0b6e4f', '#2ea7ff', '#c45c26', '#7c5cbf', '#8899a6'],
    tooltip: { trigger: 'item' },
    title: { text: '成本结构', left: 'center', textStyle: { fontSize: 14 } },
    series: [
      {
        type: 'pie',
        radius: ['35%', '62%'],
        data: d.costShare || [
          { name: '饲料', value: 8 },
          { name: '人工', value: 4 },
        ],
      },
    ],
  })
}

function onResize() {
  lineChart?.resize()
  pieChart?.resize()
}

onMounted(() => {
  load()
  window.addEventListener('resize', onResize)
})
onUnmounted(() => {
  window.removeEventListener('resize', onResize)
  lineChart?.dispose()
  pieChart?.dispose()
})
</script>

<style scoped>
.bar { display:flex; justify-content:space-between; margin-bottom:12px; }
.charts { display:grid; grid-template-columns:1.2fr .8fr; gap:12px; }
.chart { height:320px; border:1px solid #e6eeea; border-radius:8px; background:#fff; }
@media (max-width:900px){ .charts { grid-template-columns:1fr; } }
</style>
