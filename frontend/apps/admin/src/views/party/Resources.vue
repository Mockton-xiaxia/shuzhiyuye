<template>
  <div class="page-card">
    <h2 class="page-title">资源统计</h2>
    <div class="stat-grid">
      <div class="stat-item" v-for="s in cards" :key="s.l"><div class="label">{{s.l}}</div><div class="value">{{s.v}}</div></div>
    </div>
  </div>
</template>
<script setup>
import { computed, onMounted, ref } from 'vue'
import http from '@/api/http'
const d=ref({})
const cards=computed(()=>[
  {l:'主体数',v:d.value.enterpriseCount??'-'},{l:'已审塘口',v:d.value.approvedPonds??'-'},{l:'待审塘口',v:d.value.pendingPonds??'-'},{l:'已审面积亩',v:d.value.approvedAreaMu??'-'},
])
onMounted(async()=>{ d.value=(await http.get('/analytics/resources')).data||{} })
</script>
