<template>
  <SimpleTablePage title="预警信息" :rows="list" :columns="cols" :actions="isGov ? [{label:'发布预警', onClick:create}] : []" />
</template>
<script setup>
import { computed, onMounted, ref } from 'vue'
import { ElMessageBox } from 'element-plus'
import http from '@/api/http'
import { useAuthStore } from '@/stores/auth'
import SimpleTablePage from '@/components/SimpleTablePage.vue'
const auth = useAuthStore()
const isGov = computed(() => auth.portal === 'GOV')
const list = ref([])
const cols = [
  { prop: 'title', label: '标题' },
  { prop: 'level', label: '级别', width: 90 },
  { prop: 'status', label: '状态', width: 100 },
  { prop: 'content', label: '内容' },
]
async function load() {
  list.value = (await http.get('/disease/alerts')).data || []
}
async function create() {
  const { value } = await ElMessageBox.prompt('预警标题')
  await http.post('/disease/alerts', { title: value, level: 'WARN', content: value })
  load()
}
onMounted(load)
</script>
