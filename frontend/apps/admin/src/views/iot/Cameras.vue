<template>
  <div class="page-card">
    <h2 class="page-title">视频监控（萤石适配器）</h2>
    <el-table :data="list" stripe>
      <el-table-column prop="name" label="名称" />
      <el-table-column prop="deviceSerial" label="序列号" />
      <el-table-column prop="provider" label="厂商" width="100" />
      <el-table-column prop="scene" label="场景" width="100" />
      <el-table-column label="操作" width="120">
        <template #default="{ row }"><el-button link type="primary" @click="play(row)">取流</el-button></template>
      </el-table-column>
    </el-table>
    <el-dialog v-model="show" title="play-url" width="520px"><pre>{{ info }}</pre></el-dialog>
  </div>
</template>
<script setup>
import { onMounted, ref } from 'vue'
import http from '@/api/http'
const list=ref([]); const show=ref(false); const info=ref('')
async function load(){ list.value=(await http.get('/iot/cameras')).data||[] }
async function play(row){ info.value=JSON.stringify((await http.get(`/iot/cameras/${row.id}/play-url`)).data,null,2); show.value=true }
onMounted(load)
</script>
