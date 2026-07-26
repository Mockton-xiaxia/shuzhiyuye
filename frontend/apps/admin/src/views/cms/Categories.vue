<template>
  <SimpleTablePage title="栏目管理" :rows="list" :columns="cols" :actions="[{label:'新增栏目', onClick:create}]" />
</template>
<script setup>
import { onMounted, ref } from 'vue'
import { ElMessageBox } from 'element-plus'
import http from '@/api/http'
import SimpleTablePage from '@/components/SimpleTablePage.vue'
const list = ref([])
const cols = [
  { prop: 'name', label: '名称' },
  { prop: 'sortNo', label: '排序', width: 80 },
]
async function load() {
  list.value = (await http.get('/cms/categories')).data || []
}
async function create() {
  const { value } = await ElMessageBox.prompt('栏目名')
  await http.post('/cms/categories', { name: value, sortNo: 1 })
  load()
}
onMounted(load)
</script>
