<template>
  <SimpleTablePage title="市场行情" :rows="list" :columns="cols" />
</template>
<script setup>
import { onMounted, ref } from 'vue'
import http from '@/api/http'
import SimpleTablePage from '@/components/SimpleTablePage.vue'
const list = ref([])
const cols = [
  { prop: 'species', label: '品种', width: 100 },
  { prop: 'spec', label: '规格', width: 100 },
  { prop: 'price', label: '价格', width: 90 },
  { prop: 'unit', label: '单位', width: 90 },
  { prop: 'priceDate', label: '日期', width: 120 },
  { prop: 'marketId', label: '市场', width: 80 },
]
onMounted(async () => {
  list.value = (await http.get('/supply/prices')).data || []
})
</script>
