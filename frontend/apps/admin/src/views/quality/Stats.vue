<template>
  <div class="page-card">
    <h2 class="page-title">质量监管统计</h2>
    <div class="stat-grid">
      <div class="stat-item" v-for="s in cards" :key="s.l"><div class="label">{{s.l}}</div><div class="value">{{s.v}}</div></div>
    </div>
  </div>
</template>
<script setup>
import { computed, onMounted, ref } from 'vue'
import http from '@/api/http'
const d = ref({})
const cards = computed(()=>[
  {l:'抽检总数', v:d.value.inspectionTotal??'-'},
  {l:'合格', v:d.value.qualified??'-'},
  {l:'不合格', v:d.value.unqualified??'-'},
  {l:'未关闭整改', v:d.value.openRectifications??'-'},
  {l:'合格率', v:d.value.passRate??'-'},
])
onMounted(async()=>{ d.value=(await http.get('/quality/stats')).data||{} })
</script>
