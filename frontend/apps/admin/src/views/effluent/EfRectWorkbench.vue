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
          <el-option label="整改中" value="RECTIFYING" />
          <el-option label="待验收" value="REVIEW" />
          <el-option label="已闭环" value="CLOSED" />
        </el-select>
      </el-form-item>
    </el-form>
    <el-table :data="filtered" stripe v-loading="loading">
      <el-table-column prop="superviseType" label="监管类型" width="100" />
      <el-table-column prop="officerName" label="执法员" width="110" />
      <el-table-column prop="labName" label="监测机构" min-width="120" />
      <el-table-column prop="unqualified" label="不合格指标" min-width="110" />
      <el-table-column prop="reportFile" label="检测报告" width="110" />
      <el-table-column prop="disposeDate" label="执法/处置日期" width="120" />
      <el-table-column prop="title" label="整改事项" min-width="140" />
      <el-table-column prop="status" label="状态" width="100">
        <template #default="{ row }"><el-tag size="small">{{ statusLabel(row.status) }}</el-tag></template>
      </el-table-column>
      <el-table-column label="操作" width="220" fixed="right">
        <template #default="{ row }">
          <el-button v-if="row.status==='PENDING'" link type="warning" @click="doAccept(row)">接收</el-button>
          <el-button v-if="row.status==='PENDING' || row.status==='RECTIFYING'" link type="success" @click="openReply(row)">整改回复</el-button>
          <el-button v-if="isGov && row.status==='REVIEW'" link type="danger" @click="doReview(row, true)">验收通过</el-button>
          <el-button v-if="isGov && row.status==='REVIEW'" link @click="doReview(row, false)">驳回</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="replyOpen" title="尾水整改回复" width="460px" destroy-on-close>
      <el-form label-width="90px">
        <el-form-item label="整改说明"><el-input v-model="reply" type="textarea" :rows="4" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="replyOpen=false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="doReply">提交</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import http from '@/api/http'
import { useAuthStore } from '@/stores/auth'

defineProps({ title: { type: String, default: '整改记录' } })

const auth = useAuthStore()
const isGov = computed(() => auth.portal === 'GOV' || auth.portal === 'BOTH')
const rows = ref([])
const loading = ref(false)
const saving = ref(false)
const replyOpen = ref(false)
const reply = ref('')
const current = ref(null)
const q = reactive({ status: '' })

function statusLabel(s) {
  return ({ PENDING: '待接收', RECTIFYING: '整改中', REVIEW: '待验收', CLOSED: '已闭环' })[s] || s
}
const filtered = computed(() => rows.value.filter((r) => !q.status || r.status === q.status))

async function load() {
  loading.value = true
  try {
    const res = await http.get('/effluent/rectifications')
    rows.value = res.data || []
  } finally {
    loading.value = false
  }
}
function reset() {
  q.status = ''
  load()
}
async function doAccept(row) {
  await http.post(`/effluent/rectifications/${row.id}/accept`)
  ElMessage.success('已接收')
  load()
}
function openReply(row) {
  current.value = row
  reply.value = ''
  replyOpen.value = true
}
async function doReply() {
  if (!reply.value) {
    ElMessage.warning('请填写整改说明')
    return
  }
  saving.value = true
  try {
    await http.post(`/effluent/rectifications/${current.value.id}/reply`, { feedback: reply.value })
    ElMessage.success('已提交，待验收')
    replyOpen.value = false
    load()
  } finally {
    saving.value = false
  }
}
async function doReview(row, approved) {
  await http.post(`/effluent/rectifications/${row.id}/review`, { approved, opinion: approved ? '验收通过' : '需继续整改' })
  ElMessage.success(approved ? '已闭环' : '已驳回')
  load()
}

onMounted(load)
</script>

<style scoped>
.bar { display:flex; justify-content:space-between; align-items:center; margin-bottom:12px; }
.actions { display:flex; gap:8px; }
.filters { margin-bottom:8px; }
</style>
