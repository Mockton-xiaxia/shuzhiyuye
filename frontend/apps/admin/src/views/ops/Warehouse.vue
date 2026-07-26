<template>
  <div class="page-card">
    <h2 class="page-title">仓库库存</h2>
    <el-row :gutter="16">
      <el-col :span="10">
        <h4>仓库</h4>
        <el-table :data="warehouses" size="small"><el-table-column prop="id" width="60" label="ID" /><el-table-column prop="name" label="名称" /></el-table>
      </el-col>
      <el-col :span="14">
        <div class="bar"><h4>库存</h4><el-button size="small" type="primary" @click="open=true">入库</el-button></div>
        <el-table :data="stocks" size="small">
          <el-table-column prop="warehouseId" label="仓" width="70" />
          <el-table-column prop="itemId" label="品" width="70" />
          <el-table-column prop="qty" label="数量" />
        </el-table>
      </el-col>
    </el-row>
    <el-dialog v-model="open" title="入库" width="400px">
      <el-form label-width="80px">
        <el-form-item label="仓ID"><el-input-number v-model="form.warehouseId" :min="1" /></el-form-item>
        <el-form-item label="品ID"><el-input-number v-model="form.itemId" :min="1" /></el-form-item>
        <el-form-item label="数量"><el-input-number v-model="form.qty" :min="0" /></el-form-item>
      </el-form>
      <template #footer><el-button type="primary" @click="save">确定</el-button></template>
    </el-dialog>
  </div>
</template>
<script setup>
import { onMounted, reactive, ref } from 'vue'
import http from '@/api/http'
const warehouses=ref([]); const stocks=ref([]); const open=ref(false)
const form=reactive({ warehouseId:1, itemId:1, qty:100 })
async function load(){
  warehouses.value=(await http.get('/wms/warehouses')).data||[]
  stocks.value=(await http.get('/wms/stocks')).data||[]
}
async function save(){ await http.post('/wms/stocks/in', form); open.value=false; load() }
onMounted(load)
</script>
<style scoped>.bar{display:flex;justify-content:space-between;align-items:center}</style>
