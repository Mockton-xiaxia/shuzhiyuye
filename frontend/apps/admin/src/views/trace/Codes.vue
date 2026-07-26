<template>
  <div class="page-card">
    <h2 class="page-title">标识分发 / 码列表</h2>
    <el-table :data="list" stripe>
      <el-table-column prop="code" label="追溯码" min-width="180" />
      <el-table-column prop="batchId" label="批次" width="100" />
      <el-table-column prop="status" label="状态" width="100" />
      <el-table-column label="公开页" width="140">
        <template #default="{ row }">
          <el-button link type="primary" @click="open(row.code)">查看</el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>
<script setup>
import { onMounted, ref } from 'vue'
import http from '@/api/http'
const list = ref([])
async function load(){ list.value = (await http.get('/trace/codes')).data || [] }
function open(code){ window.open(`/p/trace/${code}`, '_blank') }
onMounted(load)
</script>
