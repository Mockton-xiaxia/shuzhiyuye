<template>
  <div class="page-card">
    <h2 class="page-title">大鲵专项</h2>
    <el-table :data="list" stripe>
      <el-table-column prop="recordType" label="类型" width="120" />
      <el-table-column prop="title" label="标题" />
      <el-table-column prop="content" label="内容" />
      <el-table-column prop="status" label="状态" width="100" />
    </el-table>
  </div>
</template>
<script setup>
import { onMounted, ref } from 'vue'
import http from '@/api/http'
const list=ref([])
onMounted(async()=>{ list.value=(await http.get('/specialty/salamander')).data||[] })
</script>
