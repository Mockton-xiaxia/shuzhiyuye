<template>
  <div class="page-card">
    <h2 class="page-title">投入品</h2>
    <el-table :data="list" stripe>
      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column prop="name" label="名称" />
      <el-table-column prop="category" label="类别" width="100" />
      <el-table-column prop="unit" label="单位" width="80" />
      <el-table-column prop="withdrawalDays" label="休药天数" width="100" />
    </el-table>
  </div>
</template>
<script setup>
import { onMounted, ref } from 'vue'
import http from '@/api/http'
const list=ref([])
onMounted(async()=>{ list.value=(await http.get('/inputs/items')).data||[] })
</script>
