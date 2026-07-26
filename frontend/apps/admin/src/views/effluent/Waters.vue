<template>
  <div class="page-card">
    <div class="bar"><h2 class="page-title">排放水域</h2><el-button type="primary" @click="open=true">新建</el-button></div>
    <el-table :data="list" stripe>
      <el-table-column prop="name" label="名称" /><el-table-column prop="code" label="编码" width="120" /><el-table-column prop="level" label="水质等级" width="120" />
    </el-table>
    <el-dialog v-model="open" title="新建水域" width="420px">
      <el-input v-model="form.name" placeholder="名称" style="margin-bottom:8px" />
      <el-input v-model="form.code" placeholder="编码" style="margin-bottom:8px" />
      <el-input v-model="form.level" placeholder="等级" />
      <template #footer><el-button type="primary" @click="save">保存</el-button></template>
    </el-dialog>
  </div>
</template>
<script setup>
import { onMounted, reactive, ref } from 'vue'
import http from '@/api/http'
const list=ref([]); const open=ref(false); const form=reactive({name:'',code:'',level:''})
async function load(){ list.value=(await http.get('/effluent/waters')).data||[] }
async function save(){ await http.post('/effluent/waters', form); open.value=false; load() }
onMounted(load)
</script>
<style scoped>.bar{display:flex;justify-content:space-between;align-items:center}</style>
