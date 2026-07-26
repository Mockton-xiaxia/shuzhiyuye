<template>
  <div class="vp" :class="{ compact }">
    <div v-if="showToolbar" class="vp-bar">
      <span class="name">{{ title || '监控画面' }}</span>
      <el-tag v-if="play?.demo" type="warning" size="small">演示流</el-tag>
      <el-tag v-else-if="play" type="success" size="small">已取流</el-tag>
      <el-button v-if="cameraId" link type="primary" size="small" @click="load">刷新</el-button>
    </div>
    <div class="vp-stage">
      <video
        v-if="play?.hlsUrl && useVideo"
        ref="videoEl"
        class="vid"
        controls
        autoplay
        muted
        playsinline
        :poster="play.poster"
      />
      <div v-else class="ph">
        <img v-if="play?.poster" :src="play.poster" alt="poster" />
        <div class="overlay">
          <p>{{ play?.message || emptyText }}</p>
          <p v-if="play?.playUrl" class="mono">{{ play.playUrl }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { nextTick, ref, watch } from 'vue'
import http from '@/api/http'

const props = defineProps({
  cameraId: { type: [Number, String], default: 0 },
  title: { type: String, default: '' },
  compact: { type: Boolean, default: false },
  showToolbar: { type: Boolean, default: true },
  emptyText: { type: String, default: '暂无视频流' },
})

const play = ref(null)
const videoEl = ref(null)
const useVideo = ref(true)
const emit = defineEmits(['loaded'])

async function load() {
  if (!props.cameraId) {
    play.value = null
    emit('loaded', null)
    return
  }
  try {
    const res = await http.get(`/iot/cameras/${props.cameraId}/play-url`)
    play.value = res.data || {}
  } catch {
    play.value = {
      demo: true,
      hlsUrl: 'https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8',
      poster: 'https://images.unsplash.com/photo-1544551763-46a013bb70d5?w=800&q=80',
      message: '演示流（取流失败回退）',
      playUrl: 'ezopen://open.ys7.com/DEMO/1.live',
      provider: 'EZVIZ',
      deviceSerial: 'DEMO',
      channelNo: 1,
    }
  }
  emit('loaded', play.value)
  useVideo.value = true
  await nextTick()
  const el = videoEl.value
  if (el && play.value?.hlsUrl) {
    el.src = play.value.hlsUrl
    el.play?.().catch(() => {
      useVideo.value = false
    })
  }
}

watch(() => props.cameraId, load, { immediate: true })

defineExpose({ load, play })
</script>

<style scoped>
.vp { display:flex; flex-direction:column; height:100%; min-height:140px; }
.vp-bar { display:flex; align-items:center; gap:8px; margin-bottom:6px; color:#9fd4ff; font-size:12px; }
.vp-bar .name { flex:1; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.vp-stage { flex:1; position:relative; background:#03101f; border-radius:4px; overflow:hidden; min-height:120px; }
.vid { width:100%; height:100%; object-fit:contain; background:#000; display:block; min-height:120px; }
.ph { position:absolute; inset:0; }
.ph img { width:100%; height:100%; object-fit:cover; opacity:.55; }
.overlay {
  position:absolute; inset:0; display:grid; place-content:center; text-align:center;
  color:#e8f4ff; padding:12px; gap:6px; font-size:12px;
}
.mono { font-family:ui-monospace,Consolas,monospace; word-break:break-all; opacity:.85; font-size:11px; }
.compact .vp-stage { min-height:140px; }
</style>
