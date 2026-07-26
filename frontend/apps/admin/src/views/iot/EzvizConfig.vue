<template>
  <div class="page-card ezviz">
    <div class="bar">
      <div>
        <h2 class="page-title">萤石云配置</h2>
        <p class="sub">项目级凭证由区县维护；摄像头可放入资源池再划分给下属企业。</p>
      </div>
      <el-tag :type="statusType">{{ statusText }}</el-tag>
    </div>

    <el-row :gutter="16">
      <el-col :xs="24" :md="10">
        <section class="block">
          <h3>① 开放平台凭证</h3>
          <template v-if="cfg.canEdit">
            <el-form label-width="100px">
              <el-form-item label="AppKey">
                <el-input v-model="form.appKey" placeholder="萤石开放平台 AppKey" clearable />
              </el-form-item>
              <el-form-item label="AppSecret">
                <el-input v-model="form.appSecret" type="password" show-password placeholder="AppSecret" clearable />
              </el-form-item>
              <el-form-item>
                <el-button type="primary" :loading="saving" @click="saveCfg">保存</el-button>
                <el-button :loading="testing" @click="testCfg">测试连通</el-button>
              </el-form-item>
            </el-form>
          </template>
          <template v-else>
            <p>AppKey：{{ cfg.appKeyMasked || '—' }}</p>
            <p>Secret：{{ cfg.hasSecret ? '已配置' : '未配置' }}</p>
            <p class="muted">企业侧只读；凭证由区县在「萤石云配置」中维护。</p>
          </template>
          <p class="msg">{{ cfg.lastCheckMsg }}</p>
        </section>
      </el-col>

      <el-col :xs="24" :md="14">
        <section class="block">
          <div class="row-between">
            <h3>② 摄像头台账与企业划分</h3>
            <div class="actions">
              <el-select v-if="isGov" v-model="filterEnt" clearable placeholder="按企业筛选" style="width:160px" @change="loadCams">
                <el-option label="未分配资源池" :value="0" />
                <el-option v-for="e in enterprises" :key="e.id" :label="e.name" :value="e.id" />
              </el-select>
              <el-button type="primary" @click="openCreate">新增摄像头</el-button>
              <el-button @click="loadCams">刷新</el-button>
            </div>
          </div>
          <el-table :data="cameras" stripe size="small" max-height="420">
            <el-table-column prop="name" label="名称" min-width="100" />
            <el-table-column prop="deviceSerial" label="序列号" min-width="110" />
            <el-table-column prop="channelNo" label="通道" width="60" />
            <el-table-column prop="scene" label="场景" width="80" />
            <el-table-column prop="enterpriseName" label="所属企业" min-width="120" />
            <el-table-column prop="status" label="状态" width="70" />
            <el-table-column label="操作" width="220" fixed="right">
              <template #default="{ row }">
                <el-button v-if="isGov" link type="primary" @click="openAssign(row)">划分</el-button>
                <el-button link type="primary" @click="preview(row)">测播</el-button>
                <el-button link type="danger" @click="remove(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </section>
      </el-col>
    </el-row>

    <section v-if="play" class="block preview">
      <h3>③ 取流预览 · {{ playCam?.name }}</h3>
      <p class="mono">{{ play.playUrl }}</p>
      <p>{{ play.message }}</p>
      <el-tag v-if="play.demo" type="warning" size="small">演示模式</el-tag>
      <el-tag v-else type="success" size="small">已配置凭证</el-tag>
    </section>

    <el-dialog v-model="dlg" title="新增摄像头" width="480px">
      <el-form :model="camForm" label-width="100px">
        <el-form-item label="名称"><el-input v-model="camForm.name" /></el-form-item>
        <el-form-item label="序列号"><el-input v-model="camForm.deviceSerial" placeholder="如 GN2548932" /></el-form-item>
        <el-form-item label="通道"><el-input-number v-model="camForm.channelNo" :min="1" /></el-form-item>
        <el-form-item label="场景">
          <el-select v-model="camForm.scene" style="width:100%">
            <el-option label="塘口 POND" value="POND" />
            <el-option label="仓库 WAREHOUSE" value="WAREHOUSE" />
            <el-option label="场区 YARD" value="YARD" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="isGov" label="划分企业">
          <el-select v-model="camForm.enterpriseId" clearable placeholder="留空=资源池" style="width:100%">
            <el-option label="未分配（资源池）" :value="0" />
            <el-option v-for="e in enterprises" :key="e.id" :label="e.name" :value="e.id" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dlg=false">取消</el-button>
        <el-button type="primary" @click="saveCam">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="assignDlg" title="划分给企业" width="420px">
      <p>摄像头：{{ assignRow?.name }}</p>
      <el-select v-model="assignEntId" style="width:100%;margin-top:12px" placeholder="选择企业">
        <el-option label="收回资源池" :value="0" />
        <el-option v-for="e in enterprises" :key="e.id" :label="e.name" :value="e.id" />
      </el-select>
      <template #footer>
        <el-button @click="assignDlg=false">取消</el-button>
        <el-button type="primary" @click="doAssign">确认划分</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import http from '@/api/http'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const isGov = computed(() => auth.portal === 'GOV' || auth.portal === 'BOTH')
const cfg = ref({ canEdit: false, status: 'UNSET', lastCheckMsg: '' })
const form = reactive({ appKey: '', appSecret: '' })
const saving = ref(false)
const testing = ref(false)
const cameras = ref([])
const enterprises = ref([])
const filterEnt = ref(null)
const dlg = ref(false)
const camForm = reactive({ name: '', deviceSerial: '', channelNo: 1, scene: 'POND', enterpriseId: 0 })
const assignDlg = ref(false)
const assignRow = ref(null)
const assignEntId = ref(0)
const play = ref(null)
const playCam = ref(null)

const statusType = computed(() => {
  const s = cfg.value.status
  if (s === 'OK') return 'success'
  if (s === 'ERROR') return 'danger'
  if (s === 'ENV') return 'warning'
  return 'info'
})
const statusText = computed(() => {
  const map = { OK: '凭证正常', ERROR: '异常', ENV: '环境变量兜底', UNSET: '未配置' }
  return map[cfg.value.status] || cfg.value.status || '未配置'
})

async function loadCfg() {
  const res = await http.get('/iot/ezviz/config')
  cfg.value = res.data || {}
  if (cfg.value.appKey) form.appKey = cfg.value.appKey
}

async function loadEnterprises() {
  if (!isGov.value) return
  const res = await http.get('/party/enterprises', { params: { size: 200 } })
  enterprises.value = res.data?.list || res.data || []
}

async function loadCams() {
  const params = {}
  if (isGov.value && filterEnt.value !== null && filterEnt.value !== undefined && filterEnt.value !== '') {
    params.enterpriseId = filterEnt.value
  }
  const res = await http.get('/iot/cameras', { params })
  cameras.value = res.data || []
}

async function saveCfg() {
  saving.value = true
  try {
    await http.put('/iot/ezviz/config', { appKey: form.appKey, appSecret: form.appSecret })
    ElMessage.success('已保存')
    loadCfg()
  } finally {
    saving.value = false
  }
}

async function testCfg() {
  testing.value = true
  try {
    const res = await http.post('/iot/ezviz/test')
    ElMessage.success(res.data?.message || '连通成功')
    loadCfg()
  } finally {
    testing.value = false
  }
}

function openCreate() {
  camForm.name = ''
  camForm.deviceSerial = ''
  camForm.channelNo = 1
  camForm.scene = 'POND'
  camForm.enterpriseId = isGov.value ? 0 : auth.user?.enterpriseId || 0
  dlg.value = true
}

async function saveCam() {
  await http.post('/iot/cameras', {
    name: camForm.name,
    deviceSerial: camForm.deviceSerial,
    channelNo: camForm.channelNo,
    scene: camForm.scene,
    enterpriseId: isGov.value ? camForm.enterpriseId : undefined,
  })
  ElMessage.success('已新增')
  dlg.value = false
  loadCams()
}

function openAssign(row) {
  assignRow.value = row
  assignEntId.value = row.enterpriseId || 0
  assignDlg.value = true
}

async function doAssign() {
  await http.post(`/iot/cameras/${assignRow.value.id}/assign`, { enterpriseId: assignEntId.value })
  ElMessage.success(assignEntId.value ? '已划分给企业' : '已收回资源池')
  assignDlg.value = false
  loadCams()
}

async function preview(row) {
  playCam.value = row
  const res = await http.get(`/iot/cameras/${row.id}/play-url`)
  play.value = res.data
}

async function remove(row) {
  await ElMessageBox.confirm(`删除摄像头「${row.name}」？`, '确认')
  await http.delete(`/iot/cameras/${row.id}`)
  ElMessage.success('已删除')
  loadCams()
}

onMounted(async () => {
  await Promise.all([loadCfg(), loadEnterprises(), loadCams()])
})
</script>

<style scoped>
.sub { margin: 4px 0 0; color: #678; font-size: 13px; }
.bar { display:flex; justify-content:space-between; align-items:flex-start; gap:12px; margin-bottom:16px; }
.block { border:1px solid #e6eeea; border-radius:10px; padding:14px; background:#fff; margin-bottom:12px; }
.block h3 { margin:0 0 12px; font-size:15px; }
.row-between { display:flex; justify-content:space-between; align-items:center; gap:8px; flex-wrap:wrap; margin-bottom:8px; }
.row-between h3 { margin:0; }
.actions { display:flex; gap:8px; flex-wrap:wrap; align-items:center; }
.msg, .muted { color:#678; font-size:12px; margin-top:8px; }
.mono { font-family: ui-monospace, Consolas, monospace; font-size:12px; word-break:break-all; }
.preview { background:#f7fbf9; }
</style>
