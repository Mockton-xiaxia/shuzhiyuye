<template>
  <div class="page-card">
    <div class="bar"><h2 class="page-title">水质设备</h2><el-button @click="mock">模拟上报低溶氧</el-button></div>
    <el-table :data="list" stripe>
      <el-table-column prop="name" label="名称" />
      <el-table-column prop="deviceNo" label="编号" />
      <el-table-column prop="deviceType" label="类型" width="100" />
      <el-table-column prop="status" label="状态" width="100" />
    </el-table>
  </div>
</template>
<script setup>
import { onMounted, ref } from 'vue'
import http from '@/api/http'
import { ElMessage } from 'element-plus'
const list=ref([])
async function load(){ list.value=(await http.get('/iot/devices')).data||[] }
async function mock(){
  if(!list.value.length) return
  await http.post('/iot/telemetry', { deviceId: list.value[0].id, pointCode:'DO', pointValue: 3.5 })
  ElMessage.success('已上报，若触发规则将生成告警待办')
}
onMounted(load)
</script>
<style scoped>.bar{display:flex;justify-content:space-between;align-items:center}</style>
