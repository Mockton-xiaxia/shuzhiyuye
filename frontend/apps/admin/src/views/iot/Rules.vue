<template>
  <SimpleTablePage title="告警规则" :rows="list" :columns="cols" :actions="[{label:'新增规则', onClick:create}]" />
</template>
<script setup>
import { onMounted, ref } from 'vue'
import { ElMessageBox } from 'element-plus'
import http from '@/api/http'
import SimpleTablePage from '@/components/SimpleTablePage.vue'
const list = ref([])
const cols = [
  { prop: 'name', label: '名称' },
  { prop: 'pointCode', label: '指标', width: 100 },
  { prop: 'operator', label: '条件', width: 80 },
  { prop: 'threshold', label: '阈值', width: 80 },
  { prop: 'enabled', label: '启用', width: 80 },
]
async function load() {
  list.value = (await http.get('/iot/rules')).data || []
}
async function create() {
  const { value } = await ElMessageBox.prompt('规则名')
  await http.post('/iot/rules', { name: value, pointCode: 'DO', operator: 'LT', threshold: 3 })
  load()
}
onMounted(load)
</script>
