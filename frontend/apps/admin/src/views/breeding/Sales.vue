<template>
  <SimpleTablePage title="销售记录" :rows="list" :columns="cols" :actions="[{label:'登记销售', onClick:create}]" />
</template>
<script setup>
import { onMounted, ref } from 'vue'
import { ElMessageBox } from 'element-plus'
import http from '@/api/http'
import SimpleTablePage from '@/components/SimpleTablePage.vue'
const list = ref([])
const cols = [
  { prop: 'customerName', label: '买方' },
  { prop: 'species', label: '品种', width: 100 },
  { prop: 'weightKg', label: '重量kg', width: 90 },
  { prop: 'amount', label: '金额', width: 100 },
  { prop: 'soldAt', label: '日期', width: 120 },
]
async function load() {
  list.value = (await http.get('/breeding/sales')).data || []
}
async function create() {
  const { value } = await ElMessageBox.prompt('买方')
  await http.post('/breeding/sales', { customerName: value, species: '鲫鱼', weightKg: 50, amount: 600 })
  load()
}
onMounted(load)
</script>
