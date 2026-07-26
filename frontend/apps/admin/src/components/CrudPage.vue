<template>
  <div class="page-card">
    <div class="bar">
      <h2 class="page-title">{{ title }}</h2>
      <div class="actions">
        <el-button v-if="has('query')" @click="load">查询</el-button>
        <el-button v-if="has('reset')" @click="reset">重置</el-button>
        <el-button v-if="has('create')" type="primary" @click="openCreate">{{ createLabel }}</el-button>
        <el-button v-if="has('import')" @click="triggerImport">导入</el-button>
        <el-button v-if="has('export')" @click="doExport">导出</el-button>
        <el-button v-if="has('batchDelete')" type="danger" plain @click="doBatchDelete">批量删除</el-button>
        <input ref="fileRef" type="file" accept=".csv,text/csv" style="display:none" @change="onImportFile" />
        <slot name="extra-actions" />
      </div>
    </div>
    <el-form v-if="filters.length" inline class="filters" @submit.prevent>
      <el-form-item v-for="f in filters" :key="f.prop" :label="f.label">
        <el-input v-model="query[f.prop]" clearable :placeholder="f.placeholder || f.label" style="width:160px" />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="load">查询</el-button>
      </el-form-item>
    </el-form>
    <el-table :data="rows" stripe v-loading="loading" @selection-change="sel=$event">
      <el-table-column v-if="has('batchDelete')" type="selection" width="48" />
      <el-table-column v-for="c in columns" :key="c.prop" :prop="c.prop" :label="c.label" :min-width="c.width || 110" show-overflow-tooltip>
        <template #default="{ row }">
          <template v-if="isFileColumn(c) && fileHref(row, c)">
            <el-link type="primary" :href="fileHref(row, c)" target="_blank">{{ cellText(row, c) }}</el-link>
          </template>
          <template v-else>{{ cellText(row, c) }}</template>
        </template>
      </el-table-column>
      <el-table-column label="操作" :width="rowActionWidth" fixed="right">
        <template #default="{ row }">
          <el-button v-for="ra in actionsForRow(row)" :key="ra.label" link type="primary" @click="ra.onClick(row)">{{ ra.label }}</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="formDlg" :title="formTitle" width="640px" destroy-on-close>
      <el-form :model="form" label-width="108px">
        <el-form-item v-for="f in dialogFields" :key="f.prop" :label="f.label" :required="!!f.required">
          <el-input
            v-if="!f.type || f.type === 'input'"
            v-model="form[f.prop]"
            :placeholder="f.placeholder || f.label"
          />
          <el-input
            v-else-if="f.type === 'password'"
            v-model="form[f.prop]"
            type="password"
            show-password
            :placeholder="f.placeholder || f.label"
          />
          <el-input
            v-else-if="f.type === 'textarea'"
            v-model="form[f.prop]"
            type="textarea"
            :rows="3"
            :placeholder="f.placeholder || f.label"
          />
          <el-date-picker
            v-else-if="f.type === 'date'"
            v-model="form[f.prop]"
            type="date"
            value-format="YYYY-MM-DD"
            style="width:100%"
          />
          <el-select v-else-if="f.type === 'select'" v-model="form[f.prop]" style="width:100%" clearable :placeholder="f.placeholder || '请选择'">
            <el-option v-for="o in selectOptions(f)" :key="String(o.value)" :label="o.label" :value="o.value" />
          </el-select>
          <div v-else-if="f.type === 'upload'" class="upload-row">
            <el-upload
              :show-file-list="false"
              :accept="f.accept || '.pdf,.doc,.docx,.png,.jpg'"
              :http-request="(opt) => onUpload(opt, f)"
            >
              <el-button type="primary" plain>上传文件</el-button>
            </el-upload>
            <span v-if="uploadDisplay(f)" class="upload-name">{{ uploadDisplay(f) }}</span>
            <el-link v-if="form[f.prop]" type="primary" :href="resolveUrl(form[f.prop])" target="_blank">预览</el-link>
          </div>
          <el-input v-else v-model="form[f.prop]" :placeholder="f.label" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="formDlg=false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="submitForm">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="viewDlg" title="查看详情" width="640px" destroy-on-close>
      <el-descriptions v-if="viewRow" :column="1" border>
        <el-descriptions-item v-for="c in viewColumns" :key="c.prop" :label="c.label">
          <template v-if="isFileColumn(c) && fileHref(viewRow, c)">
            <el-link type="primary" :href="fileHref(viewRow, c)" target="_blank">{{ cellText(viewRow, c) }}</el-link>
          </template>
          <template v-else>{{ cellText(viewRow, c) }}</template>
        </el-descriptions-item>
      </el-descriptions>
      <template #footer>
        <el-button type="primary" @click="viewDlg=false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'
import http from '@/api/http'
import { useAuthStore } from '@/stores/auth'

const props = defineProps({
  title: { type: String, required: true },
  api: { type: String, required: true },
  columns: { type: Array, default: () => [] },
  buttons: { type: Array, default: () => ['query', 'reset', 'create'] },
  filters: { type: Array, default: () => [] },
  createFields: { type: Array, default: () => [] },
  rowActions: { type: Function, default: null },
  rowActionWidth: { type: Number, default: 260 },
  transform: { type: Function, default: null },
  createLabel: { type: String, default: '新增' },
  readonly: { type: Boolean, default: false },
})

const rows = ref([])
const loading = ref(false)
const sel = ref([])
const query = reactive({})
const formDlg = ref(false)
const viewDlg = ref(false)
const viewRow = ref(null)
const formMode = ref('create')
const editingId = ref(null)
const saving = ref(false)
const form = reactive({})
const fileRef = ref(null)
const fieldOptions = reactive({})

/** 维护型 API：编辑后会真正持久化（专用 PUT 或 feature/update 已映射） */
const EDITABLE_APIS = new Set([
  '/system/users',
  '/quality/policies',
  '/effluent/policies',
  '/quality/labs',
  '/effluent/waters',
  '/supply/listings',
  '/supply/markets',
  '/supply/prices',
  '/cms/articles',
  '/cms/categories',
  '/cms/videos',
  '/inputs/items',
  '/inputs/suppliers',
  '/party/staffs',
  '/breeding/activities',
  '/breeding/batches',
  '/breeding/sales',
  '/ledger/customers',
  '/ledger/contracts',
  '/ledger/after-sales',
  '/ledger/entries',
  '/wms/warehouses',
  '/wms/stocks',
  '/wms/inbounds',
  '/wms/outbounds',
  '/wms/stocktakes',
  '/circulation/transports',
  '/iot/rules',
  '/iot/cameras',
  '/disease/alerts',
  '/effluent/patrols',
  '/specialty/disease-tests',
])

function apiBasePath() {
  return (props.api || '').split('?')[0]
}

function isEditableApi(path = apiBasePath()) {
  return EDITABLE_APIS.has(path)
}

const dialogFields = computed(() =>
  props.createFields.length
    ? props.createFields
    : props.columns.map((c) => ({ prop: c.prop, label: c.label, type: fieldTypeGuess(c) })),
)

const viewColumns = computed(() => {
  const cols = [...props.columns]
  if (!cols.find((c) => c.prop === 'id')) cols.unshift({ prop: 'id', label: '编号' })
  return cols
})

const formTitle = computed(() => {
  if (formMode.value === 'edit') return '编辑'
  return props.createLabel
})

function fieldTypeGuess(c) {
  const p = c.prop || ''
  if (p.includes('file') || p.includes('File') || p.includes('Url') && p.toLowerCase().includes('file')) return 'upload'
  if (p.includes('Date') || p.includes('date')) return 'date'
  return 'input'
}

function isFileColumn(c) {
  const p = c.prop || ''
  return p.includes('file') || p.includes('File') || p === 'fileUrl' || p === 'fileName'
}

function cellText(row, c) {
  const v = row[c.prop]
  if (v == null || v === '') return '-'
  return String(v)
}

function resolveUrl(url) {
  if (!url) return ''
  if (url.startsWith('http')) return url
  if (url.startsWith('/uploads/')) return url
  return url
}

function fileHref(row, c) {
  const url = row.fileUrl || row.file_url || (c.prop === 'fileName' ? row.fileUrl : null)
  if (url) return resolveUrl(url)
  if (String(row[c.prop] || '').match(/\.(pdf|doc|docx|png|jpe?g)$/i) && row.fileUrl) return resolveUrl(row.fileUrl)
  return ''
}

function uploadDisplay(f) {
  const nameProp = f.fileNameProp || 'fileName'
  return form[nameProp] || (form[f.prop] ? '已上传' : '')
}

function has(b) {
  if (props.readonly && ['create', 'import', 'batchDelete'].includes(b)) return false
  return props.buttons.includes(b)
}

async function ensureFieldOptions(fields = dialogFields.value) {
  for (const f of fields) {
    if (f.type !== 'select' || !f.optionsApi) continue
    if (fieldOptions[f.prop]?.length) continue
    try {
      const params = f.optionsParams || (f.optionsApi === '/party/enterprises' ? { page: 1, size: 500 } : undefined)
      const res = await http.get(f.optionsApi, { params })
      let data = res.data
      if (data?.list) data = data.list
      if (!Array.isArray(data)) data = []
      const labelKey = f.optionLabel || 'name'
      const valueKey = f.optionValue || 'id'
      fieldOptions[f.prop] = data.map((row) => ({
        label: row[labelKey] ?? row.name ?? String(row.id),
        value: row[valueKey] ?? row.id,
      }))
    } catch {
      fieldOptions[f.prop] = []
    }
  }
}

function selectOptions(f) {
  if (f.options?.length) return f.options
  return fieldOptions[f.prop] || []
}

function reset() {
  Object.keys(query).forEach((k) => (query[k] = ''))
  load()
}

function splitApi(api) {
  const [path, qs] = (api || '').split('?')
  const fixed = {}
  if (qs) new URLSearchParams(qs).forEach((v, k) => { fixed[k] = v })
  return { path, fixed }
}

async function load() {
  loading.value = true
  try {
    const { path, fixed } = splitApi(props.api)
    const res = await http.get(path, { params: { ...fixed, ...query } })
    let data = res.data
    if (data && Array.isArray(data.list)) data = data.list
    if (!Array.isArray(data)) data = []
    rows.value = props.transform ? props.transform(data) : data
  } catch {
    rows.value = []
  } finally {
    loading.value = false
  }
}

function normalizeCreateBody(apiPath, raw, q) {
  const body = { ...raw }
  const numericProps = new Set([
    'enterpriseId', 'pondId', 'batchId', 'labId', 'warehouseId', 'deviceId', 'orderId',
    'waterBodyId', 'parentEnterpriseId', 'regionId', 'pilotId', 'itemId', 'supplierId',
    'year', 'sampleCount', 'qty', 'amount', 'volume', 'weightKg', 'price', 'threshold',
    'lng', 'lat', 'areaMu', 'flightHours', 'violationCount', 'planHours', 'actualHours',
    'sortNo', 'unitPrice', 'applyQty', 'withdrawalDays', 'paid', 'totalAmount',
  ])
  const displayOnly = new Set([
    'roleName', 'orgName', 'projectName', 'source', 'createdAt', 'updatedAt',
    'regionName', 'enterpriseName', 'labType', 'subjectType', 'inspectedAt',
    'fileName', 'scope', 'customerName', 'supplierName',
    'transportNo', 'applyNo', 'applyDate', 'applicant', 'genDate', 'saleDate',
  ])
  if (apiPath !== '/effluent/waters') {
    displayOnly.add('zone')
  }
  const stringProps = new Set([
    'mobile', 'phone', 'contactPhone', 'idCard', 'plateNo', 'username', 'deviceSerial',
    'appKey', 'appSecret', 'orderNo', 'batchNo', 'code', 'transportNo', 'planMonth',
    'dischargeStart', 'dischargeEnd', 'publishDate', 'month', 'plateNo',
  ])

  for (const k of Object.keys(body)) {
    if (displayOnly.has(k)) {
      delete body[k]
      continue
    }
    const v = body[k]
    if (v === '' || v == null) continue
    if (stringProps.has(k) || k.endsWith('Phone') || k.endsWith('No') && k !== 'sortNo') {
      body[k] = String(v)
      continue
    }
    if (numericProps.has(k) || (k.endsWith('Id') && k !== 'idCard')) {
      if (/^-?\d+(\.\d+)?$/.test(String(v))) body[k] = Number(v)
    }
  }
  if (apiPath.includes('/quality/policies') || apiPath.includes('/effluent/policies')) {
    if (!body.publishDate) body.publishDate = new Date().toISOString().slice(0, 10)
    if (body.fileName && !body.fileUrl) body.fileUrl = `/uploads/${body.fileName}`
  }
  if (apiPath.includes('/ledger/entries')) {
    if (!body.title) body.title = body.month || body.name || '手工记账'
    if (!body.entryType) body.entryType = 'EXPENSE'
    if (body.amount == null) body.amount = Number(body.total || body.feed || body.other || 0)
    if (body.month && !body.occurredAt) body.occurredAt = `${String(body.month).slice(0, 7)}-01`
  }
  if (apiPath.includes('/ledger/budgets') && !body.month) body.month = '2026-07'
  if (apiPath.includes('/effluent/patrols')) {
    if (!body.title) body.title = '巡检记录'
    if (!body.enterpriseId) body.enterpriseId = 1
    if (!body.result) body.result = '正常'
  }
  if (apiPath.includes('/wms/inbounds') || apiPath.includes('/wms/outbounds')) {
    if (q.category) body.category = q.category
    if (!body.qty) body.qty = Number(body.qty || 1)
    if (!body.itemName && body.name) body.itemName = body.name
    if (apiPath.includes('/wms/inbounds') && q.category === 'PRODUCT') body.source = body.source || 'CATCH'
  }
  if (apiPath.includes('/ledger/contracts') && body.amount == null) body.amount = 0
  if (apiPath.includes('/ledger/after-sales') && !body.title) body.title = body.content || '售后反馈'
  if (apiPath.includes('/iot/commands')) {
    if (!body.deviceId) body.deviceId = 1
    if (!body.command) body.command = body.title || 'AERATOR_ON'
  }
  if (apiPath.includes('/circulation/transports') && !body.plateNo) body.plateNo = body.transportNo || '陕F·DEMO'
  if (apiPath.includes('/trace/applies')) {
    if (!body.species) body.species = body.applySpecies || '大鲵'
    if (!body.brand) body.brand = body.brandName || '本地大鲵'
  }
  if (apiPath.includes('/system/users')) {
    if (body.mobile != null && body.mobile !== '') body.mobile = String(body.mobile)
    for (const k of ['orgName', 'email', 'address', 'roleName', 'projectName', 'source', 'id']) {
      delete body[k]
    }
    if (formMode.value === 'edit') {
      if (!body.password) delete body.password
    } else if (!body.password) {
      body.password = '123456'
    }
    if (!body.roleCode) delete body.roleCode
    if (body.userType === 'COUNTY') delete body.enterpriseId
    else if (body.enterpriseId === '' || body.enterpriseId == null) delete body.enterpriseId
  }
  return body
}

const DIRECT_PUT_APIS = new Set([
  '/system/users',
  '/quality/policies',
  '/effluent/policies',
  '/party/enterprises',
  '/party/ponds',
  '/party/staffs',
  '/quality/labs',
  '/breeding/batches',
  '/breeding/activities',
  '/breeding/sales',
  '/circulation/transports',
  '/iot/rules',
  '/iot/cameras',
  '/disease/alerts',
  '/effluent/patrols',
  '/effluent/waters',
])

async function saveRecord(apiPath, id, body) {
  if (DIRECT_PUT_APIS.has(apiPath)) {
    await http.put(`${apiPath}/${id}`, body)
    return
  }
  const res = await http.put('/feature/update', { api: apiPath, id, data: body })
  if (res.data?.soft) {
    ElMessage.warning(res.data.message || '演示环境：该资源变更未持久化')
  }
}

function resetForm() {
  Object.keys(form).forEach((k) => delete form[k])
  dialogFields.value.forEach((f) => {
    form[f.prop] = f.default ?? ''
  })
}

async function openCreate() {
  formMode.value = 'create'
  editingId.value = null
  resetForm()
  await ensureFieldOptions()
  formDlg.value = true
}

async function openEdit(row) {
  formMode.value = 'edit'
  editingId.value = row.id
  resetForm()
  await ensureFieldOptions()
  dialogFields.value.forEach((f) => {
    form[f.prop] = row[f.prop] ?? ''
  })
  if (props.api.includes('/system/users')) {
    form.password = ''
    if (row.roleCode) form.roleCode = row.roleCode
    if (row.enterpriseId != null) form.enterpriseId = row.enterpriseId
  }
  formDlg.value = true
}

function openView(row) {
  viewRow.value = { ...row }
  viewDlg.value = true
}

async function onUpload(opt, field) {
  const auth = useAuthStore()
  const fd = new FormData()
  fd.append('file', opt.file)
  try {
    const res = await axios.post('/api/v1/platform/upload', fd, {
      headers: { Authorization: `Bearer ${auth.token}` },
    })
    const envelope = res.data
    if (envelope?.code != null && envelope.code !== 0) {
      throw new Error(envelope.message || '上传失败')
    }
    const data = envelope?.data ?? envelope
    form[field.prop] = data.url
    const nameProp = field.fileNameProp || 'fileName'
    form[nameProp] = data.fileName || opt.file.name
    ElMessage.success('上传成功')
    opt.onSuccess?.(data)
  } catch (e) {
    ElMessage.error(e.message || '上传失败')
    opt.onError?.(e)
  }
}

async function submitForm() {
  const apiFull = props.api || ''
  const apiPath = apiFull.split('?')[0]
  const q = {}
  if (apiFull.includes('?')) new URLSearchParams(apiFull.split('?')[1]).forEach((v, k) => { q[k] = v })
  saving.value = true
  try {
    const body = normalizeCreateBody(apiPath, { ...form }, q)
    if (formMode.value === 'edit' && editingId.value) {
      await saveRecord(apiPath, editingId.value, body)
      ElMessage.success('已保存')
    } else {
      await http.post(apiPath, body)
      ElMessage.success('已创建')
    }
    formDlg.value = false
    resetForm()
    load()
  } catch {
    /* interceptor */
  } finally {
    saving.value = false
  }
}

function defaultActions(row) {
  const apiPath = apiBasePath()
  const acts = [{ label: '查看', onClick: () => openView(row) }]
  if (!props.readonly && isEditableApi(apiPath)) {
    acts.push({ label: '编辑', onClick: () => openEdit(row) })
    acts.push({ label: '删除', onClick: () => removeRow(row) })
  }
  if (apiPath.includes('/system/users') && !props.readonly) {
    acts.push({
      label: '重置密码',
      onClick: async () => {
        await http.put(`/system/users/${row.id}/reset-password`)
        ElMessage.success('密码已重置为 123456')
      },
    })
  }
  return acts
}

function actionsForRow(row) {
  const custom = props.rowActions?.(row)
  if (custom && custom.length) return custom
  return defaultActions(row)
}

async function removeRow(row) {
  if (!row.id) return
  try {
    await ElMessageBox.confirm('确认删除该记录？', '删除')
  } catch {
    return
  }
  const apiPath = (props.api || '').split('?')[0]
  try {
    await http.post('/feature/batch-delete', { api: apiPath, ids: [row.id] })
    ElMessage.success('已删除')
  } catch {
    rows.value = rows.value.filter((r) => r.id !== row.id)
    ElMessage.success('已从列表移除')
    return
  }
  load()
}

function doExport() {
  const cols = props.columns.map((c) => c.prop)
  const headers = props.columns.map((c) => c.label)
  const lines = [headers.join(',')]
  rows.value.forEach((r) => {
    lines.push(cols.map((c) => `"${String(r[c] ?? '').replace(/"/g, '""')}"`).join(','))
  })
  const blob = new Blob(['\ufeff' + lines.join('\n')], { type: 'text/csv;charset=utf-8' })
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob)
  a.download = `${props.title || 'export'}.csv`
  a.click()
  ElMessage.success(`已导出 ${rows.value.length} 行`)
}

function triggerImport() {
  fileRef.value?.click()
}

async function onImportFile(e) {
  const file = e.target.files?.[0]
  e.target.value = ''
  if (!file) return
  const text = await file.text()
  const lines = text.replace(/^\ufeff/, '').split(/\r?\n/).filter(Boolean)
  if (lines.length < 2) {
    ElMessage.warning('CSV 至少需要表头+一行数据')
    return
  }
  const headers = lines[0].split(',').map((h) => h.replace(/^"|"$/g, '').trim())
  const propsByLabel = Object.fromEntries(props.columns.map((c) => [c.label, c.prop]))
  const apiFull = props.api || ''
  const apiPath = apiFull.split('?')[0]
  const q = {}
  if (apiFull.includes('?')) new URLSearchParams(apiFull.split('?')[1]).forEach((v, k) => { q[k] = v })
  let okN = 0
  for (const line of lines.slice(1, 51)) {
    const cells = line.split(',').map((x) => x.replace(/^"|"$/g, '').trim())
    const raw = {}
    headers.forEach((h, i) => {
      const prop = propsByLabel[h] || props.columns[i]?.prop
      if (prop) raw[prop] = cells[i]
    })
    try {
      await http.post(apiPath, normalizeCreateBody(apiPath, raw, q))
      okN += 1
    } catch {
      /* skip */
    }
  }
  ElMessage.success(`导入完成 ${okN} 条`)
  load()
}

async function doBatchDelete() {
  if (!sel.value.length) {
    ElMessage.warning('请先勾选行')
    return
  }
  try {
    await ElMessageBox.confirm(`确认删除选中的 ${sel.value.length} 条？`, '批量删除')
  } catch {
    return
  }
  const ids = sel.value.map((x) => x.id).filter(Boolean)
  const apiPath = (props.api || '').split('?')[0]
  try {
    const res = await http.post('/feature/batch-delete', { api: apiPath, ids })
    ElMessage.success(`已删除 ${res.data?.count ?? ids.length} 条`)
  } catch {
    rows.value = rows.value.filter((r) => !ids.includes(r.id))
    ElMessage.success('已从列表移除（演示）')
    return
  }
  load()
}

watch(() => props.api, load)
onMounted(load)
defineExpose({ load, rows, openView, openEdit })
</script>

<style scoped>
.bar { display:flex; justify-content:space-between; align-items:center; gap:12px; flex-wrap:wrap; margin-bottom:12px; }
.actions { display:flex; gap:8px; flex-wrap:wrap; }
.filters { margin-bottom:8px; }
.upload-row { display:flex; align-items:center; gap:12px; flex-wrap:wrap; }
.upload-name { color:#606266; font-size:13px; max-width:240px; overflow:hidden; text-overflow:ellipsis; }
</style>
