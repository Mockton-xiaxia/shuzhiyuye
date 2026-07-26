<template>
  <div class="wrap">
    <div class="card">
      <h1>水产品追溯</h1>
      <p class="code">码：{{ code }}</p>
      <template v-if="data">
        <h3>{{ data.enterprise?.name }}</h3>
        <p>{{ data.enterprise?.intro }}</p>
        <el-descriptions :column="2" border>
          <el-descriptions-item label="批次">{{ data.batch?.batchNo }}</el-descriptions-item>
          <el-descriptions-item label="品种">{{ data.batch?.species }}</el-descriptions-item>
          <el-descriptions-item label="投苗">{{ data.batch?.stockDate }}</el-descriptions-item>
          <el-descriptions-item label="状态">{{ data.batch?.status }}</el-descriptions-item>
        </el-descriptions>
        <h4 style="margin-top:16px">全链时间轴</h4>
        <el-timeline>
          <el-timeline-item v-for="(t,i) in data.timeline || []" :key="i" :timestamp="t.at">
            [{{ t.type }}] {{ t.title }} <span v-if="t.qty">· {{ t.qty }}{{ t.unit }}</span>
          </el-timeline-item>
        </el-timeline>
      </template>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import axios from 'axios'

const route = useRoute()
const code = route.params.code
const data = ref(null)
onMounted(async () => {
  const res = await axios.get(`/api/v1/public/trace/${code}`)
  data.value = res.data?.data
})
</script>

<style scoped>
.wrap { min-height:100%; padding:24px; background:linear-gradient(160deg,#e8f6f1,#fff); }
.card { max-width:720px; margin:0 auto; background:#fff; border-radius:14px; padding:20px; box-shadow:0 12px 30px rgba(0,0,0,.06); }
.code { color:#678; }
</style>
