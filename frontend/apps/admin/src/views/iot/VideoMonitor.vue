<template>
  <div class="video-page">
    <aside class="list">
      <h2 class="page-title">视频监控</h2>
      <el-input v-model="kw" placeholder="摄像头名称" clearable @keyup.enter="load" />
      <el-table :data="filtered" size="small" highlight-current-row height="520" style="margin-top:10px" @current-change="onSelect">
        <el-table-column prop="name" label="名称" />
        <el-table-column prop="status" label="状态" width="80" />
        <el-table-column prop="scene" label="场景" width="90" />
      </el-table>
    </aside>
    <main class="player">
      <VideoPlayer
        :camera-id="current?.id || 0"
        :title="current?.name || '请选择摄像头'"
        empty-text="请选择摄像头"
        @loaded="onPlayLoaded"
      />
      <div class="meta" v-if="playMeta">
        <span>厂商 {{ playMeta.provider }}</span>
        <span>序列号 {{ playMeta.deviceSerial }}</span>
        <span>通道 {{ playMeta.channelNo }}</span>
      </div>
      <p class="hint">形态对齐萤石 EZUIKit：正式环境配置 AppKey 后走 ezopen 协议</p>
    </main>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import http from '@/api/http'
import VideoPlayer from '@/components/VideoPlayer.vue'

const props = defineProps({
  scene: { type: String, default: '' },
})

const list = ref([])
const kw = ref('')
const current = ref(null)
const playMeta = ref(null)

const filtered = computed(() => {
  const k = kw.value.trim()
  return list.value.filter((c) => !k || String(c.name || '').includes(k))
})

async function load() {
  const params = {}
  if (props.scene === 'WAREHOUSE') params.bindStorage = true
  const res = await http.get('/iot/cameras', { params })
  list.value = res.data || []
  if (!list.value.length) {
    list.value = [{ id: 1, name: '塘口监控-1', status: 'ONLINE', scene: 'POND', provider: 'EZVIZ' }]
  }
  onSelect(list.value[0])
}

function onSelect(row) {
  if (!row) return
  current.value = row
  playMeta.value = null
}

function onPlayLoaded(p) {
  playMeta.value = p
}

onMounted(load)
</script>

<style scoped>
.video-page { display:grid; grid-template-columns:280px 1fr; gap:12px; height:calc(100vh - 120px); }
.list, .player { background:#fff; border:1px solid #e6eeea; border-radius:8px; padding:12px; }
.player { display:flex; flex-direction:column; min-height:0; }
.player :deep(.vp) { flex:1; min-height:360px; }
.meta { display:flex; gap:16px; margin-top:10px; color:#567; font-size:12px; flex-wrap:wrap; }
.hint { font-size:12px; color:#8a9; margin-top:8px; }
@media (max-width: 900px) { .video-page { grid-template-columns:1fr; height:auto; } }
</style>
