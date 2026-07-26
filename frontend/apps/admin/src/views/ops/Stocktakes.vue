<template>
  <SimpleTablePage title="库存盘点" :rows="list" :columns="cols" :actions="[{label:'新建盘点', onClick:create}]" :row-actions="rowActions" />
</template>
<script setup>
import { onMounted, ref } from 'vue'
import { ElMessageBox } from 'element-plus'
import http from '@/api/http'
import SimpleTablePage from '@/components/SimpleTablePage.vue'
const list = ref([])
const cols = [
  { prop: 'title', label: '标题' },
  { prop: 'warehouseId', label: '仓库', width: 90 },
  { prop: 'status', label: '状态', width: 100 },
  { prop: 'remark', label: '备注' },
]
async function load() {
  list.value = (await http.get('/wms/stocktakes')).data || []
}
async function create() {
  const { value } = await ElMessageBox.prompt('盘点标题')
  await http.post('/wms/stocktakes', { title: value, warehouseId: 1 })
  load()
}
function rowActions(row) {
  if (row.status === 'DRAFT') {
    return [{ label: '过账', onClick: async () => { await http.post(`/wms/stocktakes/${row.id}/post`); load() } }]
  }
  return []
}
onMounted(load)
</script>
