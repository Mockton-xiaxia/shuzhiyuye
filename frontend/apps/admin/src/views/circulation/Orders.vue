<template>
  <SimpleTablePage title="流通订单" :rows="list" :columns="cols" :actions="[{label:'新建订单', onClick:create}]" />
</template>
<script setup>
import { onMounted, ref } from 'vue'
import { ElMessageBox } from 'element-plus'
import http from '@/api/http'
import SimpleTablePage from '@/components/SimpleTablePage.vue'
const list=ref([])
const cols=[{prop:'orderNo',label:'单号',width:140},{prop:'buyer',label:'买方'},{prop:'species',label:'品种',width:100},{prop:'qty',label:'数量',width:90},{prop:'status',label:'状态',width:90}]
async function load(){ list.value=(await http.get('/circulation/orders')).data||[] }
async function create(){ const {value}=await ElMessageBox.prompt('买方'); await http.post('/circulation/orders',{buyer:value,species:'鲫鱼',qty:20}); load() }
onMounted(load)
</script>
