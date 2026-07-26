<template>
  <!-- 企业端：直接编辑本主体 -->
  <div v-if="isSelf" class="page-card ent-self">
    <h2 class="page-title">{{ title }}</h2>
    <EnterpriseForm v-if="formReady" v-model="form" :region-options="regionOptions" :parent-options="parentOptions" />
    <div class="footer-bar">
      <el-button type="primary" :loading="saving" @click="saveSelf">提交</el-button>
    </div>
  </div>

  <!-- 区县端：列表 + 抽屉 -->
  <div v-else class="page-card">
    <div class="bar">
      <h2 class="page-title">{{ title }}</h2>
      <div class="actions">
        <el-button @click="load">查询</el-button>
        <el-button @click="resetQuery">重置</el-button>
        <el-button type="primary" @click="openCreate">新建</el-button>
        <el-button @click="triggerImport">导入</el-button>
        <el-button link type="primary" @click="downloadTemplate">下载导入模板</el-button>
        <el-button @click="doExport">导出</el-button>
        <el-button type="danger" plain :disabled="!selection.length" @click="batchDelete">批量删除</el-button>
        <input ref="fileRef" type="file" accept=".csv,text/csv" style="display:none" @change="onImportFile" />
      </div>
    </div>

    <el-form inline class="filters" @submit.prevent>
      <el-form-item label="主体名称"><el-input v-model="q.keyword" clearable placeholder="主体名称" style="width:150px" /></el-form-item>
      <el-form-item label="所属区域"><el-input v-model="q.regionName" clearable placeholder="所属区域" style="width:150px" /></el-form-item>
      <el-form-item label="主体类型">
        <el-select v-model="q.subjectType" clearable placeholder="全部" style="width:130px">
          <el-option v-for="o in subjectTypeOpts" :key="o.value" :label="o.label" :value="o.value" />
        </el-select>
      </el-form-item>
      <el-form-item label="养殖品种"><el-input v-model="q.species" clearable placeholder="品种" style="width:120px" /></el-form-item>
    </el-form>

    <el-table :data="rows" stripe v-loading="loading" @selection-change="selection = $event">
      <el-table-column type="selection" width="48" />
      <el-table-column prop="name" label="主体名称" min-width="140" show-overflow-tooltip />
      <el-table-column prop="subjectType" label="主体类型" width="110" />
      <el-table-column prop="regionName" label="所属区域" min-width="180" show-overflow-tooltip />
      <el-table-column prop="projectName" label="所属项目" min-width="200" show-overflow-tooltip />
      <el-table-column prop="areaMu" label="养殖面积（亩）" width="120" />
      <el-table-column prop="species" label="养殖品种" min-width="140" show-overflow-tooltip />
      <el-table-column label="操作" width="220" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="openUsers(row)">用户管理</el-button>
          <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
          <el-button link type="danger" @click="removeOne(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
    <div class="pager">
      <el-pagination
        v-model:current-page="page"
        v-model:page-size="size"
        :total="total"
        layout="total, prev, pager, next"
        @current-change="load"
      />
    </div>

    <el-drawer v-model="drawer" :title="drawerTitle" size="820px" destroy-on-close @opened="onDrawerOpened">
      <EnterpriseForm ref="formRef" v-model="form" :region-options="regionOptions" :parent-options="parentOptions" />
      <template #footer>
        <el-button @click="drawer = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="saveGov">保存</el-button>
      </template>
    </el-drawer>

    <el-dialog v-model="userDlg" :title="`用户管理 - ${userEnt?.name || ''}`" width="720px" destroy-on-close>
      <div class="user-bar">
        <el-button type="primary" size="small" @click="openAddUser">新增用户</el-button>
      </div>
      <el-table :data="entUsers" stripe size="small" v-loading="userLoading">
        <el-table-column prop="username" label="登录名" width="120" />
        <el-table-column prop="realName" label="姓名" width="100" />
        <el-table-column prop="mobile" label="手机号" width="130" />
        <el-table-column prop="roleName" label="角色" />
        <el-table-column label="状态" width="80">
          <template #default="{ row }"><el-tag size="small" :type="row.status ? 'success' : 'info'">{{ row.status ? '启用' : '停用' }}</el-tag></template>
        </el-table-column>
      </el-table>
      <el-dialog v-model="addUserDlg" title="新增企业用户" width="420px" append-to-body destroy-on-close>
        <el-form :model="userForm" label-width="88px">
          <el-form-item label="登录名" required><el-input v-model="userForm.username" /></el-form-item>
          <el-form-item label="初始密码"><el-input v-model="userForm.password" type="password" show-password /></el-form-item>
          <el-form-item label="姓名"><el-input v-model="userForm.realName" /></el-form-item>
          <el-form-item label="手机号"><el-input v-model="userForm.mobile" /></el-form-item>
        </el-form>
        <template #footer>
          <el-button @click="addUserDlg = false">取消</el-button>
          <el-button type="primary" :loading="userSaving" @click="saveUser">确定</el-button>
        </template>
      </el-dialog>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import axios from 'axios'
import http from '@/api/http'
import { useAuthStore } from '@/stores/auth'
import EnterpriseForm from './EnterpriseForm.vue'

const props = defineProps({
  title: { type: String, default: '养殖主体' },
  mode: { type: String, default: 'gov' }, // gov | self
})

const auth = useAuthStore()
const isSelf = computed(() => props.mode === 'self' || auth.portal === 'ENT')

const rows = ref([])
const loading = ref(false)
const saving = ref(false)
const page = ref(1)
const size = ref(20)
const total = ref(0)
const selection = ref([])
const q = reactive({ keyword: '', regionName: '', subjectType: '', species: '' })
const fileRef = ref(null)

const drawer = ref(false)
const drawerTitle = ref('新建主体')
const editingId = ref(null)
const form = ref(emptyForm())
const formReady = ref(false)
const formRef = ref(null)
const regionOptions = ref([])
const parentOptions = ref([])

const userDlg = ref(false)
const userEnt = ref(null)
const entUsers = ref([])
const userLoading = ref(false)
const addUserDlg = ref(false)
const userSaving = ref(false)
const userForm = reactive({ username: '', password: '123456', realName: '', mobile: '' })

const subjectTypeOpts = [
  { label: '养殖个体户', value: 'INDIVIDUAL' },
  { label: '养殖企业', value: 'ENTERPRISE' },
  { label: '养殖园区', value: 'PARK' },
]

const FALLBACK_REGIONS = [
  {
    value: '330000',
    label: '浙江省',
    id: null,
    children: [
      {
        value: '330100',
        label: '杭州市',
        id: null,
        children: [
          {
            value: '330106',
            label: '西湖区',
            id: 1,
            children: [],
          },
        ],
      },
    ],
  },
]

function emptyForm() {
  return {
    name: '',
    subjectTypeCode: 'INDIVIDUAL',
    regionPath: [],
    regionPathLabel: '',
    regionId: null,
    idCard: '',
    parentEnterpriseId: null,
    speciesList: [],
    areaMu: null,
    annualOutputTon: null,
    breedingMode: 'POND',
    contactName: '',
    contactPhone: '',
    address: '',
    lng: null,
    lat: null,
    breedingItems: [],
    fisheryQualification: '',
    intro: '',
    promoImages: [],
    promoVideos: [],
    showOnScreen: false,
    selfCheckFiles: [],
  }
}

async function loadRegions() {
  const token = auth.token
  try {
    const res = await axios.get('/api/v1/party/regions/tree', {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    })
    const body = res.data
    const data = body?.data ?? body
    regionOptions.value = Array.isArray(data) && data.length ? data : FALLBACK_REGIONS
  } catch {
    regionOptions.value = FALLBACK_REGIONS
  }
}

async function loadParents(excludeId) {
  const res = await http.get('/party/enterprises', { params: { size: 200 } })
  const list = res.data?.list || []
  parentOptions.value = list.filter((e) => e.id !== excludeId).map((e) => ({ label: e.name, value: e.id }))
}

async function load() {
  if (isSelf.value) return
  loading.value = true
  try {
    const res = await http.get('/party/enterprises', {
      params: { page: page.value, size: size.value, keyword: q.keyword || undefined, regionName: q.regionName || undefined, subjectType: q.subjectType || undefined, species: q.species || undefined },
    })
    rows.value = res.data?.list || []
    total.value = res.data?.total || 0
  } finally {
    loading.value = false
  }
}

function resetQuery() {
  q.keyword = ''
  q.regionName = ''
  q.subjectType = ''
  q.species = ''
  page.value = 1
  load()
}

async function loadSelf() {
  const id = auth.user?.enterpriseId
  if (!id) return
  const d = (await http.get(`/party/enterprises/${id}`)).data
  form.value = mapApiToForm(d)
  formReady.value = true
  await loadParents(id)
}

function mapApiToForm(d) {
  return {
    name: d.name || '',
    subjectTypeCode: d.subjectTypeCode || 'ENTERPRISE',
    regionPath: d.regionPath || [],
    regionPathLabel: d.regionPathLabel || '',
    regionId: d.regionId || null,
    idCard: d.idCard || '',
    parentEnterpriseId: d.parentEnterpriseId || null,
    speciesList: d.speciesList?.length ? d.speciesList : (d.species ? d.species.split(/[、,]/).map((s) => s.trim()).filter(Boolean) : []),
    areaMu: d.areaMu ?? null,
    annualOutputTon: d.annualOutputTon ?? null,
    breedingMode: d.breedingMode || 'POND',
    contactName: d.contactName || '',
    contactPhone: d.contactPhone || '',
    address: d.address || '',
    lng: d.lng ?? null,
    lat: d.lat ?? null,
    breedingItems: (d.breedingItems || []).map((x) => ({ ...x })),
    fisheryQualification: d.fisheryQualification || '',
    intro: d.intro || '',
    promoImages: [...(d.promoImages || [])],
    promoVideos: [...(d.promoVideos || [])],
    showOnScreen: !!d.showOnScreen,
    selfCheckFiles: [...(d.selfCheckFiles || [])],
  }
}

function mapFormToApi(f) {
  return {
    name: f.name,
    subjectType: f.subjectTypeCode,
    regionId: f.regionId,
    regionPath: f.regionPath,
    regionPathLabel: f.regionPathLabel,
    idCard: f.idCard,
    parentEnterpriseId: f.parentEnterpriseId,
    speciesList: f.speciesList,
    areaMu: f.areaMu,
    annualOutputTon: f.annualOutputTon,
    breedingMode: f.breedingMode,
    contactName: f.contactName,
    contactPhone: f.contactPhone,
    address: f.address,
    lng: f.lng,
    lat: f.lat,
    breedingItems: f.breedingItems,
    fisheryQualification: f.fisheryQualification,
    intro: f.intro,
    promoImages: f.promoImages,
    promoVideos: f.promoVideos,
    showOnScreen: f.showOnScreen,
    selfCheckFiles: f.selfCheckFiles,
  }
}

function openCreate() {
  editingId.value = null
  drawerTitle.value = '新建主体'
  form.value = emptyForm()
  drawer.value = true
}

async function openEdit(row) {
  editingId.value = row.id
  drawerTitle.value = '编辑主体'
  const d = (await http.get(`/party/enterprises/${row.id}`)).data
  form.value = mapApiToForm(d)
  await loadParents(row.id)
  drawer.value = true
}

function onDrawerOpened() {
  formRef.value?.refreshMap?.()
}

async function saveGov() {
  if (!form.value.name?.trim()) {
    ElMessage.warning('请填写主体名称')
    return
  }
  saving.value = true
  try {
    const body = mapFormToApi(form.value)
    if (editingId.value) {
      await http.put(`/party/enterprises/${editingId.value}`, body)
      ElMessage.success('已保存')
    } else {
      await http.post('/party/enterprises', body)
      ElMessage.success('已创建')
    }
    drawer.value = false
    load()
  } finally {
    saving.value = false
  }
}

async function saveSelf() {
  if (!form.value.name?.trim()) {
    ElMessage.warning('请填写主体名称')
    return
  }
  saving.value = true
  try {
    await http.put(`/party/enterprises/${auth.user.enterpriseId}`, mapFormToApi(form.value))
    ElMessage.success('已提交')
  } finally {
    saving.value = false
  }
}

async function removeOne(row) {
  await ElMessageBox.confirm(`确定删除「${row.name}」？`, '删除确认', { type: 'warning' })
  await http.delete(`/party/enterprises/${row.id}`)
  ElMessage.success('已删除')
  load()
}

async function batchDelete() {
  if (!selection.value.length) return
  await ElMessageBox.confirm(`确定删除选中的 ${selection.value.length} 条？`, '批量删除', { type: 'warning' })
  await http.post('/party/enterprises/batch-delete', { ids: selection.value.map((r) => r.id) })
  ElMessage.success('已删除')
  load()
}

function triggerImport() {
  fileRef.value?.click()
}

async function onImportFile(ev) {
  const file = ev.target.files?.[0]
  ev.target.value = ''
  if (!file) return
  const fd = new FormData()
  fd.append('file', file)
  const token = auth.token
  await axios.post('/api/v1/party/enterprises-import', fd, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  })
  ElMessage.success('导入完成')
  load()
}

async function doExport() {
  await downloadBlob('/party/enterprises-export', 'enterprises.csv')
}

async function downloadTemplate() {
  await downloadBlob('/party/enterprises-import-template', 'enterprises_import_template.csv')
}

async function downloadBlob(path, filename) {
  const token = auth.token
  const res = await axios.get(`/api/v1${path}`, {
    responseType: 'blob',
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  })
  const url = URL.createObjectURL(res.data)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}

async function openUsers(row) {
  userEnt.value = row
  userDlg.value = true
  userLoading.value = true
  try {
    const res = await http.get('/system/users')
    entUsers.value = (res.data || []).filter((u) => u.enterpriseId === row.id)
  } finally {
    userLoading.value = false
  }
}

function openAddUser() {
  userForm.username = ''
  userForm.password = '123456'
  userForm.realName = ''
  userForm.mobile = ''
  addUserDlg.value = true
}

async function saveUser() {
  if (!userForm.username?.trim()) {
    ElMessage.warning('请填写登录名')
    return
  }
  userSaving.value = true
  try {
    await http.post('/system/users', {
      ...userForm,
      userType: 'ENTERPRISE',
      enterpriseId: userEnt.value.id,
      roleCode: 'ENT_ADMIN',
    })
    ElMessage.success('用户已创建')
    addUserDlg.value = false
    openUsers(userEnt.value)
  } finally {
    userSaving.value = false
  }
}

onMounted(async () => {
  await loadRegions()
  if (isSelf.value) {
    await loadSelf()
  } else {
    await load()
    loadParents(null)
  }
})
</script>

<style scoped>
.bar { display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:12px; margin-bottom:12px; }
.actions { display:flex; flex-wrap:wrap; gap:8px; }
.filters { margin-bottom:12px; }
.pager { margin-top:16px; display:flex; justify-content:flex-end; }
.footer-bar { margin-top:20px; }
.user-bar { margin-bottom:12px; }
.ent-self { max-width:900px; }
</style>
