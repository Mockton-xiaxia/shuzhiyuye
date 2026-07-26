<template>
  <SimpleTablePage title="运输管理" :rows="list" :columns="cols" :actions="[{label:'登记运输', onClick:create}]" />
</template>
<script setup>
import { onMounted, ref } from 'vue'
import { ElMessageBox } from 'element-plus'
import http from '@/api/http'
import SimpleTablePage from '@/components/SimpleTablePage.vue'
const list=ref([])
const cols=[
  {prop:'plateNo',label:'车牌',width:120},
  {prop:'fromAddr',label:'起点'},
  {prop:'toAddr',label:'终点'},
  {prop:'status',label:'状态',width:90},
]
async function load(){ list.value=(await http.get('/circulation/transports')).data||[] }
async function create(){
  const {value}=await ElMessageBox.prompt('车牌')
  await http.post('/circulation/transports',{plateNo:value,fromAddr:'示范镇',toAddr:'示范市'})
  load()
}
onMounted(load)
</script>
