<template>
  <SimpleTablePage title="审计日志" :rows="list" :columns="cols" />
</template>
<script setup>
import { onMounted, ref } from 'vue'
import http from '@/api/http'
import SimpleTablePage from '@/components/SimpleTablePage.vue'
const list = ref([])
const cols = [
  { prop: 'username', label: '用户', width: 120 },
  { prop: 'action', label: '动作', width: 140 },
  { prop: 'resource', label: '资源' },
  { prop: 'createdAt', label: '时间', width: 180 },
]
onMounted(async () => { list.value = ((await http.get('/system/audit-logs')).data?.list) || [] })
</script>
