<template>
  <SimpleTablePage title="尾水整改" :rows="list" :columns="cols"
    :actions="isGov?[{label:'下发整改', onClick:create}]:[]"
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
const cols=[{prop:'title',label:'标题'},{prop:'status',label:'状态',width:100},{prop:'reply',label:'回复'},{prop:'content',label:'要求'}]
async function load(){ list.value=(await http.get('/effluent/rectifications')).data||[] }
async function create(){ const {value}=await ElMessageBox.prompt('整改标题'); await http.post('/effluent/rectifications',{title:value,enterpriseId:1,content:value}); load() }
function rowActions(row){
  if(isEnt.value && row.status==='PENDING') return [{label:'回复', onClick: async()=>{ const {value}=await ElMessageBox.prompt('整改说明'); await http.post(`/effluent/rectifications/${row.id}/reply`,{feedback:value}); load() }}]
  return []
}
onMounted(load)
</script>
