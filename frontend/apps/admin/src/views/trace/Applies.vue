<template>
  <div class="page-card">
    <div class="bar"><h2 class="page-title">标识申请</h2>
      <el-button v-if="isEnt" type="primary" @click="open=true">新建申请</el-button>
    </div>
    <el-table :data="list" stripe>
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="batchId" label="批次" width="100" />
      <el-table-column prop="applyQty" label="数量" width="80" />
      <el-table-column prop="status" label="状态" width="120" />
      <el-table-column label="操作" width="260">
        <template #default="{ row }">
          <el-button v-if="isEnt && ['DRAFT','REJECTED'].includes(row.status)" link @click="submit(row)">提交</el-button>
          <el-button v-if="isGov && row.status==='PENDING'" link type="success" @click="audit(row,true)">通过</el-button>
          <el-button v-if="isGov && row.status==='PENDING'" link type="danger" @click="audit(row,false)">驳回</el-button>
          <el-button v-if="isGov && row.status==='APPROVED'" link type="primary" @click="issue(row)">分发码</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-dialog v-model="open" title="申请追溯标识" width="420px">
      <el-form label-width="80px">
        <el-form-item label="批次ID"><el-input-number v-model="form.batchId" :min="1" /></el-form-item>
        <el-form-item label="数量"><el-input-number v-model="form.applyQty" :min="1" /></el-form-item>
      </el-form>
      <template #footer><el-button type="primary" @click="create">保存</el-button></template>
    </el-dialog>
  </div>
</template>
<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import http from '@/api/http'
import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'
const auth = useAuthStore(); const isGov = computed(()=>auth.portal==='GOV'); const isEnt = computed(()=>auth.portal==='ENT')
const list=ref([]); const open=ref(false); const form=reactive({ batchId:1, applyQty:5 })
async function load(){ list.value=(await http.get('/trace/applies')).data||[] }
async function create(){ await http.post('/trace/applies', form); open.value=false; load() }
async function submit(row){ await http.post(`/trace/applies/${row.id}/submit`); ElMessage.success('已提交'); load() }
async function audit(row, approved){ await http.post(`/trace/applies/${row.id}/audit`, { approved }); load() }
async function issue(row){ const r=await http.post(`/trace/applies/${row.id}/issue`); ElMessage.success(`已分发：${(r.data.codes||[]).join(',')}`); load() }
onMounted(load)
</script>
<style scoped>.bar{display:flex;justify-content:space-between;align-items:center}</style>
