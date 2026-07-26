<template>
  <div class="page-card uav-page">
    <h2 class="page-title">{{ title }}</h2>

    <div class="stats">
      <div class="stat-card">
        <div class="stat-label">注册飞手</div>
        <div class="stat-val">{{ stats.pilotCount }}<span class="unit">人</span></div>
      </div>
      <div class="stat-card">
        <div class="stat-label">飞行任务</div>
        <div class="stat-val">{{ stats.missionCount }}<span class="unit">项</span></div>
      </div>
      <div class="stat-card">
        <div class="stat-label">待处理任务</div>
        <div class="stat-val warn">{{ stats.pendingCount }}<span class="unit">项</span></div>
      </div>
      <div class="stat-card">
        <div class="stat-label">累计飞行时长</div>
        <div class="stat-val">{{ stats.totalFlightHours }}<span class="unit">小时</span></div>
      </div>
    </div>

    <el-tabs v-model="tab" class="uav-tabs">
      <!-- 飞手管理 -->
      <el-tab-pane label="无人机飞手管理" name="pilots">
        <div class="toolbar">
          <el-input v-model="pilotQ" clearable placeholder="飞手姓名/编号" style="width:180px" @keyup.enter="loadPilots" />
          <el-button @click="loadPilots">查询</el-button>
          <el-button @click="resetPilots">重置</el-button>
          <el-button type="primary" @click="openPilotCreate">新增飞手</el-button>
        </div>
        <el-table :data="pilots" stripe v-loading="pilotLoading">
          <el-table-column prop="code" label="飞手编号" width="120" />
          <el-table-column prop="name" label="飞手姓名" width="100" />
          <el-table-column prop="level" label="资质等级" min-width="120" />
          <el-table-column prop="registerDate" label="注册日期" width="120" />
          <el-table-column prop="flightHours" label="累计飞行时长(小时)" width="150" />
          <el-table-column prop="violationCount" label="违规次数" width="90" />
          <el-table-column label="操作" width="140" fixed="right">
            <template #default="{ row }">
              <el-button link type="primary" @click="openPilotEdit(row)">编辑</el-button>
              <el-button link type="danger" @click="removePilot(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <!-- 任务管理 -->
      <el-tab-pane label="无人机飞行任务管理" name="missions">
        <div class="toolbar">
          <el-input v-model="missionQ" clearable placeholder="任务名称/编号" style="width:180px" @keyup.enter="loadMissions" />
          <el-select v-model="missionStatus" clearable placeholder="任务状态" style="width:130px">
            <el-option v-for="o in statusOpts" :key="o.value" :label="o.label" :value="o.value" />
          </el-select>
          <el-button @click="loadMissions">查询</el-button>
          <el-button @click="resetMissions">重置</el-button>
          <el-button type="primary" @click="openMissionCreate">新增任务</el-button>
        </div>
        <el-table :data="missions" stripe v-loading="missionLoading">
          <el-table-column prop="code" label="任务编号" width="120" />
          <el-table-column prop="name" label="任务名称" min-width="140" show-overflow-tooltip />
          <el-table-column prop="taskType" label="任务类型" width="100" />
          <el-table-column prop="location" label="任务地点" min-width="160" show-overflow-tooltip />
          <el-table-column prop="leader" label="任务负责人" width="100" />
          <el-table-column prop="pilotLabel" label="执行飞手(姓名/编号)" min-width="150" show-overflow-tooltip />
          <el-table-column label="任务状态" width="90">
            <template #default="{ row }"><el-tag size="small">{{ row.statusLabel || statusLabel(row.status) }}</el-tag></template>
          </el-table-column>
          <el-table-column label="验收结果" width="90">
            <template #default="{ row }">{{ row.acceptResultLabel || acceptLabel(row.acceptResult) }}</template>
          </el-table-column>
          <el-table-column prop="remark" label="备注" min-width="100" show-overflow-tooltip />
          <el-table-column label="操作" width="140" fixed="right">
            <template #default="{ row }">
              <el-button link type="primary" @click="openMissionEdit(row)">编辑</el-button>
              <el-button link type="danger" @click="removeMission(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
    </el-tabs>

    <!-- 飞手表单 -->
    <el-dialog v-model="pilotDlg" :title="pilotEditId ? '编辑飞手' : '新增飞手'" width="520px" destroy-on-close>
      <el-form :model="pilotForm" label-width="140px">
        <el-form-item label="飞手编号"><el-input :model-value="pilotForm.code || '系统自动生成'" disabled /></el-form-item>
        <el-form-item label="飞手姓名" required><el-input v-model="pilotForm.name" placeholder="请输入飞手姓名" /></el-form-item>
        <el-form-item label="资质等级" required><el-input v-model="pilotForm.level" placeholder="请输入资质等级" /></el-form-item>
        <el-form-item label="注册日期" required>
          <el-date-picker v-model="pilotForm.registerDate" type="date" value-format="YYYY-MM-DD" style="width:100%" placeholder="请选择注册日期" />
        </el-form-item>
        <el-form-item label="累计飞行时长(小时)" required>
          <el-input-number v-model="pilotForm.flightHours" :min="0" :precision="1" controls-position="right" style="width:100%" />
        </el-form-item>
        <el-form-item label="违规次数"><el-input-number v-model="pilotForm.violationCount" :min="0" controls-position="right" style="width:100%" /></el-form-item>
        <el-form-item label="飞行资质附件">
          <el-upload
            :file-list="pilotFileList"
            :limit="9"
            accept=".jpg,.jpeg,.gif,.png,.pdf"
            :http-request="(opt) => uploadFile(opt, pilotForm, 'attachments')"
            :on-remove="(f) => removeFile(f, pilotForm, 'attachments')"
          >
            <el-button type="primary" plain>上传文件</el-button>
          </el-upload>
          <p class="hint">支持 jpg/jpeg/gif/png/pdf，最多 9 个附件</p>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="pilotDlg = false">取消</el-button>
        <el-button type="primary" :loading="pilotSaving" @click="savePilot">确定</el-button>
      </template>
    </el-dialog>

    <!-- 任务表单 -->
    <el-dialog v-model="missionDlg" :title="missionEditId ? '编辑任务' : '新增任务'" width="640px" destroy-on-close>
      <el-form :model="missionForm" label-width="150px">
        <el-form-item label="任务编号"><el-input :model-value="missionForm.code || '系统自动生成'" disabled /></el-form-item>
        <el-form-item label="任务名称" required><el-input v-model="missionForm.name" placeholder="请输入任务名称" /></el-form-item>
        <el-form-item label="任务类型" required>
          <el-select v-model="missionForm.taskType" placeholder="请选择任务类型" style="width:100%">
            <el-option v-for="t in taskTypeOpts" :key="t" :label="t" :value="t" />
          </el-select>
        </el-form-item>
        <el-form-item label="任务地点" required><el-input v-model="missionForm.location" type="textarea" :rows="2" maxlength="100" show-word-limit placeholder="请输入任务地点" /></el-form-item>
        <el-form-item label="任务负责人" required><el-input v-model="missionForm.leader" placeholder="请输入任务负责人" /></el-form-item>
        <el-form-item label="执行飞手" required>
          <el-select v-model="missionForm.pilotId" placeholder="请选择执行飞手" style="width:100%" filterable>
            <el-option v-for="p in pilots" :key="p.id" :label="`${p.name} / ${p.code}`" :value="p.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="任务开始时间" required>
          <el-date-picker v-model="missionForm.startTime" type="datetime" value-format="YYYY-MM-DDTHH:mm:ss" style="width:100%" placeholder="请选择任务开始时间" />
        </el-form-item>
        <el-form-item label="任务结束时间" required>
          <el-date-picker v-model="missionForm.endTime" type="datetime" value-format="YYYY-MM-DDTHH:mm:ss" style="width:100%" placeholder="请选择任务结束时间" />
        </el-form-item>
        <el-form-item label="计划飞行时长(小时)" required>
          <el-input-number v-model="missionForm.planHours" :min="0" :precision="1" controls-position="right" style="width:100%" />
        </el-form-item>
        <el-form-item label="实际飞行时长(小时)">
          <el-input-number v-model="missionForm.actualHours" :min="0" :precision="1" controls-position="right" style="width:100%" />
        </el-form-item>
        <el-form-item label="任务状态" required>
          <el-select v-model="missionForm.status" style="width:100%">
            <el-option v-for="o in statusOpts" :key="o.value" :label="o.label" :value="o.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="任务验收结果" required>
          <el-select v-model="missionForm.acceptResult" style="width:100%">
            <el-option v-for="o in acceptOpts" :key="o.value" :label="o.label" :value="o.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="备注"><el-input v-model="missionForm.remark" type="textarea" :rows="2" maxlength="200" show-word-limit placeholder="请输入备注" /></el-form-item>
        <el-form-item label="飞行图片">
          <el-upload
            :file-list="missionImageList"
            :limit="9"
            accept=".jpg,.jpeg,.gif,.png,.pdf"
            :http-request="(opt) => uploadFile(opt, missionForm, 'images')"
            :on-remove="(f) => removeFile(f, missionForm, 'images')"
          >
            <el-button type="primary" plain>上传文件</el-button>
          </el-upload>
          <p class="hint">支持 jpg/jpeg/gif/png/pdf，最多 9 张</p>
        </el-form-item>
        <el-form-item label="飞行视频">
          <el-upload
            :file-list="missionVideoList"
            :limit="3"
            accept=".mp4,.avi,.mov,.wmv,.flv,.mkv"
            :http-request="(opt) => uploadFile(opt, missionForm, 'videos')"
            :on-remove="(f) => removeFile(f, missionForm, 'videos')"
          >
            <el-button type="primary" plain>上传视频</el-button>
          </el-upload>
          <p class="hint">支持 mp4/avi/mov/wmv/flv/mkv，最多 3 个</p>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="missionDlg = false">取消</el-button>
        <el-button type="primary" :loading="missionSaving" @click="saveMission">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import axios from 'axios'
import http from '@/api/http'
import { useAuthStore } from '@/stores/auth'

defineProps({ title: { type: String, default: '无人机巡查' } })

const auth = useAuthStore()
const tab = ref('pilots')
const stats = reactive({ pilotCount: 0, missionCount: 0, pendingCount: 0, totalFlightHours: 0 })

const pilots = ref([])
const missions = ref([])
const pilotLoading = ref(false)
const missionLoading = ref(false)
const pilotQ = ref('')
const missionQ = ref('')
const missionStatus = ref('')

const pilotDlg = ref(false)
const pilotEditId = ref(null)
const pilotSaving = ref(false)
const pilotForm = reactive(emptyPilot())

const missionDlg = ref(false)
const missionEditId = ref(null)
const missionSaving = ref(false)
const missionForm = reactive(emptyMission())

const statusOpts = [
  { label: '未开始', value: 'NOT_STARTED' },
  { label: '进行中', value: 'IN_PROGRESS' },
  { label: '已完成', value: 'COMPLETED' },
  { label: '已取消', value: 'CANCELLED' },
]
const acceptOpts = [
  { label: '合格', value: 'QUALIFIED' },
  { label: '不合格', value: 'UNQUALIFIED' },
  { label: '待验收', value: 'PENDING' },
]
const taskTypeOpts = ['日常巡查', '应急排查', '水质监测', '投饵监管', '其他']

function emptyPilot() {
  return { code: '', name: '', level: '', registerDate: '', flightHours: 0, violationCount: 0, attachments: [] }
}
function emptyMission() {
  return {
    code: '', name: '', taskType: '', location: '', leader: '', pilotId: null,
    startTime: '', endTime: '', planHours: null, actualHours: null,
    status: 'NOT_STARTED', acceptResult: 'QUALIFIED', remark: '', images: [], videos: [],
  }
}

function statusLabel(s) {
  return statusOpts.find((o) => o.value === s)?.label || s
}
function acceptLabel(s) {
  return acceptOpts.find((o) => o.value === s)?.label || s
}

function fileListFrom(urls) {
  return (urls || []).map((url, i) => ({ name: url.split('/').pop() || `file-${i}`, url, uid: `${url}-${i}` }))
}
const pilotFileList = computed(() => fileListFrom(pilotForm.attachments))
const missionImageList = computed(() => fileListFrom(missionForm.images))
const missionVideoList = computed(() => fileListFrom(missionForm.videos))

async function loadStats() {
  const res = await http.get('/uav/stats')
  Object.assign(stats, res.data || {})
}

async function loadPilots() {
  pilotLoading.value = true
  try {
    const res = await http.get('/uav/pilots', { params: { keyword: pilotQ.value || undefined } })
    pilots.value = res.data?.list || []
  } finally {
    pilotLoading.value = false
  }
}

async function loadMissions() {
  missionLoading.value = true
  try {
    const res = await http.get('/uav/missions', {
      params: { keyword: missionQ.value || undefined, status: missionStatus.value || undefined },
    })
    missions.value = res.data?.list || []
  } finally {
    missionLoading.value = false
  }
}

function resetPilots() {
  pilotQ.value = ''
  loadPilots()
}
function resetMissions() {
  missionQ.value = ''
  missionStatus.value = ''
  loadMissions()
}

function openPilotCreate() {
  pilotEditId.value = null
  Object.assign(pilotForm, emptyPilot())
  pilotDlg.value = true
}
function openPilotEdit(row) {
  pilotEditId.value = row.id
  Object.assign(pilotForm, {
    code: row.code,
    name: row.name,
    level: row.level,
    registerDate: row.registerDate,
    flightHours: row.flightHours,
    violationCount: row.violationCount,
    attachments: [...(row.attachments || [])],
  })
  pilotDlg.value = true
}

async function savePilot() {
  if (!pilotForm.name?.trim() || !pilotForm.level?.trim() || !pilotForm.registerDate) {
    ElMessage.warning('请填写必填项')
    return
  }
  pilotSaving.value = true
  try {
    const body = {
      name: pilotForm.name,
      level: pilotForm.level,
      registerDate: pilotForm.registerDate,
      flightHours: pilotForm.flightHours,
      violationCount: pilotForm.violationCount,
      attachments: pilotForm.attachments,
    }
    if (pilotEditId.value) {
      await http.put(`/uav/pilots/${pilotEditId.value}`, body)
    } else {
      await http.post('/uav/pilots', body)
    }
    ElMessage.success('已保存')
    pilotDlg.value = false
    loadPilots()
    loadStats()
  } finally {
    pilotSaving.value = false
  }
}

async function removePilot(row) {
  await ElMessageBox.confirm(`确定删除飞手「${row.name}」？`, '删除确认', { type: 'warning' })
  await http.delete(`/uav/pilots/${row.id}`)
  ElMessage.success('已删除')
  loadPilots()
  loadStats()
}

function openMissionCreate() {
  missionEditId.value = null
  Object.assign(missionForm, emptyMission())
  if (!pilots.value.length) loadPilots()
  missionDlg.value = true
}
function openMissionEdit(row) {
  missionEditId.value = row.id
  Object.assign(missionForm, {
    code: row.code,
    name: row.name,
    taskType: row.taskType,
    location: row.location,
    leader: row.leader,
    pilotId: row.pilotId,
    startTime: row.startTime,
    endTime: row.endTime,
    planHours: row.planHours,
    actualHours: row.actualHours,
    status: row.status,
    acceptResult: row.acceptResult,
    remark: row.remark || '',
    images: [...(row.images || [])],
    videos: [...(row.videos || [])],
  })
  missionDlg.value = true
}

async function saveMission() {
  if (!missionForm.name?.trim() || !missionForm.taskType || !missionForm.location?.trim() || !missionForm.leader?.trim() || !missionForm.pilotId) {
    ElMessage.warning('请填写必填项')
    return
  }
  missionSaving.value = true
  try {
    const body = { ...missionForm }
    if (missionEditId.value) {
      await http.put(`/uav/missions/${missionEditId.value}`, body)
    } else {
      await http.post('/uav/missions', body)
    }
    ElMessage.success('已保存')
    missionDlg.value = false
    loadMissions()
    loadStats()
  } finally {
    missionSaving.value = false
  }
}

async function removeMission(row) {
  await ElMessageBox.confirm(`确定删除任务「${row.name}」？`, '删除确认', { type: 'warning' })
  await http.delete(`/uav/missions/${row.id}`)
  ElMessage.success('已删除')
  loadMissions()
  loadStats()
}

async function uploadFile(opt, form, field) {
  const fd = new FormData()
  fd.append('file', opt.file)
  try {
    const res = await axios.post('/api/v1/platform/upload', fd, {
      headers: auth.token ? { Authorization: `Bearer ${auth.token}` } : {},
    })
    const envelope = res.data
    if (envelope?.code != null && envelope.code !== 0) throw new Error(envelope.message || '上传失败')
    const data = envelope?.data ?? envelope
    if (!form[field]) form[field] = []
    form[field].push(data.url)
    opt.onSuccess?.(data)
  } catch (e) {
    opt.onError?.(e)
  }
}

function removeFile(file, form, field) {
  form[field] = (form[field] || []).filter((u) => u !== file.url)
}

onMounted(async () => {
  await loadStats()
  await loadPilots()
  await loadMissions()
})
</script>

<style scoped>
.uav-page { min-height: 520px; }
.stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 20px; }
.stat-card { background: linear-gradient(135deg, #f0f7ff 0%, #fff 100%); border: 1px solid #e4e9f2; border-radius: 8px; padding: 16px 20px; }
.stat-label { color: #606266; font-size: 13px; margin-bottom: 8px; }
.stat-val { font-size: 28px; font-weight: 600; color: #303133; }
.stat-val.warn { color: #e6a23c; }
.unit { font-size: 14px; font-weight: normal; margin-left: 4px; color: #909399; }
.uav-tabs { margin-top: 8px; }
.toolbar { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 12px; align-items: center; }
.hint { font-size: 12px; color: #909399; margin: 4px 0 0; }
@media (max-width: 900px) { .stats { grid-template-columns: repeat(2, 1fr); } }
</style>
