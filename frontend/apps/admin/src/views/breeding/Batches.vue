<template>
  <div class="page-card">
    <div class="bar"><h2 class="page-title">养殖批次</h2><el-button type="primary" @click="open=true">新建批次</el-button></div>
    <el-table :data="list" stripe>
      <el-table-column prop="batchNo" label="批次号" />
      <el-table-column prop="species" label="品种" width="100" />
      <el-table-column prop="pondId" label="塘口" width="80" />
      <el-table-column prop="status" label="状态" width="110" />
      <el-table-column prop="feedTotalKg" label="投喂kg" width="100" />
      <el-table-column prop="harvestKg" label="出塘kg" width="100" />
      <el-table-column prop="fcr" label="FCR" width="80" />
      <el-table-column label="操作" width="220">
        <template #default="{ row }">
          <el-button link type="primary" @click="showTimeline(row)">时间轴</el-button>
          <el-button v-if="row.status==='BREEDING'" link @click="harvest(row)">出塘</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-dialog v-model="open" title="新建批次" width="460px">
      <el-form label-width="90px">
        <el-form-item label="塘口ID"><el-input-number v-model="form.pondId" :min="1" /></el-form-item>
        <el-form-item label="批次号"><el-input v-model="form.batchNo" /></el-form-item>
        <el-form-item label="品种"><el-input v-model="form.species" /></el-form-item>
        <el-form-item label="投苗量"><el-input-number v-model="form.stockQty" :min="0" /></el-form-item>
      </el-form>
      <template #footer><el-button type="primary" @click="create">保存</el-button></template>
    </el-dialog>
    <el-drawer v-model="drawer" title="批次全链时间轴" size="420px">
      <pre style="white-space:pre-wrap;font-size:12px">{{ timeline }}</pre>
    </el-drawer>
  </div>
</template>
<script setup>
import { onMounted, reactive, ref } from 'vue'
import http from '@/api/http'
import { ElMessage, ElMessageBox } from 'element-plus'
const list=ref([]); const open=ref(false); const drawer=ref(false); const timeline=ref('')
const form=reactive({ pondId:1, batchNo:`B${Date.now().toString().slice(-6)}`, species:'大鲵', stockQty:100 })
async function load(){ list.value=(await http.get('/breeding/batches')).data||[] }
async function create(){ await http.post('/breeding/batches', form); open.value=false; load() }
async function showTimeline(row){ const r=await http.get(`/breeding/batches/${row.id}/timeline`); timeline.value=JSON.stringify(r.data,null,2); drawer.value=true }
async function harvest(row){
  const { value } = await ElMessageBox.prompt('出塘重量 kg', '出塘')
  await http.post('/breeding/harvests', { batchId: row.id, weightKg: Number(value) })
  ElMessage.success('出塘成功（已校验休药期）'); load()
}
onMounted(load)
</script>
<style scoped>.bar{display:flex;justify-content:space-between;align-items:center}</style>
