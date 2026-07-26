<template>
  <div class="page-card">
    <div class="bar"><h2 class="page-title">政策管理</h2><el-button type="primary" @click="open=true">新建</el-button></div>
    <el-table :data="list" stripe><el-table-column prop="name" label="政策名称" /><el-table-column prop="publishDate" label="日期" width="140" /></el-table>
    <el-dialog v-model="open" title="新建政策" width="420px">
      <el-input v-model="form.name" placeholder="政策名称" />
      <template #footer><el-button type="primary" @click="save">保存</el-button></template>
    </el-dialog>
  </div>
</template>
<script setup>
import { onMounted, reactive, ref } from 'vue'
import http from '@/api/http'
import { ElMessage } from 'element-plus'
const list = ref([]); const open = ref(false); const form = reactive({ name: '' })
async function load(){ list.value = (await http.get('/quality/policies')).data || [] }
async function save(){ await http.post('/quality/policies', form); open.value=false; ElMessage.success('已保存'); load() }
onMounted(load)
</script>
<style scoped>.bar{display:flex;justify-content:space-between;align-items:center}</style>
