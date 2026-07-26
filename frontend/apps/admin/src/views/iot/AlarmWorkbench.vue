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
      <el-form-item label="设备名称"><el-input v-model="q.deviceName" clearable style="width:140px" /></el-form-item>
      <el-form-item label="状态">
        <el-select v-model="q.status" clearable style="width:120px">
          <el-option label="未确认" value="OPEN" />
          <el-option label="已确认" value="ACK" />
          <el-option label="已关闭" value="CLOSED" />
        </el-select>
      </el-form-item>
    </el-form>
    <el-table :data="filtered" stripe v-loading="loading">
      <el-table-column prop="deviceName" label="设备名称" min-width="120" />
      <el-table-column prop="deviceNo" label="设备编号" min-width="120" />
      <el-table-column prop="deviceType" label="设备类型" width="90" />
      <el-table-column prop="title" label="预警信息" min-width="160" />
      <el-table-column prop="content" label="详情" min-width="140" show-overflow-tooltip />
      <el-table-column prop="status" label="状态" width="90">
        <template #default="{ row }"><el-tag size="small" :type="row.status==='OPEN'?'danger':row.status==='ACK'?'warning':'success'">{{ statusLabel(row.status) }}</el-tag></template>
      </el-table-column>
      <el-table-column prop="occurredAt" label="预警时间" min-width="160" />
      <el-table-column label="操作" width="160" fixed="right">
        <template #default="{ row }">
          <el-button v-if="row.status==='OPEN'" link type="warning" @click="ack(row)">确认</el-button>
          <el-button v-if="row.status==='OPEN' || row.status==='ACK'" link type="primary" @click="close(row)">关闭</el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import http from '@/api/http'

defineProps({ title: { type: String, default: '设备预警' } })

const rows = ref([])
const loading = ref(false)
const q = reactive({ deviceName: '', status: '' })

function statusLabel(s) {
  return ({ OPEN: '未确认', ACK: '已确认', CLOSED: '已关闭' })[s] || s
}

const filtered = computed(() =>
  rows.value.filter((r) => {
    if (q.status && r.status !== q.status) return false
    if (q.deviceName && !String(r.deviceName || '').includes(q.deviceName)) return false
    return true
  }),
)

async function load() {
  loading.value = true
  try {
    const res = await http.get('/iot/alarms')
    rows.value = res.data || []
  } finally {
    loading.value = false
  }
}
function reset() {
  q.deviceName = ''
  q.status = ''
  load()
}
async function ack(row) {
  await http.post(`/iot/alarms/${row.id}/ack`)
  ElMessage.success('已确认预警')
  load()
}
async function close(row) {
  await http.post(`/iot/alarms/${row.id}/close`)
  ElMessage.success('已关闭预警')
  load()
}

onMounted(load)
</script>

<style scoped>
.bar { display:flex; justify-content:space-between; align-items:center; margin-bottom:12px; }
.actions { display:flex; gap:8px; }
.filters { margin-bottom:8px; }
</style>
