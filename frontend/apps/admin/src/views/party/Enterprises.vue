<template>
  <div class="page-card">
    <h2 class="page-title">养殖主体</h2>
    <el-table :data="list" stripe>
      <el-table-column prop="name" label="名称" />
      <el-table-column prop="contactName" label="联系人" width="100" />
      <el-table-column prop="contactPhone" label="电话" width="130" />
      <el-table-column prop="areaMu" label="面积(亩)" width="100" />
      <el-table-column prop="species" label="品种" />
      <el-table-column prop="status" label="状态" width="100" />
    </el-table>
  </div>
</template>
<script setup>
import { onMounted, ref } from 'vue'
import http from '@/api/http'
const list = ref([])
onMounted(async () => { list.value = ((await http.get('/party/enterprises')).data?.list) || [] })
</script>
