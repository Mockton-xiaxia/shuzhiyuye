<template>
  <SimpleTablePage title="分发流水" :rows="list" :columns="cols" />
</template>
<script setup>
import { onMounted, ref } from 'vue'
import http from '@/api/http'
import SimpleTablePage from '@/components/SimpleTablePage.vue'
const list=ref([])
const cols=[{prop:'applyId',label:'申请ID',width:90},{prop:'issueQty',label:'数量',width:80},{prop:'startCode',label:'起码'},{prop:'endCode',label:'止码'},{prop:'enterpriseId',label:'主体',width:80}]
onMounted(async()=>{ list.value=(await http.get('/trace/issues')).data||[] })
</script>
