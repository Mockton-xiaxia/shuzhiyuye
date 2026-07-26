<template>
  <div class="page-card">
    <div class="bar">
      <h2 class="page-title">{{ title }}</h2>
      <div class="actions">
        <el-button @click="load">查询</el-button>
        <el-button @click="reset">重置</el-button>
        <el-button v-if="isEnt" type="primary" @click="openCreate">新增申请</el-button>
      </div>
    </div>
    <el-form inline class="filters">
      <el-form-item label="状态">
        <el-select v-model="q.status" clearable style="width:130px">
          <el-option v-for="s in statusOpts" :key="s" :label="statusLabel(s)" :value="s" />
        </el-select>
      </el-form-item>
      <el-form-item v-if="isGov" label="养殖主体"><el-input v-model="q.enterpriseName" clearable style="width:150px" /></el-form-item>
    </el-form>

    <el-table :data="filtered" stripe v-loading="loading">
      <el-table-column v-if="isGov" prop="enterpriseName" label="养殖主体" min-width="130" />
      <el-table-column v-if="isGov" prop="regionName" label="所属区域" width="90" />
      <el-table-column prop="species" label="申请品种" width="100" />
      <el-table-column prop="brand" label="品种品牌" width="110" />
      <el-table-column prop="applyQty" label="申请数量" width="90" />
      <el-table-column prop="applyDate" label="申请日期" width="120" />
      <el-table-column prop="status" label="状态" width="100">
        <template #default="{ row }"><el-tag size="small">{{ statusLabel(row.status) }}</el-tag></template>
      </el-table-column>
      <el-table-column label="操作" width="240" fixed="right">
        <template #default="{ row }">
          <el-button v-if="isGov && row.status==='PENDING'" link type="success" @click="audit(row, true)">通过</el-button>
          <el-button v-if="isGov && row.status==='PENDING'" link type="danger" @click="audit(row, false)">驳回</el-button>
          <el-button v-if="isGov && row.status==='APPROVED'" link type="primary" @click="issue(row)">分发标识</el-button>
          <el-button v-if="isEnt && (row.status==='DRAFT' || row.status==='REJECTED')" link type="warning" @click="submit(row)">提交审核</el-button>
          <span v-if="row.status==='ISSUED'" class="done">已分发</span>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dlg" title="标识申请" width="440px" destroy-on-close>
      <el-form :model="form" label-width="100px">
        <el-form-item label="申请品种"><el-input v-model="form.species" placeholder="大鲵" /></el-form-item>
        <el-form-item label="品种品牌"><el-input v-model="form.brand" placeholder="本地大鲵" /></el-form-item>
        <el-form-item label="申请数量"><el-input-number v-model="form.applyQty" :min="1" :max="9999" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dlg=false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="save">提交申请</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import http from '@/api/http'
import { useAuthStore } from '@/stores/auth'

defineProps({ title: { type: String, default: '标识申请' } })

const auth = useAuthStore()
const isGov = computed(() => auth.portal === 'GOV' || auth.portal === 'BOTH')
const isEnt = computed(() => auth.portal === 'ENT' || auth.portal === 'BOTH')
const rows = ref([])
const loading = ref(false)
const saving = ref(false)
const dlg = ref(false)
const q = reactive({ status: '', enterpriseName: '' })
const form = reactive({ species: '大鲵', brand: '本地大鲵', applyQty: 10, batchId: 1 })
const statusOpts = ['PENDING', 'APPROVED', 'REJECTED', 'ISSUED', 'DRAFT']

function statusLabel(s) {
  return ({ DRAFT: '草稿', PENDING: '待审核', APPROVED: '已通过', REJECTED: '已驳回', ISSUED: '已分发' })[s] || s
}

const filtered = computed(() =>
  rows.value.filter((r) => {
    if (q.status && r.status !== q.status) return false
    if (q.enterpriseName && !String(r.enterpriseName || '').includes(q.enterpriseName)) return false
    return true
  }),
)

async function load() {
  loading.value = true
  try {
    const res = await http.get('/trace/applies')
    rows.value = res.data || []
  } finally {
    loading.value = false
  }
}
function reset() {
  q.status = ''
  q.enterpriseName = ''
  load()
}
function openCreate() {
  dlg.value = true
}
async function save() {
  saving.value = true
  try {
    await http.post('/trace/applies', { ...form })
    ElMessage.success('已提交，等待区县审核')
    dlg.value = false
    load()
  } finally {
    saving.value = false
  }
}
async function submit(row) {
  await http.post(`/trace/applies/${row.id}/submit`)
  ElMessage.success('已提交审核')
  load()
}
async function audit(row, approved) {
  let opinion = approved ? '同意' : '材料不全'
  if (!approved) {
    const { value } = await ElMessageBox.prompt('驳回意见', '标识审核驳回')
    opinion = value || opinion
  }
  await http.post(`/trace/applies/${row.id}/audit`, { approved, opinion })
  ElMessage.success(approved ? '已通过' : '已驳回')
  load()
}
async function issue(row) {
  const res = await http.post(`/trace/applies/${row.id}/issue`)
  const n = res.data?.codes?.length || row.applyQty
  ElMessage.success(`已分发 ${n} 枚标识码`)
  load()
}

onMounted(load)
</script>

<style scoped>
.bar { display:flex; justify-content:space-between; align-items:center; margin-bottom:12px; flex-wrap:wrap; gap:8px; }
.actions { display:flex; gap:8px; }
.filters { margin-bottom:8px; }
.done { color:#67c23a; font-size:12px; }
</style>
