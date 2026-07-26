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
        <el-select v-model="q.status" clearable style="width:140px">
          <el-option v-for="s in statusOpts" :key="s" :label="statusLabel(s)" :value="s" />
        </el-select>
      </el-form-item>
      <el-form-item v-if="isGov" label="抽检主体"><el-input v-model="q.enterpriseName" clearable style="width:160px" /></el-form-item>
      <el-form-item label="品种"><el-input v-model="q.species" clearable style="width:120px" /></el-form-item>
    </el-form>

    <el-table :data="filtered" stripe v-loading="loading">
      <el-table-column v-if="isGov" prop="enterpriseName" label="抽检主体" min-width="130" />
      <el-table-column v-if="isGov" prop="regionName" label="所属区域" width="90" />
      <el-table-column prop="species" label="检测品种" width="90" />
      <el-table-column v-if="!isGov" prop="pondName" label="养殖塘口" width="110" />
      <el-table-column v-if="!isGov" prop="sampleCount" label="抽检数量" width="90" />
      <el-table-column prop="labName" label="检测机构" min-width="120" />
      <el-table-column prop="result" label="检测结果" width="100" />
      <el-table-column prop="unqualified" label="不合格指标" min-width="110" />
      <el-table-column prop="reportFile" label="检测报告" width="120" />
      <el-table-column prop="inspectedAt" label="抽测日期" min-width="150" />
      <el-table-column prop="status" label="状态" width="110">
        <template #default="{ row }"><el-tag size="small">{{ statusLabel(row.status) }}</el-tag></template>
      </el-table-column>
      <el-table-column label="操作" width="220" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="openView(row)">查看</el-button>
          <el-button v-if="canAccept(row)" link type="warning" @click="doAccept(row)">接收</el-button>
          <el-button v-if="canReply(row)" link type="success" @click="openReply(row)">整改回复</el-button>
          <el-button v-if="canReview(row)" link type="danger" @click="openReview(row)">验收复核</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-drawer v-model="viewOpen" title="整改详情" size="420px">
      <el-descriptions v-if="current" :column="1" border>
        <el-descriptions-item label="主体">{{ current.enterpriseName }}</el-descriptions-item>
        <el-descriptions-item label="塘口">{{ current.pondName }}</el-descriptions-item>
        <el-descriptions-item label="品种">{{ current.species }}</el-descriptions-item>
        <el-descriptions-item label="机构">{{ current.labName }}</el-descriptions-item>
        <el-descriptions-item label="结果">{{ current.result }}</el-descriptions-item>
        <el-descriptions-item label="不合格指标">{{ current.unqualified }}</el-descriptions-item>
        <el-descriptions-item label="下发说明">{{ current.content }}</el-descriptions-item>
        <el-descriptions-item label="整改说明">{{ current.reply || '—' }}</el-descriptions-item>
        <el-descriptions-item label="整改日期">{{ current.rectifyDate || '—' }}</el-descriptions-item>
        <el-descriptions-item label="整改证明">{{ current.proofFile || '—' }}</el-descriptions-item>
        <el-descriptions-item label="验收意见">{{ current.reviewOpinion || '—' }}</el-descriptions-item>
        <el-descriptions-item label="状态">{{ statusLabel(current.status) }}</el-descriptions-item>
      </el-descriptions>
    </el-drawer>

    <el-dialog v-model="replyOpen" title="整改回复" width="480px" destroy-on-close>
      <el-form :model="replyForm" label-width="100px">
        <el-form-item label="整改日期"><el-date-picker v-model="replyForm.rectifyDate" type="date" value-format="YYYY-MM-DD" style="width:100%" /></el-form-item>
        <el-form-item label="整改说明"><el-input v-model="replyForm.reply" type="textarea" :rows="4" /></el-form-item>
        <el-form-item label="整改证明">
          <el-upload :auto-upload="false" :limit="1" @change="(f) => (replyForm.proofFile = f?.name || f?.raw?.name || '整改证明.jpg')">
            <el-button>选择证明材料</el-button>
          </el-upload>
          <div class="muted">演示：仅记录文件名</div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="replyOpen=false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="doReply">提交整改</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="reviewOpen" title="验收复核" width="480px" destroy-on-close>
      <el-form :model="reviewForm" label-width="100px">
        <el-form-item label="验收日期"><el-date-picker v-model="reviewForm.reviewDate" type="date" value-format="YYYY-MM-DD" style="width:100%" /></el-form-item>
        <el-form-item label="验收结果">
          <el-radio-group v-model="reviewForm.approved">
            <el-radio :value="true">通过</el-radio>
            <el-radio :value="false">驳回</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="验收说明"><el-input v-model="reviewForm.opinion" type="textarea" :rows="3" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="reviewOpen=false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="doReview">提交验收</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import http from '@/api/http'
import { useAuthStore } from '@/stores/auth'

defineProps({ title: { type: String, default: '质量整改' } })

const auth = useAuthStore()
const isGov = computed(() => auth.portal === 'GOV' || auth.portal === 'BOTH')
const rows = ref([])
const loading = ref(false)
const saving = ref(false)
const current = ref(null)
const viewOpen = ref(false)
const replyOpen = ref(false)
const reviewOpen = ref(false)
const q = reactive({ status: '', enterpriseName: '', species: '' })
const replyForm = reactive({ reply: '', rectifyDate: '', proofFile: '' })
const reviewForm = reactive({ approved: true, opinion: '', reviewDate: '' })

const statusOpts = ['PENDING', 'RECTIFYING', 'REVIEW', 'CLOSED']
function statusLabel(s) {
  return ({ PENDING: '待接收', RECTIFYING: '整改中', REVIEW: '待复查', CLOSED: '已闭环', REJECTED: '已驳回' })[s] || s
}

const filtered = computed(() =>
  rows.value.filter((r) => {
    if (q.status && r.status !== q.status) return false
    if (q.enterpriseName && !String(r.enterpriseName || '').includes(q.enterpriseName)) return false
    if (q.species && !String(r.species || '').includes(q.species)) return false
    return true
  }),
)

function canAccept(row) {
  return !isGov.value && row.status === 'PENDING'
}
function canReply(row) {
  return !isGov.value && (row.status === 'RECTIFYING' || row.status === 'PENDING')
}
function canReview(row) {
  return isGov.value && row.status === 'REVIEW'
}

async function load() {
  loading.value = true
  try {
    const res = await http.get('/quality/rectifications')
    rows.value = res.data || []
  } finally {
    loading.value = false
  }
}
function reset() {
  q.status = ''
  q.enterpriseName = ''
  q.species = ''
  load()
}
function openView(row) {
  current.value = row
  viewOpen.value = true
}
async function doAccept(row) {
  await http.post(`/quality/rectifications/${row.id}/accept`)
  ElMessage.success('已接收，进入整改中')
  load()
}
function openReply(row) {
  current.value = row
  replyForm.reply = ''
  replyForm.rectifyDate = new Date().toISOString().slice(0, 10)
  replyForm.proofFile = ''
  replyOpen.value = true
}
async function doReply() {
  if (!replyForm.reply) {
    ElMessage.warning('请填写整改说明')
    return
  }
  saving.value = true
  try {
    await http.post(`/quality/rectifications/${current.value.id}/reply`, { ...replyForm })
    ElMessage.success('已提交整改，等待区县复查')
    replyOpen.value = false
    load()
  } finally {
    saving.value = false
  }
}
function openReview(row) {
  current.value = row
  reviewForm.approved = true
  reviewForm.opinion = ''
  reviewForm.reviewDate = new Date().toISOString().slice(0, 10)
  reviewOpen.value = true
}
async function doReview() {
  saving.value = true
  try {
    await http.post(`/quality/rectifications/${current.value.id}/review`, { ...reviewForm })
    ElMessage.success(reviewForm.approved ? '验收通过，已闭环' : '已驳回，企业需继续整改')
    reviewOpen.value = false
    load()
  } finally {
    saving.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.bar { display:flex; justify-content:space-between; align-items:center; gap:12px; flex-wrap:wrap; margin-bottom:12px; }
.actions { display:flex; gap:8px; }
.filters { margin-bottom:8px; }
.muted { color:#888; font-size:12px; margin-top:4px; }
</style>
