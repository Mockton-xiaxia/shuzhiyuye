<template>
  <div class="page-card">
    <div class="bar">
      <h2 class="page-title">库存盘点</h2>
      <div>
        <el-button type="primary" @click="openCreate">新增盘存</el-button>
        <el-button @click="load">刷新</el-button>
      </div>
    </div>
    <el-table :data="rows" stripe>
      <el-table-column prop="id" label="单号" width="80" />
      <el-table-column prop="title" label="盘点标题" />
      <el-table-column prop="warehouseId" label="仓库" width="90" />
      <el-table-column prop="status" label="状态" width="100" />
      <el-table-column prop="remark" label="备注" />
      <el-table-column label="操作" width="160">
        <template #default="{ row }">
          <el-button v-if="row.status==='DRAFT'" link type="success" @click="post(row)">过账</el-button>
          <el-button link type="primary" @click="viewRow(row)">查看</el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import http from '@/api/http'

const rows = ref([])

async function load() {
  const res = await http.get('/wms/stocktakes')
  rows.value = res.data || []
}

async function openCreate() {
  const { value } = await ElMessageBox.prompt('盘点标题', '新增盘存', { inputValue: '月度盘存' })
  let warehouseId = 1
  try {
    const wh = await http.get('/wms/warehouses')
    warehouseId = wh.data?.[0]?.id || 1
  } catch {
    /* default */
  }
  await http.post('/wms/stocktakes', { warehouseId, title: value })
  ElMessage.success('已创建盘点单')
  load()
}

async function post(row) {
  await http.post(`/wms/stocktakes/${row.id}/post`)
  ElMessage.success('已过账')
  load()
}

function viewRow(row) {
  ElMessage.info(row.title || String(row.id))
}

onMounted(load)
</script>

<style scoped>
.bar { display:flex; justify-content:space-between; margin-bottom:12px; }
</style>
