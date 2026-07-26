<template>
  <div class="page-card">
    <div class="bar">
      <h2 class="page-title">{{ title }}</h2>
      <div class="actions">
        <el-button @click="load">查询</el-button>
        <el-button @click="reset">重置</el-button>
        <el-button v-if="canCreate" type="primary" @click="openCreate">{{ createLabel }}</el-button>
        <el-button @click="doExport">导出</el-button>
      </div>
    </div>
    <el-form inline class="filters">
      <el-form-item label="年度"><el-input v-model="q.year" clearable style="width:100px" /></el-form-item>
      <el-form-item label="季度">
        <el-select v-model="q.quarter" clearable style="width:100px">
          <el-option v-for="x in ['Q1','Q2','Q3','Q4']" :key="x" :label="x" :value="x" />
        </el-select>
      </el-form-item>
      <el-form-item label="级别">
        <el-select v-model="q.level" clearable style="width:100px">
          <el-option v-for="x in ['国家级','省级','市级','区级']" :key="x" :label="x" :value="x" />
        </el-select>
      </el-form-item>
      <el-form-item label="品种"><el-input v-model="q.species" clearable style="width:120px" /></el-form-item>
      <el-button type="primary" @click="load">查询</el-button>
    </el-form>
    <el-table :data="filtered" stripe v-loading="loading">
      <el-table-column prop="year" label="年度" width="80" />
      <el-table-column prop="quarter" label="季度" width="80" />
      <el-table-column prop="level" label="级别" width="90" />
      <el-table-column prop="enterpriseName" label="抽检主体" min-width="140" />
      <el-table-column prop="species" label="品种" width="100" />
      <el-table-column prop="sampleCount" label="样品数" width="90" />
      <el-table-column prop="labName" label="检测机构" min-width="120" />
      <el-table-column prop="result" label="检测结果" width="100" />
      <el-table-column prop="unqualified" label="不合格指标" min-width="110" />
      <el-table-column prop="reportFile" label="检测报告" width="110" />
      <el-table-column prop="inspectedAt" label="抽检日期" min-width="150" />
      <el-table-column prop="status" label="状态" width="100" />
      <el-table-column label="操作" width="160" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="viewRow(row)">查看</el-button>
          <el-button v-if="row.result==='UNQUALIFIED' && canIssue" link type="warning" @click="issueRect(row)">下发整改</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dlg" :title="createLabel" width="560px" destroy-on-close>
      <el-form :model="form" label-width="100px">
        <el-form-item label="抽检主体"><el-input v-model="form.enterpriseName" placeholder="示范养殖场" /></el-form-item>
        <el-form-item label="抽检品种"><el-input v-model="form.species" placeholder="大鲵" /></el-form-item>
        <el-form-item label="样品数"><el-input-number v-model="form.sampleCount" :min="1" /></el-form-item>
        <el-form-item label="检测机构"><el-input v-model="form.labName" placeholder="区县水产检测中心" /></el-form-item>
        <el-form-item label="年度"><el-input-number v-model="form.year" :min="2020" /></el-form-item>
        <el-form-item label="季度">
          <el-select v-model="form.quarter" style="width:100%">
            <el-option v-for="x in ['Q1','Q2','Q3','Q4']" :key="x" :label="x" :value="x" />
          </el-select>
        </el-form-item>
        <el-form-item label="级别">
          <el-select v-model="form.level" style="width:100%">
            <el-option v-for="x in ['国家级','省级','市级','区级']" :key="x" :label="x" :value="x" />
          </el-select>
        </el-form-item>
        <el-form-item label="检测结果">
          <el-select v-model="form.result" style="width:100%">
            <el-option label="合格 QUALIFIED" value="QUALIFIED" />
            <el-option label="不合格 UNQUALIFIED" value="UNQUALIFIED" />
            <el-option label="待检 PENDING" value="PENDING" />
          </el-select>
        </el-form-item>
        <el-form-item label="检测报告">
          <el-upload :auto-upload="false" :limit="1" accept=".pdf,.jpg,.png" @change="onFile">
            <el-button>选择报告文件</el-button>
          </el-upload>
          <div class="muted">演示：仅记录文件名，不上传对象存储</div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dlg=false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="save">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import http from '@/api/http'
import { useAuthStore } from '@/stores/auth'

const props = defineProps({
  title: { type: String, default: '质量抽检' },
  api: { type: String, default: '/quality/inspections' },
  mode: { type: String, default: 'gov' }, // gov | self | readonly
})

const auth = useAuthStore()
const rows = ref([])
const loading = ref(false)
const dlg = ref(false)
const saving = ref(false)
const q = reactive({ year: '', quarter: '', level: '', species: '' })
const form = reactive({
  enterpriseName: '示范养殖场',
  species: '大鲵',
  sampleCount: 3,
  labName: '区县水产检测中心',
  year: 2026,
  quarter: 'Q2',
  level: '区级',
  result: 'QUALIFIED',
  reportFile: '',
  enterpriseId: 1,
})

const canCreate = computed(() => props.mode !== 'readonly')
const canIssue = computed(() => auth.portal === 'GOV')
const createLabel = computed(() => (props.mode === 'self' ? '新建自检' : '新增抽检'))

const filtered = computed(() =>
  rows.value.filter((r) => {
    if (q.year && String(r.year) !== String(q.year)) return false
    if (q.quarter && r.quarter !== q.quarter) return false
    if (q.level && r.level !== q.level) return false
    if (q.species && !String(r.species || '').includes(q.species)) return false
    return true
  }),
)

async function load() {
  loading.value = true
  try {
    const res = await http.get(props.api)
    let list = res.data?.list || res.data || []
    if (!Array.isArray(list)) list = []
    rows.value = list.map((r) => ({
      ...r,
      sampleCount: r.sampleCount ?? 3,
      reportFile: r.reportFile || (r.result === 'UNQUALIFIED' ? '不合格报告.pdf' : '检测报告.pdf'),
      unqualified: r.unqualified || (r.result === 'UNQUALIFIED' ? '指标异常' : '—'),
    }))
  } finally {
    loading.value = false
  }
}

function reset() {
  Object.keys(q).forEach((k) => (q[k] = ''))
  load()
}

function openCreate() {
  dlg.value = true
}

function onFile(file) {
  form.reportFile = file?.name || file?.raw?.name || '检测报告.pdf'
}

async function save() {
  saving.value = true
  try {
    const api = props.mode === 'self' ? '/quality/self-checks' : '/quality/inspections'
    const body =
      props.mode === 'self'
        ? {
            title: `${form.species}自主监管`,
            result: form.result,
            pondId: 1,
          }
        : {
            title: `${form.year}${form.quarter}${form.species}抽检`,
            enterpriseId: form.enterpriseId,
            enterpriseName: form.enterpriseName,
            species: form.species,
            year: form.year,
            quarter: form.quarter,
            level: form.level,
            result: form.result,
            labName: form.labName,
          }
    await http.post(api, body)
    ElMessage.success('已保存' + (form.reportFile ? ` · 报告 ${form.reportFile}` : ''))
    dlg.value = false
    load()
  } finally {
    saving.value = false
  }
}

function viewRow(row) {
  ElMessageBox.alert(
    `<pre style="white-space:pre-wrap;font-size:12px">${JSON.stringify(row, null, 2)}</pre>`,
    '抽检详情',
    { dangerouslyUseHTMLString: true, customClass: 'wide-msg' },
  )
}

async function issueRect(row) {
  await http.post(`/quality/inspections/${row.id}/issue-rect`)
  ElMessage.success('已下发不合格整改，企业可在质量整改中处理')
  load()
}

function doExport() {
  const cols = ['year', 'quarter', 'level', 'enterpriseName', 'species', 'result', 'status']
  const lines = [cols.join(',')]
  filtered.value.forEach((r) => lines.push(cols.map((c) => `"${r[c] ?? ''}"`).join(',')))
  const blob = new Blob(['\ufeff' + lines.join('\n')], { type: 'text/csv;charset=utf-8' })
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob)
  a.download = `${props.title}.csv`
  a.click()
  ElMessage.success('已导出')
}

onMounted(load)
</script>

<style scoped>
.bar { display:flex; justify-content:space-between; align-items:center; gap:12px; flex-wrap:wrap; margin-bottom:12px; }
.actions { display:flex; gap:8px; flex-wrap:wrap; }
.filters { margin-bottom:8px; }
.muted { color:#888; font-size:12px; margin-top:4px; }
</style>
