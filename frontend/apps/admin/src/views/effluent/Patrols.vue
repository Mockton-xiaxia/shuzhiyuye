<template>
  <SimpleTablePage title="巡检记录" :rows="list" :columns="cols" :actions="[{label:'登记巡检', onClick:create}]" />
</template>
<script setup>
import { onMounted, ref } from 'vue'
import { ElMessageBox } from 'element-plus'
import http from '@/api/http'
import { useAuthStore } from '@/stores/auth'
import SimpleTablePage from '@/components/SimpleTablePage.vue'
const auth=useAuthStore()
const list=ref([])
const cols=[{prop:'title',label:'标题'},{prop:'result',label:'结果',width:120},{prop:'status',label:'状态',width:100},{prop:'enterpriseId',label:'主体',width:80}]
async function load(){ list.value=(await http.get('/effluent/patrols')).data||[] }
async function create(){
  const {value}=await ElMessageBox.prompt('巡检标题')
  await http.post('/effluent/patrols',{title:value, enterpriseId: auth.user?.enterpriseId || 1, result:'正常'})
  load()
}
onMounted(load)
</script>
