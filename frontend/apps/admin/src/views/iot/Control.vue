<template>
  <div class="page-card">
    <div class="toolbar"><h2 class="page-title">设备控制</h2>
      <el-button type="primary" @click="send">下发指令</el-button>
    </div>
    <el-table :data="list" stripe>
      <el-table-column prop="deviceId" label="设备" width="90" />
      <el-table-column prop="command" label="指令" />
      <el-table-column prop="result" label="结果" width="100" />
      <el-table-column prop="detail" label="详情" />
    </el-table>
  </div>
</template>
<script setup>
import { onMounted, ref } from 'vue'
import { ElMessageBox } from 'element-plus'
import http from '@/api/http'
const list = ref([])
async function load() {
  list.value = (await http.get('/iot/commands')).data || []
}
async function send() {
  const { value } = await ElMessageBox.prompt('指令内容')
  await http.post('/iot/commands', { deviceId: 1, command: value || 'ON' })
  load()
}
onMounted(load)
</script>
