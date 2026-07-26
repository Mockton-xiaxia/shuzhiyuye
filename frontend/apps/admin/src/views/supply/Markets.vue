<template>
  <SimpleTablePage title="市场管理" :rows="list" :columns="cols" :actions="[{label:'新增市场', onClick:create}]" />
</template>
<script setup>
import { onMounted, ref } from 'vue'
import { ElMessageBox } from 'element-plus'
import http from '@/api/http'
import SimpleTablePage from '@/components/SimpleTablePage.vue'
const list = ref([])
const cols = [
  { prop: 'name', label: '名称' },
  { prop: 'region', label: '区域' },
  { prop: 'lng', label: '经度', width: 100 },
  { prop: 'lat', label: '纬度', width: 100 },
]
async function load() {
  list.value = (await http.get('/supply/markets')).data || []
}
async function create() {
  const { value } = await ElMessageBox.prompt('市场名称')
  await http.post('/supply/markets', { name: value, region: '示范县' })
  load()
}
onMounted(load)
</script>
