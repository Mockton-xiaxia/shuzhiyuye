<template>
  <SimpleTablePage title="检测机构" :rows="list" :columns="cols" :actions="[{label:'新建', onClick: create}]" />
</template>
<script setup>
import { onMounted, ref } from 'vue'
import { ElMessageBox } from 'element-plus'
import http from '@/api/http'
import SimpleTablePage from '@/components/SimpleTablePage.vue'
const list = ref([])
const cols = [
  { prop: 'name', label: '名称' },
  { prop: 'contact', label: '联系人', width: 100 },
  { prop: 'phone', label: '电话', width: 130 },
]
async function load(){ list.value=(await http.get('/quality/labs')).data||[] }
async function create(){ const {value}=await ElMessageBox.prompt('机构名称'); await http.post('/quality/labs',{name:value}); load() }
onMounted(load)
</script>
