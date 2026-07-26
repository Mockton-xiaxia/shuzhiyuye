<template>
  <div class="page-card">
    <div class="bar"><h2 class="page-title">农事记录</h2><el-button type="primary" @click="open=true">记一笔</el-button></div>
    <el-table :data="list" stripe>
      <el-table-column prop="batchId" label="批次" width="80" />
      <el-table-column prop="activityType" label="类型" width="100" />
      <el-table-column prop="title" label="内容" />
      <el-table-column prop="qty" label="数量" width="90" />
      <el-table-column prop="unit" label="单位" width="80" />
      <el-table-column prop="withdrawalUntil" label="休药至" width="120" />
    </el-table>
    <el-dialog v-model="open" title="农事 / 用药 / 投喂" width="520px">
      <el-form label-width="100px">
        <el-form-item label="批次ID"><el-input-number v-model="form.batchId" :min="1" /></el-form-item>
        <el-form-item label="类型">
          <el-select v-model="form.activityType">
            <el-option label="投喂" value="FEED" /><el-option label="用药" value="MEDICINE" /><el-option label="其他" value="OTHER" />
          </el-select>
        </el-form-item>
        <el-form-item label="标题"><el-input v-model="form.title" /></el-form-item>
        <el-form-item label="数量"><el-input-number v-model="form.qty" :min="0" /></el-form-item>
        <el-form-item label="投入品ID"><el-input-number v-model="form.inputItemId" :min="0" /></el-form-item>
        <el-form-item label="仓库ID"><el-input-number v-model="form.warehouseId" :min="0" /></el-form-item>
      </el-form>
      <template #footer><el-button type="primary" @click="create">保存</el-button></template>
    </el-dialog>
  </div>
</template>
<script setup>
import { onMounted, reactive, ref } from 'vue'
import http from '@/api/http'
import { ElMessage } from 'element-plus'
const list=ref([]); const open=ref(false)
const form=reactive({ batchId:1, activityType:'FEED', title:'投喂', qty:10, inputItemId:null, warehouseId:null, unit:'kg' })
async function load(){ list.value=(await http.get('/breeding/activities')).data||[] }
async function create(){
  const payload={...form}
  if(!payload.inputItemId) delete payload.inputItemId
  if(!payload.warehouseId) delete payload.warehouseId
  const r=await http.post('/breeding/activities', payload)
  ElMessage.success(r.data?.withdrawalUntil ? `已记录，休药至 ${r.data.withdrawalUntil}` : '已记录')
  open.value=false; load()
}
onMounted(load)
</script>
<style scoped>.bar{display:flex;justify-content:space-between;align-items:center}</style>
