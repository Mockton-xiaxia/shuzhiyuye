<template>
  <div class="page-card">
    <div class="bar"><h2 class="page-title">尾水排放计划</h2>
      <el-button type="primary" @click="open=true">新建</el-button>
    </div>
    <el-table :data="list" stripe>
      <el-table-column prop="title" label="标题" />
      <el-table-column prop="planMonth" label="月份" width="100" />
      <el-table-column prop="volume" label="计划量" width="100" />
      <el-table-column prop="status" label="状态" width="120" />
      <el-table-column label="操作" width="180">
        <template #default="{ row }">
          <el-button v-if="row.status==='DRAFT'" link @click="submit(row)">提交</el-button>
          <el-button v-if="isGov && row.status==='SUBMITTED'" link type="success" @click="file(row)">备案</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-dialog v-model="open" title="新建计划" width="460px">
      <el-form label-width="90px">
        <el-form-item label="标题"><el-input v-model="form.title" /></el-form-item>
        <el-form-item label="主体ID"><el-input-number v-model="form.enterpriseId" :min="1" /></el-form-item>
        <el-form-item label="月份"><el-input v-model="form.planMonth" placeholder="2026-07" /></el-form-item>
        <el-form-item label="水量"><el-input-number v-model="form.volume" :min="0" /></el-form-item>
      </el-form>
      <template #footer><el-button type="primary" @click="create">保存</el-button></template>
    </el-dialog>
  </div>
</template>
<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import http from '@/api/http'
import { useAuthStore } from '@/stores/auth'
const auth=useAuthStore(); const isGov=computed(()=>auth.portal==='GOV')
const list=ref([]); const open=ref(false)
const form=reactive({ title:'', enterpriseId: auth.user?.enterpriseId || 1, planMonth:'2026-07', volume:100 })
async function load(){ list.value=(await http.get('/effluent/plans')).data||[] }
async function create(){ await http.post('/effluent/plans', form); open.value=false; load() }
async function submit(row){ await http.post(`/effluent/plans/${row.id}/submit`); load() }
async function file(row){ await http.post(`/effluent/plans/${row.id}/file`); load() }
onMounted(load)
</script>
<style scoped>.bar{display:flex;justify-content:space-between;align-items:center}</style>
