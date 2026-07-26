<template>
  <SimpleTablePage title="指挥调度" :rows="list" :columns="cols"
    :actions="isGov?[{label:'下发调度', onClick:create}]:[]"
    :row-actions="rowActions" />
</template>
<script setup>
import { computed, onMounted, ref } from 'vue'
import { ElMessageBox } from 'element-plus'
import http from '@/api/http'
import { useAuthStore } from '@/stores/auth'
import SimpleTablePage from '@/components/SimpleTablePage.vue'
const auth=useAuthStore(); const isGov=computed(()=>auth.portal==='GOV'); const isEnt=computed(()=>auth.portal==='ENT')
const list=ref([])
const cols=[{prop:'title',label:'标题'},{prop:'status',label:'状态',width:100},{prop:'feedback',label:'反馈'},{prop:'enterpriseId',label:'主体',width:80}]
async function load(){ list.value=(await http.get('/effluent/dispatches')).data||[] }
async function create(){ const {value}=await ElMessageBox.prompt('调度标题'); await http.post('/effluent/dispatches',{title:value,enterpriseId:1,content:value}); load() }
function rowActions(row){
  const arr=[]
  if(isEnt.value && row.status==='PENDING') arr.push({label:'接收', onClick: async()=>{ await http.post(`/effluent/dispatches/${row.id}/accept`); load() }})
  if(isEnt.value && ['PENDING','DOING'].includes(row.status)) arr.push({label:'反馈', onClick: async()=>{ const {value}=await ElMessageBox.prompt('反馈'); await http.post(`/effluent/dispatches/${row.id}/feedback`,{feedback:value}); load() }})
  return arr
}
onMounted(load)
</script>
