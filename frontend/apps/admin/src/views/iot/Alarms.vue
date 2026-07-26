<template>
  <div class="page-card">
    <h2 class="page-title">设备预警</h2>
    <el-table :data="list" stripe>
      <el-table-column prop="title" label="标题" />
      <el-table-column prop="content" label="内容" />
      <el-table-column prop="status" label="状态" width="100" />
      <el-table-column prop="occurredAt" label="时间" width="180" />
      <el-table-column label="操作" width="200">
        <template #default="{ row }">
          <el-button v-if="row.cameraId" link type="primary" @click="play(row.cameraId)">联动</el-button>
          <el-button v-if="row.status==='OPEN'" link type="primary" @click="ack(row.id)">确认</el-button>
          <el-button v-if="['OPEN','ACK'].includes(row.status)" link type="primary" @click="close(row.id)">关闭</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-dialog v-model="show" title="关联摄像头" width="480px"><pre>{{ info }}</pre></el-dialog>
  </div>
</template>
<script setup>
import { onMounted, ref } from 'vue'
import http from '@/api/http'
const list=ref([]); const show=ref(false); const info=ref('')
async function load(){ list.value=(await http.get('/iot/alarms')).data||[] }
async function play(id){ info.value=JSON.stringify((await http.get(`/iot/cameras/${id}/play-url`)).data,null,2); show.value=true }
async function ack(id){ await http.post(`/iot/alarms/${id}/ack`); load() }
async function close(id){ await http.post(`/iot/alarms/${id}/close`); load() }
onMounted(load)
</script>
