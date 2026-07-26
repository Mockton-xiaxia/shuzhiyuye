<template>
  <div class="page-card">
    <h2 class="page-title">工作台 · 待办</h2>
    <div class="stat-grid" style="margin-bottom:16px">
      <div class="stat-item"><div class="label">待处理</div><div class="value">{{ pending }}</div></div>
      <div class="stat-item"><div class="label">全部</div><div class="value">{{ total }}</div></div>
    </div>
    <el-table :data="list" stripe>
      <el-table-column prop="title" label="标题" min-width="220" />
      <el-table-column prop="bizType" label="类型" width="160">
        <template #default="{ row }">{{ bizTypeLabel(row.bizType) }}</template>
      </el-table-column>
      <el-table-column prop="status" label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="row.status === 'PENDING' ? 'warning' : 'success'" size="small">
            {{ statusLabel(row.status) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="180">
        <template #default="{ row }">
          <el-button link type="primary" @click="$router.push(row.linkPath || '/workbench')">进入</el-button>
          <el-button v-if="row.status==='PENDING'" link type="success" @click="done(row)">完成</el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import http from '@/api/http'
import { ElMessage } from 'element-plus'
import { bizTypeLabel, statusLabel } from '@/utils/labels'

const list = ref([])
const total = ref(0)
const pending = computed(() => list.value.filter((x) => x.status === 'PENDING').length)

async function load() {
  const res = await http.get('/todos', { params: { page: 1, size: 50 } })
  list.value = res.data.list || []
  total.value = res.data.total || 0
}
async function done(row) {
  await http.post(`/todos/${row.id}/done`)
  ElMessage.success('已完成')
  load()
}
onMounted(load)
</script>
