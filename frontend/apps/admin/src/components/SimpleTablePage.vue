<template>
  <div class="page-card">
    <h2 class="page-title">{{ title }}</h2>
    <div v-if="actions.length" style="margin-bottom:12px">
      <el-button v-for="a in actions" :key="a.label" type="primary" size="small" @click="a.onClick">{{ a.label }}</el-button>
    </div>
    <el-table :data="rows" stripe v-loading="loading">
      <el-table-column v-for="c in columns" :key="c.prop" :prop="c.prop" :label="c.label" :width="c.width" />
      <el-table-column v-if="rowActions" label="操作" width="220">
        <template #default="{ row }">
          <el-button v-for="ra in rowActions(row)" :key="ra.label" link type="primary" @click="ra.onClick(row)">{{ ra.label }}</el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>
<script setup>
defineProps({
  title: String,
  rows: { type: Array, default: () => [] },
  columns: { type: Array, default: () => [] },
  loading: Boolean,
  actions: { type: Array, default: () => [] },
  rowActions: { type: Function, default: null },
})
</script>
