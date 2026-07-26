<template>
  <div class="page-card">
    <h2 class="page-title">资讯文章</h2>
    <el-table :data="list" stripe>
      <el-table-column prop="title" label="标题" />
      <el-table-column prop="category" label="类别" width="120" />
      <el-table-column prop="source" label="来源" width="120" />
      <el-table-column prop="views" label="阅读" width="80" />
    </el-table>
  </div>
</template>
<script setup>
import { onMounted, ref } from 'vue'
import http from '@/api/http'
const list=ref([])
onMounted(async()=>{ list.value=(await http.get('/cms/articles')).data||[] })
</script>
