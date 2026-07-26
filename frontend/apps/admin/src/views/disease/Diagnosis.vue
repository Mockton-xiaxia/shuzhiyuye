<template>
  <SimpleTablePage title="诊断链接" :rows="list" :columns="cols" />
</template>
<script setup>
import { onMounted, ref } from 'vue'
import http from '@/api/http'
import SimpleTablePage from '@/components/SimpleTablePage.vue'
const list = ref([])
const cols = [
  { prop: 'name', label: '名称' },
  { prop: 'url', label: '链接' },
  { prop: 'portal', label: '门户', width: 90 },
]
onMounted(async () => {
  list.value = (await http.get('/disease/diagnosis-links')).data || []
})
</script>
