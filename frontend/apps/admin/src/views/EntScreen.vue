<template>
  <div class="screen">
    <header class="screen-header">
      <h1>{{ data.enterprise?.name || '企业大屏' }} · 运营总览</h1>
      <div class="header-actions">
        <button type="button" class="ghost" @click="toggleFs">全屏</button>
        <button type="button" class="ghost" @click="$router.push('/ent/workbench')">返回后台</button>
      </div>
    </header>
    <div class="screen-body">
      <aside class="col">
        <section class="panel">
          <div class="panel-title">主体简介</div>
          <p class="intro">{{ data.enterprise?.intro || '绿色循环渔业示范主体' }}</p>
          <p class="meta">品种：{{ data.enterprise?.species || '-' }}</p>
        </section>
        <section class="panel grow">
          <div class="panel-title">投喂/出塘</div>
          <div ref="feedChartEl" class="ent-chart" />
          <table class="data-table" style="margin-top:8px">
            <thead><tr><th>批次</th><th>品种</th><th>状态</th><th>FCR</th></tr></thead>
            <tbody>
              <tr v-for="b in (data.batches || [])" :key="b.batchNo">
                <td>{{ b.batchNo }}</td><td>{{ b.species }}</td><td>{{ b.status }}</td><td>{{ b.fcr ?? '-' }}</td>
              </tr>
              <tr v-if="!(data.batches || []).length"><td colspan="4" class="empty">暂无数据</td></tr>
            </tbody>
          </table>
        </section>
      </aside>
      <main class="col center">
        <div class="kpi-row">
          <div class="kpi"><div class="n">{{ data.enterprise?.areaMu ?? '-' }}</div><div class="l">面积(亩)</div></div>
          <div class="kpi"><div class="n">{{ data.deviceCount ?? '-' }}</div><div class="l">设备数</div></div>
          <div class="kpi"><div class="n">{{ data.traceCodeCount ?? '-' }}</div><div class="l">追溯码</div></div>
          <div class="kpi"><div class="n">{{ data.openRectifications ?? '-' }}</div><div class="l">未关闭整改</div></div>
        </div>
        <div class="map-stage">
          <div ref="mapEl" class="ent-map" />
          <div class="map-foot">{{ data.enterprise?.name || '企业一张图' }}</div>
        </div>
      </main>
      <aside class="col">
        <section class="panel">
          <div class="panel-title row">
            <span>视频监控</span>
            <select v-model="camId" class="site-select">
              <option v-for="c in cameras" :key="c.id" :value="c.id">{{ c.name }}</option>
            </select>
          </div>
          <div class="video-box">
            <VideoPlayer
              v-if="camId"
              :camera-id="camId"
              :title="cameras.find((c) => c.id === camId)?.name || ''"
              compact
              :show-toolbar="false"
            />
            <div v-else class="video-empty">暂无已分配摄像头</div>
          </div>
        </section>
        <section class="panel grow">
          <div class="panel-title">环境监测</div>
          <div ref="waterChartEl" class="ent-chart" />
        </section>
      </aside>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, onUnmounted, ref } from 'vue'
import * as echarts from 'echarts'
import Map from 'ol/Map'
import View from 'ol/View'
import VectorLayer from 'ol/layer/Vector'
import VectorSource from 'ol/source/Vector'
import { fromLonLat } from 'ol/proj'
import GeoJSON from 'ol/format/GeoJSON'
import Feature from 'ol/Feature'
import { Fill, Stroke, Style, Circle as CircleStyle } from 'ol/style'
import 'ol/ol.css'
import http from '@/api/http'
import { makeBasemapLayer } from '@/utils/basemap'
import VideoPlayer from '@/components/VideoPlayer.vue'
import { DEMO_MAP_CENTER } from '@/config/demoMap'

const data = ref({})
const camId = ref(0)
const mapEl = ref(null)
const feedChartEl = ref(null)
const waterChartEl = ref(null)
let map
let vectorSource
let feedChart
let waterChart

const cameras = computed(() => (data.value.cameras || []).filter((c) => c.id > 0))

function initMap() {
  if (!mapEl.value || map) return
  vectorSource = new VectorSource()
  map = new Map({
    target: mapEl.value,
    layers: [
      makeBasemapLayer('td-vec'),
      new VectorLayer({
        source: vectorSource,
        style: (f) => {
          const t = f.get('layerType')
          if (t === 'OUTLET') {
            return new Style({
              image: new CircleStyle({
                radius: 6,
                fill: new Fill({ color: '#f59e0b' }),
                stroke: new Stroke({ color: '#fff', width: 2 }),
              }),
            })
          }
          return new Style({
            fill: new Fill({ color: t === 'EFFLUENT' ? 'rgba(56,189,248,.35)' : 'rgba(52,211,153,.4)' }),
            stroke: new Stroke({ color: t === 'EFFLUENT' ? '#38bdf8' : '#34d399', width: 2 }),
          })
        },
      }),
    ],
    view: new View({ center: fromLonLat([DEMO_MAP_CENTER.lng, DEMO_MAP_CENTER.lat]), zoom: 14 }),
    controls: [],
  })
}

async function loadLayers() {
  const res = await http.get('/party/gis/layers', { params: { mode: 'collect' } })
  const ponds = res.data?.ponds || []
  const fmt = new GeoJSON()
  vectorSource.clear()
  for (const p of ponds) {
    if (!p.geomGeojson) continue
    try {
      const obj = typeof p.geomGeojson === 'string' ? JSON.parse(p.geomGeojson) : p.geomGeojson
      const geom = fmt.readGeometry(obj, { dataProjection: 'EPSG:4326', featureProjection: 'EPSG:3857' })
      const f = new Feature({ geometry: geom })
      f.set('layerType', p.layerType)
      vectorSource.addFeature(f)
    } catch {
      /* skip */
    }
  }
  if (vectorSource.getFeatures().length) {
    map.getView().fit(vectorSource.getExtent(), { padding: [40, 40, 40, 40], maxZoom: 16 })
  }
}

function renderCharts() {
  const feed = data.value.charts?.feedTrend
  const water = data.value.charts?.waterLatest
  if (feedChartEl.value) {
    feedChart = feedChart || echarts.init(feedChartEl.value)
    feedChart.setOption({
      backgroundColor: 'transparent',
      color: ['#5dffd2', '#3db6ff'],
      tooltip: { trigger: 'axis' },
      legend: { data: ['投喂', '出塘'], textStyle: { color: '#9fd4ff', fontSize: 10 } },
      grid: { left: 36, right: 12, top: 28, bottom: 24 },
      xAxis: { type: 'category', data: feed?.months || [], axisLabel: { color: '#8eb4d8', fontSize: 10 } },
      yAxis: { type: 'value', splitLine: { lineStyle: { color: 'rgba(70,130,190,.2)' } }, axisLabel: { color: '#8eb4d8', fontSize: 10 } },
      series: [
        { name: '投喂', type: 'bar', data: feed?.feed || [] },
        { name: '出塘', type: 'line', data: feed?.harvest || [] },
      ],
    })
  }
  if (waterChartEl.value) {
    waterChart = waterChart || echarts.init(waterChartEl.value)
    waterChart.setOption({
      backgroundColor: 'transparent',
      color: ['#5dffd2'],
      tooltip: {},
      xAxis: { type: 'category', data: (water || []).map((x) => x.name), axisLabel: { color: '#8eb4d8', fontSize: 10 } },
      yAxis: { type: 'value', splitLine: { lineStyle: { color: 'rgba(70,130,190,.2)' } }, axisLabel: { color: '#8eb4d8', fontSize: 10 } },
      series: [{ type: 'bar', data: (water || []).map((x) => x.value), barWidth: 28 }],
      grid: { left: 36, right: 12, top: 20, bottom: 28 },
    })
  }
}

onMounted(async () => {
  const res = await http.get('/analytics/enterprise-screen')
  data.value = res.data || {}
  if (cameras.value.length) camId.value = cameras.value[0].id
  await nextTick()
  initMap()
  await loadLayers()
  map?.updateSize()
  renderCharts()
})

onUnmounted(() => {
  if (map) {
    map.setTarget(null)
    map = null
  }
  feedChart?.dispose()
  waterChart?.dispose()
})

function toggleFs() {
  if (!document.fullscreenElement) document.documentElement.requestFullscreen?.()
  else document.exitFullscreen?.()
  nextTick(() => {
    map?.updateSize()
    feedChart?.resize()
    waterChart?.resize()
  })
}
</script>

<style scoped>
.screen {
  min-height: 100vh;
  background: linear-gradient(180deg, #061428 0%, #0a1f3d 45%, #071526 100%);
  color: #d7e9ff;
  font-family: "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
}
.screen-header {
  height: 64px; display: grid; place-items: center; position: relative;
  background: linear-gradient(180deg, rgba(18,70,130,.55), transparent);
}
.screen-header h1 { margin: 0; font-size: 24px; letter-spacing: 2px; }
.header-actions { position: absolute; right: 16px; top: 16px; display: flex; gap: 8px; }
.ghost {
  border: 1px solid rgba(90,180,255,.45); background: rgba(10,40,80,.45);
  color: #9fd4ff; border-radius: 4px; padding: 4px 10px; cursor: pointer;
}
.screen-body {
  display: grid; grid-template-columns: 300px 1fr 300px; gap: 12px;
  padding: 8px 16px 16px; height: calc(100vh - 64px); box-sizing: border-box;
}
.col { display: flex; flex-direction: column; gap: 12px; min-height: 0; }
.panel {
  background: linear-gradient(180deg, rgba(18,52,96,.55), rgba(8,28,58,.72));
  border: 1px solid rgba(64,160,255,.35); padding: 10px 12px; flex-shrink: 0;
}
.panel.grow { flex: 1; overflow: auto; }
.panel-title { color: #7ec8ff; margin-bottom: 8px; border-left: 3px solid #2ea7ff; padding-left: 8px; }
.panel-title.row { display: flex; align-items: center; justify-content: space-between; gap: 8px; }
.site-select {
  background: rgba(8,28,58,.8); border: 1px solid rgba(64,160,255,.4);
  color: #9fd4ff; border-radius: 3px; font-size: 12px; padding: 2px 6px; max-width: 140px;
}
.intro, .meta { font-size: 13px; color: #a9c7e6; line-height: 1.5; }
.kpi-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-bottom: 12px; }
.kpi { text-align: center; padding: 10px; background: rgba(8,30,60,.55); border: 1px solid rgba(60,140,220,.25); }
.kpi .n { font-size: 22px; color: #5dffd2; font-weight: 700; }
.kpi .l { font-size: 12px; color: #8eb4d8; }
.map-stage { position: relative; flex: 1; border: 1px solid rgba(64,160,255,.35); min-height: 280px; overflow: hidden; }
.ent-map { position: absolute; inset: 0; }
.map-foot {
  position: absolute; left: 0; right: 0; bottom: 12px; text-align: center; color: #9fd4ff;
  z-index: 2; pointer-events: none; text-shadow: 0 0 8px rgba(0,0,0,.6);
}
.video-box { min-height: 140px; }
.video-empty { height: 140px; display: grid; place-items: center; color: #6f8eae; background: #03101f; }
.ent-chart { height: 160px; width: 100%; }
.data-table { width: 100%; border-collapse: collapse; font-size: 12px; }
.data-table th, .data-table td { padding: 8px 6px; border-bottom: 1px solid rgba(70,130,190,.25); }
.data-table th { color: #7eb8ea; }
.empty { text-align: center; color: #6f8eae; }
@media (max-width: 1100px) { .screen-body { grid-template-columns: 1fr; height: auto; } }
</style>
