<template>
  <SimpleTablePage title="角色管理" :rows="list" :columns="cols" />
</template>
<script setup>
import { onMounted, ref } from 'vue'
import http from '@/api/http'
import SimpleTablePage from '@/components/SimpleTablePage.vue'
const list = ref([])
const cols = [
  { prop: 'code', label: '编码' },
  { prop: 'name', label: '名称' },
  { prop: 'portal', label: '门户', width: 100 },
  { prop: 'status', label: '状态', width: 80 },
]
onMounted(async () => { list.value = (await http.get('/system/roles')).data || [] })
</script>
