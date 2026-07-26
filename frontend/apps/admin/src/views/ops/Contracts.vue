<template>
  <SimpleTablePage title="合同台账" :rows="list" :columns="cols" :actions="[{label:'新增合同', onClick:create}]" />
</template>
<script setup>
import { onMounted, ref } from 'vue'
import { ElMessageBox } from 'element-plus'
import http from '@/api/http'
import SimpleTablePage from '@/components/SimpleTablePage.vue'
const list = ref([])
const cols = [
  { prop: 'title', label: '标题' },
  { prop: 'customerId', label: '客户', width: 90 },
  { prop: 'amount', label: '金额', width: 100 },
  { prop: 'status', label: '状态', width: 90 },
]
async function load() {
  list.value = (await http.get('/ledger/contracts')).data || []
}
async function create() {
  const { value } = await ElMessageBox.prompt('合同标题')
  await http.post('/ledger/contracts', { title: value, amount: 10000 })
  load()
}
onMounted(load)
</script>
