<template>
  <SimpleTablePage title="人员管理" :rows="list" :columns="cols" :actions="[{label:'新增人员', onClick:create}]" />
</template>
<script setup>
import { onMounted, ref } from 'vue'
import { ElMessageBox } from 'element-plus'
import http from '@/api/http'
import SimpleTablePage from '@/components/SimpleTablePage.vue'
const list=ref([])
const cols=[{prop:'name',label:'姓名'},{prop:'phone',label:'电话',width:130},{prop:'post',label:'岗位',width:120},{prop:'status',label:'状态',width:80}]
async function load(){ list.value=(await http.get('/party/staffs')).data||[] }
async function create(){ const {value}=await ElMessageBox.prompt('姓名'); await http.post('/party/staffs',{name:value,post:'养殖员'}); load() }
onMounted(load)
</script>
