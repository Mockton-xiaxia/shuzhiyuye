<template>
  <div class="page-card">
    <h2 class="page-title">字典管理</h2>
    <el-row :gutter="16">
      <el-col :span="8">
        <el-table :data="types" size="small" @row-click="loadItems" highlight-current-row>
          <el-table-column prop="code" label="编码" />
          <el-table-column prop="name" label="名称" />
        </el-table>
      </el-col>
      <el-col :span="16">
        <el-table :data="items" size="small">
          <el-table-column prop="label" label="标签" />
          <el-table-column prop="value" label="值" />
          <el-table-column prop="sortNo" label="排序" width="80" />
        </el-table>
      </el-col>
    </el-row>
  </div>
</template>
<script setup>
import { onMounted, ref } from 'vue'
import http from '@/api/http'
const types = ref([]); const items = ref([])
async function loadItems(row) { items.value = (await http.get(`/system/dicts/${row.code}/items`)).data || [] }
onMounted(async () => { types.value = (await http.get('/system/dict-types')).data || [] })
</script>
