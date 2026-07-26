<template>
  <SimpleTablePage title="视频管理" :rows="list" :columns="cols" :actions="[{label:'新增视频', onClick:create}]" />
</template>
<script setup>
import { onMounted, ref } from 'vue'
import { ElMessageBox } from 'element-plus'
import http from '@/api/http'
import SimpleTablePage from '@/components/SimpleTablePage.vue'
const list = ref([])
const cols = [
  { prop: 'title', label: '标题' },
  { prop: 'category', label: '栏目', width: 120 },
  { prop: 'url', label: '链接' },
  { prop: 'views', label: '浏览', width: 80 },
]
async function load() {
  list.value = (await http.get('/cms/videos')).data || []
}
async function create() {
  const { value } = await ElMessageBox.prompt('视频标题')
  await http.post('/cms/videos', { title: value, url: 'https://example.com/v.mp4', category: '产业' })
  load()
}
onMounted(load)
</script>
