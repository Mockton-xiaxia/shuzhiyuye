<template>
  <SimpleTablePage title="渔业信息审核" :rows="list" :columns="cols" :row-actions="rowActions"
    :actions="isEnt?[{label:'新建提报', onClick:create}]:[]" />
</template>
<script setup>
import { computed, onMounted, ref } from 'vue'
import { ElMessageBox } from 'element-plus'
import http from '@/api/http'
import { useAuthStore } from '@/stores/auth'
import SimpleTablePage from '@/components/SimpleTablePage.vue'
const auth=useAuthStore(); const isGov=computed(()=>auth.portal==='GOV'); const isEnt=computed(()=>auth.portal==='ENT')
const list=ref([])
const cols=[{prop:'title',label:'标题'},{prop:'status',label:'状态',width:110},{prop:'auditOpinion',label:'意见'},{prop:'enterpriseId',label:'主体',width:80}]
async function load(){ list.value=(await http.get('/party/info-submits')).data||[] }
async function create(){ const {value}=await ElMessageBox.prompt('提报标题'); const r=await http.post('/party/info-submits',{title:value,content:value}); await http.post(`/party/info-submits/${r.data.id}/submit`); load() }
function rowActions(row){
  const arr=[]
  if(isEnt.value && ['DRAFT','REJECTED'].includes(row.status)) arr.push({label:'提交', onClick: async()=>{ await http.post(`/party/info-submits/${row.id}/submit`); load() }})
  if(isGov.value && row.status==='PENDING'){
    arr.push({label:'通过', onClick: async()=>{ await http.post(`/party/info-submits/${row.id}/audit`,{approved:true}); load() }})
    arr.push({label:'驳回', onClick: async()=>{ await http.post(`/party/info-submits/${row.id}/audit`,{approved:false,opinion:'请补充'}); load() }})
  }
  return arr
}
onMounted(load)
</script>
