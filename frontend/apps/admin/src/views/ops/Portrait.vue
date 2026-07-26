<template>
  <div class="page-card">
    <div class="bar">
      <h2 class="page-title">客户画像</h2>
      <el-button @click="load">刷新</el-button>
    </div>
    <div class="grid">
      <aside class="left">
        <el-table :data="list" highlight-current-row size="small" height="520" @current-change="cur=$event">
          <el-table-column prop="customerName" label="客户" />
          <el-table-column prop="level" label="等级" width="70" />
          <el-table-column prop="totalAmount" label="累计金额" width="100" />
        </el-table>
      </aside>
      <main v-if="cur" class="main">
        <div class="hero">
          <div>
            <h3>{{ cur.customerName }}</h3>
            <p>{{ cur.phone }} · {{ cur.address }}</p>
            <div class="tags">
              <el-tag v-for="t in cur.tags || []" :key="t" size="small">{{ t }}</el-tag>
            </div>
          </div>
          <div class="kpis">
            <div><b>{{ cur.totalOrders }}</b><span>订单数</span></div>
            <div><b>{{ cur.totalAmount }}</b><span>成交额</span></div>
            <div><b>{{ cur.paidAmount }}</b><span>已回款</span></div>
            <div><b>{{ cur.unpaidAmount }}</b><span>待回款</span></div>
          </div>
        </div>
        <h4>往来时间线</h4>
        <el-timeline>
          <el-timeline-item v-for="(ev, i) in cur.timeline || []" :key="i" :timestamp="ev.date">
            {{ ev.event }} <span v-if="ev.amount">· ¥{{ ev.amount }}</span>
          </el-timeline-item>
        </el-timeline>
      </main>
      <p v-else class="muted">选择客户查看画像</p>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import http from '@/api/http'

const list = ref([])
const cur = ref(null)

async function load() {
  const res = await http.get('/ledger/portrait')
  list.value = res.data || []
  cur.value = list.value[0] || null
}

onMounted(load)
</script>

<style scoped>
.bar { display:flex; justify-content:space-between; margin-bottom:12px; }
.grid { display:grid; grid-template-columns:280px 1fr; gap:16px; min-height:520px; }
.left { border:1px solid #e6eeea; border-radius:8px; padding:8px; }
.hero { display:flex; justify-content:space-between; gap:16px; flex-wrap:wrap; margin-bottom:16px; padding:16px; background:linear-gradient(135deg,#e8f7f1,#f7fbf9); border-radius:10px; }
.hero h3 { margin:0 0 6px; }
.hero p { margin:0; color:#567; }
.tags { margin-top:8px; display:flex; gap:6px; }
.kpis { display:grid; grid-template-columns:repeat(4, minmax(70px,1fr)); gap:10px; }
.kpis div { text-align:center; background:#fff; border-radius:8px; padding:10px 8px; }
.kpis b { display:block; font-size:18px; color:#0b6e4f; }
.kpis span { font-size:12px; color:#678; }
.muted { color:#888; }
@media (max-width:900px){ .grid { grid-template-columns:1fr; } }
</style>
