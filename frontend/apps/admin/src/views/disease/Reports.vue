<template>
  <SimpleTablePage title="病情测报" :rows="list" :columns="cols" :actions="[{label:'新建上报', onClick:create}]" />
</template>
<script setup>
import { onMounted, ref } from 'vue'
import { ElMessageBox } from 'element-plus'
import http from '@/api/http'
import SimpleTablePage from '@/components/SimpleTablePage.vue'
const list = ref([])
const cols = [
  { prop: 'title', label: '标题' },
  { prop: 'symptom', label: '症状' },
  { prop: 'status', label: '状态', width: 110 },
  { prop: 'enterpriseId', label: '主体', width: 80 },
]
async function load() {
  list.value = (await http.get('/disease/reports')).data || []
}
async function create() {
  const { value } = await ElMessageBox.prompt('标题')
  await http.post('/disease/reports', { title: value, symptom: '待观察' })
  load()
}
onMounted(load)
</script>
