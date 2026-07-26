<template>
  <SimpleTablePage title="供应大厅" :rows="list" :columns="cols" :actions="isGov ? [{label:'发布供应', onClick:create}] : []" />
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
  { prop: 'category', label: '类别', width: 100 },
  { prop: 'supplierName', label: '供应商' },
  { prop: 'contact', label: '联系人', width: 100 },
  { prop: 'phone', label: '电话', width: 120 },
]
async function load() {
  list.value = (await http.get('/supply/listings')).data || []
}
async function create() {
  const { value } = await ElMessageBox.prompt('供应标题')
  await http.post('/supply/listings', { title: value, category: '苗种', supplierName: '示范供应商' })
  load()
}
onMounted(load)
</script>
