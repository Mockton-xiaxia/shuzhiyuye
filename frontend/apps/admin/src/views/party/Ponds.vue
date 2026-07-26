<template>
  <div class="page-card">
    <div class="bar">
      <h2 class="page-title">塘口测绘 / 审核</h2>
      <el-button v-if="isEnt" type="primary" @click="open=true">新建塘口</el-button>
    </div>
    <el-table :data="list" stripe>
      <el-table-column prop="name" label="塘口" />
      <el-table-column prop="areaMu" label="面积亩" width="90" />
      <el-table-column prop="layerType" label="图层" width="120" />
      <el-table-column prop="auditStatus" label="审核状态" width="110" />
      <el-table-column label="操作" width="220">
        <template #default="{ row }">
          <el-button v-if="isEnt && ['DRAFT','REJECTED'].includes(row.auditStatus)" link @click="submit(row)">提交审核</el-button>
          <el-button v-if="isGov && row.auditStatus==='PENDING'" link type="success" @click="audit(row,true)">通过</el-button>
          <el-button v-if="isGov && row.auditStatus==='PENDING'" link type="danger" @click="audit(row,false)">驳回</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-dialog v-model="open" title="新建塘口测绘" width="520px">
      <el-form label-width="100px">
        <el-form-item label="名称"><el-input v-model="form.name" /></el-form-item>
        <el-form-item label="面积亩"><el-input-number v-model="form.areaMu" :min="0" :step="0.1" /></el-form-item>
        <el-form-item label="品种"><el-input v-model="form.species" /></el-form-item>
        <el-form-item label="经度"><el-input-number v-model="form.lng" :step="0.001" /></el-form-item>
        <el-form-item label="纬度"><el-input-number v-model="form.lat" :step="0.001" /></el-form-item>
        <el-form-item label="GeoJSON"><el-input v-model="form.geomGeojson" type="textarea" :rows="3" /></el-form-item>
      </el-form>
      <template #footer><el-button type="primary" @click="create">保存草稿</el-button></template>
    </el-dialog>
  </div>
</template>
<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import http from '@/api/http'
import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'
import { DEMO_MAP_CENTER } from '@/config/demoMap'
const auth = useAuthStore()
const isGov = computed(() => auth.portal === 'GOV')
const isEnt = computed(() => auth.portal === 'ENT')
const list = ref([]); const open = ref(false)
const form = reactive({
  name: '', areaMu: 10, species: '大鲵', lng: DEMO_MAP_CENTER.lng, lat: DEMO_MAP_CENTER.lat,
  geomGeojson: '{"type":"Polygon","coordinates":[[[120.150,30.243],[120.152,30.243],[120.152,30.245],[120.150,30.245],[120.150,30.243]]]}',
  layerType: 'AQUACULTURE',
})
async function load(){ list.value = ((await http.get('/party/ponds')).data?.list) || [] }
async function create(){ await http.post('/party/ponds', form); open.value=false; ElMessage.success('已保存'); load() }
async function submit(row){ await http.post(`/party/ponds/${row.id}/submit`); ElMessage.success('已提交'); load() }
async function audit(row, approved){ await http.post(`/party/ponds/${row.id}/audit`, { approved, opinion: approved?'同意':'请修改范围' }); load() }
onMounted(load)
</script>
<style scoped>.bar{display:flex;justify-content:space-between;align-items:center}</style>
