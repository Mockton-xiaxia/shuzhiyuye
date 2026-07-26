<template>
  <div class="page-card">
    <div class="bar"><h2 class="page-title">客户账本</h2><el-button type="primary" @click="open=true">记账</el-button></div>
    <el-table :data="list" stripe>
      <el-table-column prop="title" label="摘要" />
      <el-table-column prop="entryType" label="类型" width="100" />
      <el-table-column prop="amount" label="金额" width="120" />
      <el-table-column prop="batchId" label="批次" width="90" />
      <el-table-column prop="occurredAt" label="日期" width="120" />
    </el-table>
    <el-dialog v-model="open" title="记一笔" width="420px">
      <el-form label-width="80px">
        <el-form-item label="摘要"><el-input v-model="form.title" /></el-form-item>
        <el-form-item label="类型"><el-select v-model="form.entryType"><el-option label="收入" value="INCOME" /><el-option label="支出" value="EXPENSE" /></el-select></el-form-item>
        <el-form-item label="金额"><el-input-number v-model="form.amount" :min="0" /></el-form-item>
        <el-form-item label="批次"><el-input-number v-model="form.batchId" :min="0" /></el-form-item>
      </el-form>
      <template #footer><el-button type="primary" @click="save">保存</el-button></template>
    </el-dialog>
  </div>
</template>
<script setup>
import { onMounted, reactive, ref } from 'vue'
import http from '@/api/http'
const list=ref([]); const open=ref(false)
const form=reactive({ title:'饲料采购', entryType:'EXPENSE', amount:100, batchId:null })
async function load(){ list.value=(await http.get('/ledger/entries')).data||[] }
async function save(){ const p={...form}; if(!p.batchId) delete p.batchId; await http.post('/ledger/entries', p); open.value=false; load() }
onMounted(load)
</script>
<style scoped>.bar{display:flex;justify-content:space-between;align-items:center}</style>
