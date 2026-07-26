<template>
  <SimpleTablePage title="自主监管" :rows="list" :columns="cols" :actions="isEnt?[{label:'新建自检', onClick:create}]:[]" />
</template>
<script setup>
import { computed, onMounted, ref } from 'vue'
import { ElMessageBox } from 'element-plus'
import http from '@/api/http'
import { useAuthStore } from '@/stores/auth'
import SimpleTablePage from '@/components/SimpleTablePage.vue'
const auth=useAuthStore(); const isEnt=computed(()=>auth.portal==='ENT')
const list=ref([])
const cols=[{prop:'title',label:'标题'},{prop:'result',label:'结果',width:120},{prop:'checkedAt',label:'时间',width:180}]
async function load(){ list.value=(await http.get('/quality/self-checks')).data||[] }
async function create(){ const {value}=await ElMessageBox.prompt('自检标题'); await http.post('/quality/self-checks',{title:value}); load() }
onMounted(load)
</script>
