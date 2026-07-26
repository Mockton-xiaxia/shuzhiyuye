<template>
  <div class="page-card">
    <h2 class="page-title">追溯统计</h2>
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
  {l:'申请总数',v:d.value.applyTotal??'-'},{l:'待审',v:d.value.pending??'-'},{l:'已分发',v:d.value.issued??'-'},{l:'码总量',v:d.value.codeTotal??'-'},{l:'已绑定',v:d.value.bound??'-'},
])
onMounted(async()=>{ d.value=(await http.get('/trace/stats')).data||{} })
</script>
