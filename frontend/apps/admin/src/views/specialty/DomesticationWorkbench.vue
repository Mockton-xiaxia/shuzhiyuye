<template>
  <div class="page-card dom-page">
    <h2 class="page-title">{{ title }}</h2>

    <div class="stats">
      <div class="stat-card">
        <div class="stat-label">当前存栏量</div>
        <div class="stat-val">{{ stats.stockCount || 0 }}<span class="unit">尾</span></div>
        <div class="sub">成鱼：{{ stats.adultCount || 0 }}尾 | 幼鱼：{{ stats.juvenileCount || 0 }}尾</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">今日投喂总量</div>
        <div class="stat-val">{{ (stats.todayFeedKg || 0).toFixed(2) }}<span class="unit">kg</span></div>
        <div class="sub">较昨日 {{ feedDelta >= 0 ? '+' : '' }}{{ feedDelta.toFixed(1) }}kg</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">驯化成功率</div>
        <div class="stat-val">{{ stats.successRate || 0 }}<span class="unit">%</span></div>
      </div>
      <div class="stat-card">
        <div class="stat-label">待处理事项</div>
        <div class="stat-val warn">{{ stats.pendingCount || 0 }}<span class="unit">项</span></div>
      </div>
    </div>

    <!-- 企业端：驯化记录 -->
    <template v-if="isEnt">
      <div class="toolbar">
        <el-input v-model="logQ" clearable placeholder="驯化记录" style="width:180px" @keyup.enter="loadLogs" />
        <el-button @click="loadLogs">查询</el-button>
        <el-button @click="logQ=''; loadLogs()">重置</el-button>
        <el-button type="primary" @click="openLogCreate">新增记录</el-button>
      </div>
      <el-table :data="logs" stripe v-loading="logLoading">
        <el-table-column prop="code" label="记录编号" width="120" />
        <el-table-column prop="logDate" label="驯化日期" width="120" />
        <el-table-column prop="pondCode" label="池塘编号" width="100" />
        <el-table-column prop="baitType" label="饵料类型" width="110" />
        <el-table-column prop="feedKg" label="投喂量(kg)" width="100" />
        <el-table-column prop="effect" label="驯化效果" width="100" />
        <el-table-column label="操作" width="140" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openLogEdit(row)">编辑</el-button>
            <el-button link type="danger" @click="removeLog(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </template>

    <!-- 区县端：三 Tab -->
    <el-tabs v-else v-model="tab" class="dom-tabs" @tab-change="onTabChange">
      <el-tab-pane label="稻田管理" name="paddy">
        <div class="toolbar">
          <el-button type="primary" @click="openPaddyCreate">新增地块</el-button>
          <el-button @click="loadPaddy">刷新</el-button>
        </div>
        <el-table :data="paddyRows" stripe v-loading="paddyLoading">
          <el-table-column prop="code" label="地块编号" width="120" />
          <el-table-column prop="areaMu" label="地块面积(亩)" width="110" />
          <el-table-column prop="cropSpecies" label="种植品种" width="100" />
          <el-table-column prop="plantDate" label="种植时间" width="110" />
          <el-table-column prop="statusLabel" label="当前状态" width="90" />
          <el-table-column prop="cost" label="总成本(元)" width="100" />
          <el-table-column prop="yieldKg" label="总产量(kg)" width="100" />
          <el-table-column prop="income" label="总收入(元)" width="100" />
          <el-table-column prop="profit" label="纯利润(元)" width="100" />
          <el-table-column label="操作" width="140" fixed="right">
            <template #default="{ row }">
              <el-button link type="primary" @click="openPaddyEdit(row)">编辑</el-button>
              <el-button link type="danger" @click="removePlot(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
      <el-tab-pane label="渔稻生产管理" name="ricefish">
        <div class="toolbar">
          <el-button type="primary" @click="openRiceFishCreate">新增共生池</el-button>
          <el-button @click="loadRiceFish">刷新</el-button>
        </div>
        <el-table :data="riceFishRows" stripe v-loading="riceFishLoading">
          <el-table-column prop="code" label="地块编号" width="120" />
          <el-table-column prop="areaMu" label="地块面积(亩)" width="110" />
          <el-table-column prop="cropSpecies" label="水稻品种" width="100" />
          <el-table-column prop="fishSpecies" label="养殖品种" width="100" />
          <el-table-column prop="plantDate" label="种植时间" width="110" />
          <el-table-column prop="statusLabel" label="当前状态" width="90" />
          <el-table-column prop="cost" label="总成本(元)" width="100" />
          <el-table-column prop="riceYieldKg" label="稻产量(kg)" width="100" />
          <el-table-column prop="fishYieldKg" label="鱼产量(kg)" width="100" />
          <el-table-column prop="income" label="总收入(元)" width="100" />
          <el-table-column prop="profit" label="纯利润(元)" width="100" />
          <el-table-column label="操作" width="140" fixed="right">
            <template #default="{ row }">
              <el-button link type="primary" @click="openRiceFishEdit(row)">编辑</el-button>
              <el-button link type="danger" @click="removePlot(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
      <el-tab-pane label="经济效益统计" name="economics">
        <div v-loading="econLoading" class="econ-wrap">
          <div class="econ-cards">
            <div class="econ-block">
              <h4>稻田管理（纯稻）统计</h4>
              <div class="econ-grid">
                <span>总种植面积：{{ econ.paddy?.areaMu || 0 }} 亩</span>
                <span>总产量：{{ econ.paddy?.yieldKg || 0 }} kg</span>
                <span>总成本：{{ econ.paddy?.cost || 0 }} 元</span>
                <span>总收益：{{ econ.paddy?.income || 0 }} 元</span>
                <span>总利润：{{ econ.paddy?.profit || 0 }} 元</span>
                <span>亩均成本：{{ econ.paddy?.costPerMu || 0 }} 元</span>
                <span>亩均收益：{{ econ.paddy?.incomePerMu || 0 }} 元</span>
              </div>
            </div>
            <div class="econ-block">
              <h4>渔稻共生统计</h4>
              <div class="econ-grid">
                <span>总种植面积：{{ econ.riceFish?.areaMu || 0 }} 亩</span>
                <span>总产量：{{ econ.riceFish?.yieldKg || 0 }} kg</span>
                <span>总成本：{{ econ.riceFish?.cost || 0 }} 元</span>
                <span>总收益：{{ econ.riceFish?.income || 0 }} 元</span>
                <span>总利润：{{ econ.riceFish?.profit || 0 }} 元</span>
                <span>亩均成本：{{ econ.riceFish?.costPerMu || 0 }} 元</span>
                <span>亩均收益：{{ econ.riceFish?.incomePerMu || 0 }} 元</span>
              </div>
            </div>
          </div>
          <div ref="chartEl" class="chart-el" />
        </div>
      </el-tab-pane>
    </el-tabs>

    <!-- 稻田地块表单 -->
    <el-dialog v-model="paddyDlg" :title="editId ? '编辑地块' : '新增地块'" width="560px" destroy-on-close>
      <el-form :model="paddyForm" label-width="130px">
        <el-form-item label="地块编号"><el-input :model-value="paddyForm.code || '系统自动生成'" disabled /></el-form-item>
        <el-form-item label="地块面积(亩)" required><el-input-number v-model="paddyForm.areaMu" :min="0" :precision="2" style="width:100%" /></el-form-item>
        <el-form-item label="种植品种" required><el-input v-model="paddyForm.cropSpecies" placeholder="如 优质稻" /></el-form-item>
        <el-form-item label="种植时间" required><el-date-picker v-model="paddyForm.plantDate" type="date" value-format="YYYY-MM-DD" style="width:100%" /></el-form-item>
        <el-form-item label="当前状态" required>
          <el-select v-model="paddyForm.status" style="width:100%">
            <el-option label="生长中" value="GROWING" /><el-option label="已收获" value="HARVESTED" /><el-option label="休耕" value="FALLOW" />
          </el-select>
        </el-form-item>
        <el-form-item label="土壤情况"><el-input v-model="paddyForm.soilDesc" type="textarea" :rows="2" maxlength="100" show-word-limit /></el-form-item>
        <el-form-item label="灌溉方式"><el-input v-model="paddyForm.irrigation" type="textarea" :rows="2" maxlength="100" show-word-limit /></el-form-item>
        <el-form-item label="总成本(元)" required><el-input-number v-model="paddyForm.cost" :min="0" style="width:100%" @change="calcPaddyProfit" /></el-form-item>
        <el-form-item label="总产量(kg)" required><el-input-number v-model="paddyForm.yieldKg" :min="0" style="width:100%" /></el-form-item>
        <el-form-item label="总收入(元)" required><el-input-number v-model="paddyForm.income" :min="0" style="width:100%" @change="calcPaddyProfit" /></el-form-item>
        <el-form-item label="纯利润(元)"><el-input :model-value="paddyProfit" disabled placeholder="计算显示，总收入-总成本" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="paddyDlg=false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="savePaddy">确定</el-button>
      </template>
    </el-dialog>

    <!-- 渔稻地块表单 -->
    <el-dialog v-model="riceDlg" :title="editId ? '编辑共生池' : '新增共生池'" width="560px" destroy-on-close>
      <el-form :model="riceForm" label-width="130px">
        <el-form-item label="地块编号"><el-input :model-value="riceForm.code || '系统自动生成'" disabled /></el-form-item>
        <el-form-item label="地块面积(亩)" required><el-input-number v-model="riceForm.areaMu" :min="0" :precision="2" style="width:100%" /></el-form-item>
        <el-form-item label="水稻品种" required><el-input v-model="riceForm.cropSpecies" /></el-form-item>
        <el-form-item label="养殖品种" required><el-input v-model="riceForm.fishSpecies" placeholder="如 鲤、鲫" /></el-form-item>
        <el-form-item label="投放数量(kg)"><el-input-number v-model="riceForm.stockingKg" :min="0" style="width:100%" /></el-form-item>
        <el-form-item label="种植时间" required><el-date-picker v-model="riceForm.plantDate" type="date" value-format="YYYY-MM-DD" style="width:100%" /></el-form-item>
        <el-form-item label="当前状态" required>
          <el-select v-model="riceForm.status" style="width:100%">
            <el-option label="生长中" value="GROWING" /><el-option label="已收获" value="HARVESTED" />
          </el-select>
        </el-form-item>
        <el-form-item label="总成本(元)" required><el-input-number v-model="riceForm.cost" :min="0" style="width:100%" @change="calcRiceProfit" /></el-form-item>
        <el-form-item label="稻产量(kg)" required><el-input-number v-model="riceForm.riceYieldKg" :min="0" style="width:100%" /></el-form-item>
        <el-form-item label="鱼产量(kg)" required><el-input-number v-model="riceForm.fishYieldKg" :min="0" style="width:100%" /></el-form-item>
        <el-form-item label="总收入(元)" required><el-input-number v-model="riceForm.income" :min="0" style="width:100%" @change="calcRiceProfit" /></el-form-item>
        <el-form-item label="利润(元)"><el-input :model-value="riceProfit" disabled placeholder="计算显示，总收入-总成本" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="riceDlg=false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="saveRiceFish">确定</el-button>
      </template>
    </el-dialog>

    <!-- 驯化记录表单 -->
    <el-dialog v-model="logDlg" :title="logEditId ? '编辑记录' : '新增记录'" width="480px" destroy-on-close>
      <el-form :model="logForm" label-width="100px">
        <el-form-item label="驯化日期" required><el-date-picker v-model="logForm.logDate" type="date" value-format="YYYY-MM-DD" style="width:100%" /></el-form-item>
        <el-form-item label="池塘编号" required><el-input v-model="logForm.pondCode" /></el-form-item>
        <el-form-item label="饵料类型" required><el-input v-model="logForm.baitType" placeholder="鲜活饵料/配合饲料" /></el-form-item>
        <el-form-item label="投喂量(kg)" required><el-input-number v-model="logForm.feedKg" :min="0" :precision="1" style="width:100%" /></el-form-item>
        <el-form-item label="驯化效果"><el-input v-model="logForm.effect" placeholder="良好/一般" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="logDlg=false">取消</el-button>
        <el-button type="primary" :loading="logSaving" @click="saveLog">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, onUnmounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import * as echarts from 'echarts'
import http from '@/api/http'
import { useAuthStore } from '@/stores/auth'

defineProps({ title: { type: String, default: '育种驯化管理' } })

const auth = useAuthStore()
const isEnt = computed(() => auth.portal === 'ENT')

const stats = reactive({ stockCount: 0, adultCount: 0, juvenileCount: 0, todayFeedKg: 0, yesterdayFeedKg: 0, successRate: 0, pendingCount: 0 })
const feedDelta = computed(() => (stats.todayFeedKg || 0) - (stats.yesterdayFeedKg || 0))

const tab = ref('paddy')
const paddyRows = ref([])
const riceFishRows = ref([])
const paddyLoading = ref(false)
const riceFishLoading = ref(false)
const saving = ref(false)
const editId = ref(null)

const paddyDlg = ref(false)
const riceDlg = ref(false)
const paddyForm = reactive(emptyPaddy())
const riceForm = reactive(emptyRice())

const logs = ref([])
const logQ = ref('')
const logLoading = ref(false)
const logDlg = ref(false)
const logEditId = ref(null)
const logSaving = ref(false)
const logForm = reactive({ logDate: '', pondCode: '', baitType: '', feedKg: null, effect: '' })

const econ = reactive({ paddy: {}, riceFish: {}, chart: {} })
const econLoading = ref(false)
const chartEl = ref(null)
let chart

const paddyProfit = computed(() => Math.max(0, (paddyForm.income || 0) - (paddyForm.cost || 0)))
const riceProfit = computed(() => Math.max(0, (riceForm.income || 0) - (riceForm.cost || 0)))

function emptyPaddy() {
  return { code: '', areaMu: null, cropSpecies: '', plantDate: '', status: 'GROWING', soilDesc: '', irrigation: '', cost: null, yieldKg: null, income: null }
}
function emptyRice() {
  return { code: '', areaMu: null, cropSpecies: '', fishSpecies: '', stockingKg: null, plantDate: '', status: 'GROWING', cost: null, riceYieldKg: null, fishYieldKg: null, income: null }
}

function calcPaddyProfit() {}
function calcRiceProfit() {}

async function loadStats() {
  try {
    const res = await http.get('/specialty/domestication/stats')
    Object.assign(stats, res.data || {})
  } catch {
    /* optional */
  }
}

async function loadPaddy() {
  paddyLoading.value = true
  try {
    const res = await http.get('/specialty/domestication/plots', { params: { plotType: 'PADDY' } })
    paddyRows.value = res.data?.list || []
  } finally {
    paddyLoading.value = false
  }
}

async function loadRiceFish() {
  riceFishLoading.value = true
  try {
    const res = await http.get('/specialty/domestication/plots', { params: { plotType: 'RICE_FISH' } })
    riceFishRows.value = res.data?.list || []
  } finally {
    riceFishLoading.value = false
  }
}

async function loadEconomics() {
  econLoading.value = true
  try {
    const res = await http.get('/specialty/domestication/economics')
    Object.assign(econ, res.data || {})
    await nextTick()
    renderChart()
  } finally {
    econLoading.value = false
  }
}

function renderChart() {
  if (!chartEl.value) return
  if (!chart) chart = echarts.init(chartEl.value)
  const c = econ.chart || {}
  chart.setOption({
    color: ['#e74c3c', '#3498db', '#2ecc71'],
    title: { text: '纯稻 VS 渔稻共生 收益对比', left: 'center', textStyle: { fontSize: 14 } },
    tooltip: { trigger: 'axis' },
    legend: { data: ['成本', '收益', '利润'], top: 28 },
    grid: { left: 50, right: 20, top: 70, bottom: 30 },
    xAxis: { type: 'category', data: c.categories || ['纯稻', '渔稻共生'] },
    yAxis: { type: 'value' },
    series: [
      { name: '成本', type: 'bar', data: c.cost || [0, 0] },
      { name: '收益', type: 'bar', data: c.income || [0, 0] },
      { name: '利润', type: 'bar', data: c.profit || [0, 0] },
    ],
  })
}

function onTabChange(name) {
  if (name === 'economics') loadEconomics()
}

function openPaddyCreate() {
  editId.value = null
  Object.assign(paddyForm, emptyPaddy())
  paddyDlg.value = true
}
function openPaddyEdit(row) {
  editId.value = row.id
  Object.assign(paddyForm, { ...row, cropSpecies: row.cropSpecies, plantDate: row.plantDate })
  paddyDlg.value = true
}
function openRiceFishCreate() {
  editId.value = null
  Object.assign(riceForm, emptyRice())
  riceDlg.value = true
}
function openRiceFishEdit(row) {
  editId.value = row.id
  Object.assign(riceForm, { ...row })
  riceDlg.value = true
}

async function savePaddy() {
  if (!paddyForm.areaMu || !paddyForm.cropSpecies || !paddyForm.plantDate) {
    ElMessage.warning('请填写必填项')
    return
  }
  saving.value = true
  try {
    const body = { plotType: 'PADDY', ...paddyForm, profit: paddyProfit.value }
    if (editId.value) await http.put(`/specialty/domestication/plots/${editId.value}`, body)
    else await http.post('/specialty/domestication/plots', body)
    ElMessage.success('已保存')
    paddyDlg.value = false
    loadPaddy()
    loadStats()
  } finally {
    saving.value = false
  }
}

async function saveRiceFish() {
  if (!riceForm.areaMu || !riceForm.cropSpecies || !riceForm.fishSpecies || !riceForm.plantDate) {
    ElMessage.warning('请填写必填项')
    return
  }
  saving.value = true
  try {
    const body = { plotType: 'RICE_FISH', ...riceForm, profit: riceProfit.value }
    if (editId.value) await http.put(`/specialty/domestication/plots/${editId.value}`, body)
    else await http.post('/specialty/domestication/plots', body)
    ElMessage.success('已保存')
    riceDlg.value = false
    loadRiceFish()
    loadStats()
  } finally {
    saving.value = false
  }
}

async function removePlot(row) {
  await ElMessageBox.confirm(`确定删除地块「${row.code}」？`, '删除确认', { type: 'warning' })
  await http.delete(`/specialty/domestication/plots/${row.id}`)
  ElMessage.success('已删除')
  loadPaddy()
  loadRiceFish()
  loadStats()
}

async function loadLogs() {
  logLoading.value = true
  try {
    const res = await http.get('/specialty/domestication/logs', { params: { keyword: logQ.value || undefined } })
    logs.value = res.data?.list || []
  } finally {
    logLoading.value = false
  }
}

function openLogCreate() {
  logEditId.value = null
  Object.assign(logForm, { logDate: '', pondCode: '', baitType: '', feedKg: null, effect: '' })
  logDlg.value = true
}
function openLogEdit(row) {
  logEditId.value = row.id
  Object.assign(logForm, { logDate: row.logDate, pondCode: row.pondCode, baitType: row.baitType, feedKg: row.feedKg, effect: row.effect })
  logDlg.value = true
}
async function saveLog() {
  if (!logForm.logDate || !logForm.pondCode || !logForm.baitType) {
    ElMessage.warning('请填写必填项')
    return
  }
  logSaving.value = true
  try {
    if (logEditId.value) await http.put(`/specialty/domestication/logs/${logEditId.value}`, logForm)
    else await http.post('/specialty/domestication/logs', logForm)
    ElMessage.success('已保存')
    logDlg.value = false
    loadLogs()
    loadStats()
  } finally {
    logSaving.value = false
  }
}
async function removeLog(row) {
  await ElMessageBox.confirm('确定删除该记录？', '删除确认', { type: 'warning' })
  await http.delete(`/specialty/domestication/logs/${row.id}`)
  ElMessage.success('已删除')
  loadLogs()
  loadStats()
}

function onResize() {
  chart?.resize()
}

onMounted(async () => {
  await loadStats()
  if (isEnt.value) {
    await loadLogs()
  } else {
    await loadPaddy()
    await loadRiceFish()
  }
  window.addEventListener('resize', onResize)
})
onUnmounted(() => {
  window.removeEventListener('resize', onResize)
  chart?.dispose()
})
</script>

<style scoped>
.dom-page { min-height: 520px; }
.stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 20px; }
.stat-card { background: linear-gradient(135deg, #f0f7ff 0%, #fff 100%); border: 1px solid #e4e9f2; border-radius: 8px; padding: 16px 20px; }
.stat-label { color: #606266; font-size: 13px; margin-bottom: 8px; }
.stat-val { font-size: 26px; font-weight: 600; color: #303133; }
.stat-val.warn { color: #e6a23c; }
.unit { font-size: 14px; font-weight: normal; margin-left: 4px; color: #909399; }
.sub { font-size: 12px; color: #909399; margin-top: 6px; }
.toolbar { display: flex; gap: 8px; margin-bottom: 12px; flex-wrap: wrap; }
.econ-wrap { padding: 8px 0; }
.econ-cards { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 20px; }
.econ-block { border: 1px solid #ebeef5; border-radius: 8px; padding: 16px; background: #fafafa; }
.econ-block h4 { margin: 0 0 12px; font-size: 14px; color: #303133; }
.econ-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; font-size: 13px; color: #606266; }
.chart-el { height: 360px; width: 100%; }
@media (max-width: 900px) {
  .stats, .econ-cards { grid-template-columns: 1fr 1fr; }
}
</style>
