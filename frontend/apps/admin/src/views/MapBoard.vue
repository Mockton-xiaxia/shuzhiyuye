<template>
  <div class="page-card">
    <h2 class="page-title">一张图运营台</h2>
    <el-row :gutter="16">
      <el-col :span="10">
        <h4>主体</h4>
        <el-table :data="layers.enterprises || []" size="small" height="240">
          <el-table-column prop="name" label="名称" />
          <el-table-column prop="lng" label="经度" width="90" />
          <el-table-column prop="lat" label="纬度" width="90" />
        </el-table>
        <h4 style="margin-top:12px">开放告警</h4>
        <el-table :data="layers.alarms || []" size="small" height="180">
          <el-table-column prop="title" label="告警" />
          <el-table-column label="视频" width="90">
            <template #default="{ row }">
              <el-button v-if="row.cameraId" link type="primary" @click="play(row.cameraId)">打开</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-col>
      <el-col :span="14">
        <h4>塘口图层</h4>
        <el-table :data="layers.ponds || []" size="small" height="460">
          <el-table-column prop="name" label="塘口" />
          <el-table-column prop="layerType" label="图层" width="120" />
          <el-table-column prop="auditStatus" label="审核" width="100" />
          <el-table-column prop="lng" label="经度" width="90" />
          <el-table-column prop="lat" label="纬度" width="90" />
        </el-table>
      </el-col>
    </el-row>
    <el-dialog v-model="showPlay" title="视频取流" width="480px">
      <pre style="white-space:pre-wrap">{{ playInfo }}</pre>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import http from '@/api/http'

const layers = ref({})
const showPlay = ref(false)
const playInfo = ref('')
onMounted(async () => {
  const res = await http.get('/map/layers')
  layers.value = res.data || {}
})
async function play(id) {
  const res = await http.get(`/iot/cameras/${id}/play-url`)
  playInfo.value = JSON.stringify(res.data, null, 2)
  showPlay.value = true
}
</script>
