<template>
  <div class="page-card">
    <div class="bar">
      <h2 class="page-title">{{ title }}</h2>
      <div class="actions">
        <el-button @click="load">查询</el-button>
        <el-button @click="reset">重置</el-button>
        <el-button type="primary" @click="openCreate">新建</el-button>
        <el-button @click="exportCsv">导出</el-button>
        <el-button type="warning" plain @click="showUnfiled">未备案主体</el-button>
      </div>
    </div>
    <el-form inline class="filters">
      <el-form-item label="养殖主体"><el-input v-model="q.enterpriseName" clearable style="width:150px" /></el-form-item>
      <el-form-item label="状态">
        <el-select v-model="q.status" clearable style="width:120px">
          <el-option label="草稿" value="DRAFT" />
          <el-option label="已提交" value="SUBMITTED" />
          <el-option label="已备案" value="FILED" />
          <el-option label="已驳回" value="REJECTED" />
        </el-select>
      </el-form-item>
    </el-form>
    <el-table :data="filtered" stripe v-loading="loading">
      <el-table-column prop="county" label="区县" width="90" />
      <el-table-column prop="township" label="乡镇" width="100" />
      <el-table-column prop="village" label="村" width="80" />
      <el-table-column prop="enterpriseName" label="养殖主体" min-width="130" />
      <el-table-column prop="zone" label="尾水区" min-width="110" />
      <el-table-column prop="planTime" label="尾水计划排放时间" min-width="140" />
      <el-table-column prop="fileDate" label="备案日期" width="110" />
      <el-table-column prop="status" label="状态" width="90">
        <template #default="{ row }"><el-tag size="small">{{ statusLabel(row.status) }}</el-tag></template>
      </el-table-column>
      <el-table-column label="操作" width="260" fixed="right">
        <template #default="{ row }">
          <el-button v-if="row.status==='DRAFT' || row.status==='REJECTED'" link type="primary" @click="openEdit(row)">编辑</el-button>
          <el-button v-if="row.status==='DRAFT' || row.status==='REJECTED'" link type="warning" @click="submit(row)">提交</el-button>
          <el-button v-if="row.status==='SUBMITTED'" link type="success" @click="file(row)">备案</el-button>
          <el-button v-if="row.status==='SUBMITTED'" link type="danger" @click="reject(row)">驳回</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dlg" :title="dlgMode === 'edit' ? '编辑尾水排放计划' : '新建尾水排放计划'" width="520px" destroy-on-close>
      <el-form :model="form" label-width="110px">
        <el-form-item label="计划标题"><el-input v-model="form.title" /></el-form-item>
        <el-form-item label="养殖主体">
          <el-select v-model="form.enterpriseId" style="width:100%">
            <el-option v-for="e in enterprises" :key="e.id" :label="e.name" :value="e.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="联系人"><el-input v-model="form.contactName" /></el-form-item>
        <el-form-item label="联系方式"><el-input v-model="form.contactPhone" /></el-form-item>
        <el-form-item label="排放开始"><el-date-picker v-model="form.dischargeStart" type="date" value-format="YYYY-MM-DD" style="width:100%" /></el-form-item>
        <el-form-item label="排放结束"><el-date-picker v-model="form.dischargeEnd" type="date" value-format="YYYY-MM-DD" style="width:100%" /></el-form-item>
        <el-form-item label="计划水量(m³)"><el-input-number v-model="form.volume" :min="0" style="width:100%" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dlg=false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="save">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="unfiledOpen" title="未备案主体" width="520px">
      <el-table :data="unfiled" size="small">
        <el-table-column prop="name" label="主体" />
        <el-table-column prop="species" label="品种" width="100" />
        <el-table-column prop="areaMu" label="面积(亩)" width="100" />
      </el-table>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import http from '@/api/http'

defineProps({ title: { type: String, default: '尾水排放计划' } })

const rows = ref([])
const enterprises = ref([{ id: 1, name: '示范养殖场' }])
const unfiled = ref([])
const loading = ref(false)
const saving = ref(false)
const dlg = ref(false)
const dlgMode = ref('create')
const editingId = ref(null)
const unfiledOpen = ref(false)
const q = reactive({ enterpriseName: '', status: '' })
const form = reactive({
  title: '2026年7月尾水排放计划',
  enterpriseId: 1,
  contactName: '张示范',
  contactPhone: '13800001111',
  dischargeStart: '2026-07-01',
  dischargeEnd: '2026-07-31',
  volume: 120,
})

function statusLabel(s) {
  return ({ DRAFT: '草稿', SUBMITTED: '已提交', FILED: '已备案', REJECTED: '已驳回' })[s] || s
}
const filtered = computed(() =>
  rows.value.filter((r) => {
    if (q.status && r.status !== q.status) return false
    if (q.enterpriseName && !String(r.enterpriseName || '').includes(q.enterpriseName)) return false
    return true
  }),
)

function resetFormDefaults() {
  form.title = '2026年7月尾水排放计划'
  form.enterpriseId = enterprises.value[0]?.id || 1
  form.contactName = '张示范'
  form.contactPhone = '13800001111'
  form.dischargeStart = '2026-07-01'
  form.dischargeEnd = '2026-07-31'
  form.volume = 120
}

async function load() {
  loading.value = true
  try {
    const res = await http.get('/effluent/plans')
    rows.value = res.data || []
    try {
      const er = await http.get('/party/enterprises')
      const list = er.data?.list || er.data || []
      if (Array.isArray(list) && list.length) enterprises.value = list.map((e) => ({ id: e.id, name: e.name }))
    } catch {
      /* keep default */
    }
  } finally {
    loading.value = false
  }
}
function reset() {
  q.enterpriseName = ''
  q.status = ''
  load()
}
function openCreate() {
  dlgMode.value = 'create'
  editingId.value = null
  resetFormDefaults()
  dlg.value = true
}
function openEdit(row) {
  dlgMode.value = 'edit'
  editingId.value = row.id
  form.title = row.title || ''
  form.enterpriseId = row.enterpriseId || enterprises.value[0]?.id || 1
  form.contactName = row.contactName && row.contactName !== '-' ? row.contactName : ''
  form.contactPhone = row.contactPhone && row.contactPhone !== '-' ? row.contactPhone : ''
  form.dischargeStart = row.planTime || row.dischargeStart || ''
  form.dischargeEnd = row.dischargeEnd || ''
  form.volume = row.volume ?? 0
  dlg.value = true
}
async function save() {
  saving.value = true
  try {
    const body = { ...form }
    if (dlgMode.value === 'edit' && editingId.value) {
      await http.put(`/effluent/plans/${editingId.value}`, body)
      ElMessage.success('计划已更新')
    } else {
      await http.post('/effluent/plans', body)
      ElMessage.success('计划已创建')
    }
    dlg.value = false
    load()
  } finally {
    saving.value = false
  }
}
async function submit(row) {
  await http.post(`/effluent/plans/${row.id}/submit`)
  ElMessage.success('已提交备案')
  load()
}
async function file(row) {
  await http.post(`/effluent/plans/${row.id}/file`)
  ElMessage.success('已备案')
  load()
}
async function reject(row) {
  await http.post(`/effluent/plans/${row.id}/reject`)
  ElMessage.success('已驳回')
  load()
}
async function showUnfiled() {
  const res = await http.get('/effluent/plans/unfiled-enterprises')
  unfiled.value = res.data || []
  unfiledOpen.value = true
}
function exportCsv() {
  const cols = ['county', 'township', 'village', 'enterpriseName', 'zone', 'planTime', 'fileDate', 'status']
  const lines = [cols.join(',')]
  filtered.value.forEach((r) => lines.push(cols.map((c) => `"${r[c] ?? ''}"`).join(',')))
  const blob = new Blob(['\ufeff' + lines.join('\n')], { type: 'text/csv;charset=utf-8' })
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob)
  a.download = '尾水排放计划.csv'
  a.click()
}

onMounted(load)
</script>

<style scoped>
.bar { display:flex; justify-content:space-between; align-items:center; gap:8px; flex-wrap:wrap; margin-bottom:12px; }
.actions { display:flex; gap:8px; flex-wrap:wrap; }
.filters { margin-bottom:8px; }
</style>
