<template>
  <SimpleTablePage title="售后服务" :rows="list" :columns="cols" :actions="[{label:'新建工单', onClick:create}]" />
</template>
<script setup>
import { onMounted, ref } from 'vue'
import { ElMessageBox } from 'element-plus'
import http from '@/api/http'
import SimpleTablePage from '@/components/SimpleTablePage.vue'
const list = ref([])
const cols = [
  { prop: 'title', label: '标题' },
  { prop: 'status', label: '状态', width: 100 },
  { prop: 'content', label: '内容' },
]
async function load() {
  list.value = (await http.get('/ledger/after-sales')).data || []
}
async function create() {
  const { value } = await ElMessageBox.prompt('售后标题')
  await http.post('/ledger/after-sales', { title: value, content: value })
  load()
}
onMounted(load)
</script>
