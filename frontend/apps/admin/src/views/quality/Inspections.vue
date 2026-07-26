<template>
  <div class="page-card">
    <div class="bar"><h2 class="page-title">质量抽检</h2>
      <el-button v-if="isGov" type="primary" @click="open=true">新建抽检</el-button>
    </div>
    <el-table :data="list" stripe>
      <el-table-column prop="title" label="标题" />
      <el-table-column prop="result" label="结果" width="120" />
      <el-table-column prop="status" label="状态" width="120" />
      <el-table-column label="操作" width="120">
        <template #default="{ row }">
          <el-button v-if="row.status==='DRAFT'" link type="primary" @click="submit(row)">提交</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-dialog v-model="open" title="新建抽检" width="480px">
      <el-form label-width="90px">
        <el-form-item label="标题"><el-input v-model="form.title" /></el-form-item>
        <el-form-item label="主体ID"><el-input-number v-model="form.enterpriseId" :min="1" /></el-form-item>
        <el-form-item label="结果">
          <el-select v-model="form.result"><el-option label="合格" value="QUALIFIED" /><el-option label="不合格" value="UNQUALIFIED" /></el-select>
        </el-form-item>
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
const auth = useAuthStore(); const isGov = computed(() => auth.portal === 'GOV')
const list = ref([]); const open = ref(false)
const form = reactive({ title: '', enterpriseId: 1, result: 'UNQUALIFIED' })
async function load(){ list.value = (await http.get('/quality/inspections')).data || [] }
async function create(){ await http.post('/quality/inspections', form); open.value=false; load() }
async function submit(row){ await http.post(`/quality/inspections/${row.id}/submit`); ElMessage.success('已提交，不合格将自动生成整改'); load() }
onMounted(load)
</script>
<style scoped>.bar{display:flex;justify-content:space-between;align-items:center}</style>
