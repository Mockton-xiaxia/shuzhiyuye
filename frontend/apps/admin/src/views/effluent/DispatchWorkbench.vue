<template>
  <div class="page-card">
    <div class="bar">
      <h2 class="page-title">{{ title }}</h2>
      <div class="actions">
        <el-button @click="load">查询</el-button>
        <el-button @click="reset">重置</el-button>
      </div>
    </div>
    <el-form inline class="filters">
      <el-form-item label="状态">
        <el-select v-model="q.status" clearable style="width:130px">
          <el-option label="待接收" value="PENDING" />
          <el-option label="处置中" value="DOING" />
          <el-option label="已完成" value="DONE" />
        </el-select>
      </el-form-item>
      <el-form-item label="检测结果">
        <el-input v-model="q.result" clearable style="width:120px" />
      </el-form-item>
    </el-form>

    <el-table :data="filtered" stripe v-loading="loading">
      <el-table-column prop="officerName" label="执法员" width="120" />
      <el-table-column prop="labName" label="检测机构" min-width="130" />
      <el-table-column prop="result" label="检测结果" width="100" />
      <el-table-column prop="unqualified" label="不合格指标" min-width="110" />
      <el-table-column prop="reportFile" label="检测报告" width="120" />
      <el-table-column prop="disposeDate" label="处置日期" width="120" />
      <el-table-column prop="title" label="调度任务" min-width="140" />
      <el-table-column prop="status" label="状态" width="100">
        <template #default="{ row }"><el-tag size="small">{{ statusLabel(row.status) }}</el-tag></template>
      </el-table-column>
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="openView(row)">查看</el-button>
          <el-button v-if="row.status==='PENDING'" link type="warning" @click="doAccept(row)">接收</el-button>
          <el-button v-if="row.status==='PENDING' || row.status==='DOING'" link type="success" @click="openFeedback(row)">反馈</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-drawer v-model="viewOpen" title="调度详情" size="400px">
      <el-descriptions v-if="current" :column="1" border>
        <el-descriptions-item label="任务">{{ current.title }}</el-descriptions-item>
        <el-descriptions-item label="内容">{{ current.content }}</el-descriptions-item>
        <el-descriptions-item label="执法员">{{ current.officerName }}</el-descriptions-item>
        <el-descriptions-item label="机构">{{ current.labName }}</el-descriptions-item>
        <el-descriptions-item label="结果">{{ current.result }}</el-descriptions-item>
        <el-descriptions-item label="反馈">{{ current.feedback || '—' }}</el-descriptions-item>
        <el-descriptions-item label="状态">{{ statusLabel(current.status) }}</el-descriptions-item>
      </el-descriptions>
    </el-drawer>

    <el-dialog v-model="fbOpen" title="调度反馈" width="460px" destroy-on-close>
      <el-form label-width="90px">
        <el-form-item label="反馈内容"><el-input v-model="feedback" type="textarea" :rows="4" placeholder="说明处置措施与结果" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="fbOpen=false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="doFeedback">提交反馈</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import http from '@/api/http'

defineProps({ title: { type: String, default: '指挥调度记录' } })

const rows = ref([])
const loading = ref(false)
const saving = ref(false)
const current = ref(null)
const viewOpen = ref(false)
const fbOpen = ref(false)
const feedback = ref('')
const q = reactive({ status: '', result: '' })

function statusLabel(s) {
  return ({ PENDING: '待接收', DOING: '处置中', DONE: '已完成', ACCEPTED: '处置中' })[s] || s
}

const filtered = computed(() =>
  rows.value.filter((r) => {
    if (q.status && r.status !== q.status) return false
    if (q.result && !String(r.result || '').includes(q.result)) return false
    return true
  }),
)

async function load() {
  loading.value = true
  try {
    const res = await http.get('/effluent/dispatches')
    rows.value = (res.data || []).filter((d) => d.title && !String(d.title).includes('?'))
  } finally {
    loading.value = false
  }
}
function reset() {
  q.status = ''
  q.result = ''
  load()
}
function openView(row) {
  current.value = row
  viewOpen.value = true
}
async function doAccept(row) {
  await http.post(`/effluent/dispatches/${row.id}/accept`)
  ElMessage.success('已接收，进入处置中')
  load()
}
function openFeedback(row) {
  current.value = row
  feedback.value = ''
  fbOpen.value = true
}
async function doFeedback() {
  if (!feedback.value) {
    ElMessage.warning('请填写反馈内容')
    return
  }
  saving.value = true
  try {
    await http.post(`/effluent/dispatches/${current.value.id}/feedback`, { feedback: feedback.value })
    ElMessage.success('反馈已提交，调度完成')
    fbOpen.value = false
    load()
  } finally {
    saving.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.bar { display:flex; justify-content:space-between; align-items:center; margin-bottom:12px; }
.actions { display:flex; gap:8px; }
.filters { margin-bottom:8px; }
</style>
