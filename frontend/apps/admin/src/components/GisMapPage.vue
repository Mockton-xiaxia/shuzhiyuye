<template>
  <div class="gis-page" :class="{ fullscreen: isFs }">
    <aside class="left">
      <h3>{{ title }}</h3>
      <div class="summary" v-if="summary">
        <div><b>{{ summary.approvedCount ?? summary.drawnCount ?? 0 }}</b><span>已审要素</span></div>
        <div><b>{{ summary.pendingCount ?? 0 }}</b><span>待审核</span></div>
        <div><b>{{ summary.areaMu ?? 0 }}</b><span>面积(亩)</span></div>
        <div><b>{{ (summary.species || []).length }}</b><span>品种</span></div>
      </div>
      <el-input v-model="keyword" placeholder="塘口 / 主体名称" clearable @keyup.enter="reload" />
      <el-button type="primary" style="margin-top:8px;width:100%" @click="reload">查询</el-button>
      <el-table
        :data="filtered"
        size="small"
        height="360"
        highlight-current-row
        @current-change="onSelectRow"
        style="margin-top:12px"
      >
        <el-table-column prop="name" label="塘口" min-width="90" />
        <el-table-column prop="layerType" label="图层" width="72">
          <template #default="{ row }">{{ layerLabel(row.layerType) }}</template>
        </el-table-column>
        <el-table-column prop="auditStatus" label="状态" width="78">
          <template #default="{ row }">{{ auditLabel(row.auditStatus) }}</template>
        </el-table-column>
      </el-table>
      <div v-if="mode === 'audit'" class="batch">
        <el-button size="small" type="success" @click="batchAudit(true)">批量通过待审</el-button>
      </div>
    </aside>

    <main class="map">
      <div class="toolbar">
        <el-button-group>
          <el-button size="small" :type="tool==='pan'?'primary':'default'" @click="setTool('pan')">漫游</el-button>
          <el-button v-if="mode==='collect'" size="small" :type="tool==='aquaculture'?'primary':'default'" @click="setTool('aquaculture')">养殖区测绘</el-button>
          <el-button v-if="mode==='collect'" size="small" :type="tool==='effluent'?'primary':'default'" @click="setTool('effluent')">尾水区测绘</el-button>
          <el-button v-if="mode==='collect'" size="small" :type="tool==='outlet'?'primary':'default'" @click="setTool('outlet')">出水口打点</el-button>
          <el-button size="small" :type="tool==='measure'?'primary':'default'" @click="setTool('measure')">测距</el-button>
          <el-button v-if="mode==='stats'" size="small" :type="tool==='box'?'primary':'default'" @click="setTool('box')">自定义框画</el-button>
        </el-button-group>
        <el-button v-if="mode==='collect'" size="small" type="primary" plain @click="triggerGeoImport">导入 GeoJSON</el-button>
        <el-button v-if="mode==='collect'" size="small" link type="primary" @click="downloadGeoTemplate">下载 GeoJSON 模板</el-button>
        <input ref="geoImportRef" type="file" accept=".json,.geojson,application/geo+json" style="display:none" @change="onGeoImportFile" />
        <el-checkbox v-model="showAqua" @change="syncLayerVis">养殖区</el-checkbox>
        <el-checkbox v-model="showEffluent" @change="syncLayerVis">尾水区</el-checkbox>
        <el-checkbox v-model="showOutlet" @change="syncLayerVis">出水口</el-checkbox>
        <el-select v-model="basemap" size="small" style="width:120px" @change="switchBasemap">
          <el-option v-for="o in basemapOptions" :key="o.value" :label="o.label" :value="o.value" />
        </el-select>
        <el-button size="small" @click="fitAll">地图定位</el-button>
        <el-button size="small" @click="isFs=!isFs">{{ isFs ? '退出全屏' : '全屏' }}</el-button>
      </div>
      <div ref="mapEl" class="map-el" />
      <div class="coord">鼠标 {{ cursor.lng }} · {{ cursor.lat }}{{ measureTip ? ' · ' + measureTip : '' }}</div>
    </main>

    <aside class="right">
      <h3>详情</h3>
      <template v-if="selected">
        <p><b>名称：</b>{{ selected.name }}</p>
        <p><b>编号：</b>{{ selected.code || '-' }}</p>
        <p><b>主体：</b>{{ selected.enterpriseName || selected.enterpriseId || '-' }}</p>
        <p><b>面积：</b>{{ selected.areaMu ?? '-' }} 亩</p>
        <p><b>品种：</b>{{ selected.species || '-' }}</p>
        <p><b>乡镇：</b>{{ selected.township || '-' }}</p>
        <p><b>图层：</b>{{ layerLabel(selected.layerType) }}</p>
        <p><b>审核：</b>{{ auditLabel(selected.auditStatus) }}</p>
        <p><b>塘口坐标：</b>{{ selected.lng ?? '-' }}, {{ selected.lat ?? '-' }}</p>
        <div class="btns">
          <el-button size="small" type="primary" @click="flyTo(selected)">定位到面</el-button>
          <el-button size="small" @click="fitAll">查看全部</el-button>
          <el-button v-if="mode==='collect' && selected.id" size="small" type="primary" @click="submitPond">提交审核</el-button>
          <template v-if="mode==='audit' && ['PENDING','SUBMITTED','DRAFT'].includes(selected.auditStatus)">
            <el-button size="small" type="success" @click="audit(true)">通过</el-button>
            <el-button size="small" type="danger" @click="audit(false)">驳回</el-button>
          </template>
        </div>
        <div v-if="mode==='stats'" class="stats">
          <p>已审塘口：{{ summary.approvedCount ?? '-' }}</p>
          <p>待审塘口：{{ summary.pendingCount ?? '-' }}</p>
          <p>已画面积：{{ summary.areaMu ?? '-' }} 亩</p>
          <p>品种：{{ (summary.species || []).join('、') || '-' }}</p>
        </div>
      </template>
      <p v-else class="muted">点击塘口或地图要素查看</p>
      <p v-if="mode==='collect'" class="hint-text">双击结束多边形绘制；保存后自动进入待审核。支持「导入 GeoJSON」（FeatureCollection，properties 可含 name、layerType）。可先「下载 GeoJSON 模板」填写后导入。</p>
    </aside>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import axios from 'axios'
import Map from 'ol/Map'
import View from 'ol/View'
import VectorLayer from 'ol/layer/Vector'
import VectorSource from 'ol/source/Vector'
import { Draw, Modify, Select } from 'ol/interaction'
import { getLength, getArea } from 'ol/sphere'
import { fromLonLat, toLonLat } from 'ol/proj'
import GeoJSON from 'ol/format/GeoJSON'
import { Fill, Stroke, Style, Circle as CircleStyle, Text } from 'ol/style'
import Feature from 'ol/Feature'
import Point from 'ol/geom/Point'
import 'ol/ol.css'
import http from '@/api/http'
import { useAuthStore } from '@/stores/auth'
import { BASEMAP_OPTIONS } from '@/config/map'
import { makeBasemapLayer } from '@/utils/basemap'
import { statusLabel } from '@/utils/labels'
import { DEMO_MAP_CENTER } from '@/config/demoMap'

const props = defineProps({
  title: { type: String, default: '塘口 GIS' },
  mode: { type: String, default: 'collect' },
})

const auth = useAuthStore()

const mapEl = ref(null)
const geoImportRef = ref(null)
const keyword = ref('')
const ponds = ref([])
const selected = ref(null)
const summary = ref({})
const tool = ref('pan')
const isFs = ref(false)
const basemap = ref('td-vec')
const basemapOptions = BASEMAP_OPTIONS
const showAqua = ref(true)
const showEffluent = ref(true)
const showOutlet = ref(true)
const cursor = reactive({ lng: DEMO_MAP_CENTER.lng.toFixed(6), lat: DEMO_MAP_CENTER.lat.toFixed(6) })
const measureTip = ref('')
/** 列表刷新时避免 current-change 触发定位，把视野又缩回单点 */
let suppressFly = false

let map
let aquaSource
let effluentSource
let outletSource
let aquaLayer
let effluentLayer
let outletLayer
let draw
let measureDraw
let select
let baseLayer
const geojson = new GeoJSON()
const MU = 666.6667

const filtered = computed(() => {
  const k = keyword.value.trim()
  if (!k) return ponds.value
  return ponds.value.filter(
    (p) => String(p.name || '').includes(k) || String(p.enterpriseName || '').includes(k) || String(p.code || '').includes(k),
  )
})

function layerLabel(t) {
  return { AQUACULTURE: '养殖区', EFFLUENT: '尾水区', OUTLET: '出水口' }[t] || t || '-'
}

function auditLabel(s) {
  return statusLabel(s) || s || '-'
}

function triggerGeoImport() {
  geoImportRef.value?.click()
}

async function downloadGeoTemplate() {
  const token = auth.token
  const res = await axios.get('/api/v1/party/ponds/geojson-template', {
    responseType: 'blob',
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  })
  const url = URL.createObjectURL(res.data)
  const a = document.createElement('a')
  a.href = url
  a.download = 'pond_import_template.geojson'
  a.click()
  URL.revokeObjectURL(url)
}

async function onGeoImportFile(e) {
  const file = e.target.files?.[0]
  e.target.value = ''
  if (!file) return
  try {
    const text = await file.text()
    const res = await http.post('/party/ponds/import-geojson', { geojson: text })
    const n = res.data?.count ?? 0
    const skipped = res.data?.skipped ?? 0
    ElMessage.success(`导入完成：成功 ${n} 条${skipped ? `，跳过 ${skipped} 条` : ''}`)
    await reload()
    fitAll()
  } catch {
    /* interceptor */
  }
}

function styleFor(type, active, name = '') {
  const label = new Text({
    text: name || '',
    font: '12px Microsoft YaHei, sans-serif',
    fill: new Fill({ color: '#0f172a' }),
    stroke: new Stroke({ color: 'rgba(255,255,255,0.92)', width: 3 }),
    offsetY: type === 'OUTLET' ? -14 : 0,
    overflow: true,
  })
  if (type === 'OUTLET') {
    return new Style({
      image: new CircleStyle({
        radius: active ? 9 : 7,
        fill: new Fill({ color: active ? '#ff6b35' : '#f59e0b' }),
        stroke: new Stroke({ color: '#fff', width: 2 }),
      }),
      text: label,
      zIndex: active ? 20 : 10,
    })
  }
  const fill =
    type === 'EFFLUENT'
      ? `rgba(14,165,233,${active ? 0.55 : 0.38})`
      : `rgba(22,163,74,${active ? 0.55 : 0.4})`
  const stroke = type === 'EFFLUENT' ? '#0284c7' : '#15803d'
  return new Style({
    fill: new Fill({ color: fill }),
    stroke: new Stroke({ color: active ? '#f8fafc' : stroke, width: active ? 3 : 2 }),
    text: label,
    zIndex: active ? 20 : 5,
  })
}

function makeBase(kind) {
  return makeBasemapLayer(kind)
}

function switchBasemap() {
  if (!map) return
  map.removeLayer(baseLayer)
  baseLayer = makeBase(basemap.value)
  map.getLayers().insertAt(0, baseLayer)
}

function syncLayerVis() {
  if (aquaLayer) aquaLayer.setVisible(showAqua.value)
  if (effluentLayer) effluentLayer.setVisible(showEffluent.value)
  if (outletLayer) outletLayer.setVisible(showOutlet.value)
}

function clearDraw() {
  if (draw) {
    map.removeInteraction(draw)
    draw = null
  }
  if (measureDraw) {
    map.removeInteraction(measureDraw)
    measureDraw = null
  }
  measureTip.value = ''
}

function setTool(t) {
  tool.value = t
  clearDraw()
  if (!map) return
  if (t === 'pan') return
  if (t === 'measure') {
    measureDraw = new Draw({ source: new VectorSource(), type: 'LineString' })
    measureDraw.on('drawend', (e) => {
      const len = getLength(e.feature.getGeometry())
      measureTip.value = len > 1000 ? `测距 ${(len / 1000).toFixed(2)} km` : `测距 ${len.toFixed(1)} m`
      ElMessage.info(measureTip.value)
    })
    map.addInteraction(measureDraw)
    return
  }
  if (t === 'box') {
    measureDraw = new Draw({ source: new VectorSource(), type: 'Polygon' })
    measureDraw.on('drawend', (e) => {
      const box = e.feature.getGeometry()
      const hit = []
      for (const p of ponds.value) {
        const f = featureFromPond(p)
        if (!f) continue
        const g = f.getGeometry()
        if (!g) continue
        const c = g.getType() === 'Point' ? g.getCoordinates() : g.getInteriorPoint().getCoordinates()
        if (box.intersectsCoordinate(c)) hit.push(p)
      }
      const area = hit.reduce((s, p) => s + Number(p.areaMu || 0), 0)
      ElMessage.success(`框选命中 ${hit.length} 个要素 · 面积合计 ${area.toFixed(2)} 亩`)
      if (hit.length) onSelectRow(hit[0])
      setTool('pan')
    })
    map.addInteraction(measureDraw)
    return
  }
  const layerType = t === 'effluent' ? 'EFFLUENT' : t === 'outlet' ? 'OUTLET' : 'AQUACULTURE'
  const geomType = t === 'outlet' ? 'Point' : 'Polygon'
  const src = layerType === 'EFFLUENT' ? effluentSource : layerType === 'OUTLET' ? outletSource : aquaSource
  draw = new Draw({ source: src, type: geomType })
  draw.on('drawend', async (e) => {
    const f = e.feature
    f.set('layerType', layerType)
    await persistNewFeature(f, layerType)
    setTool('pan')
  })
  map.addInteraction(draw)
}

async function persistNewFeature(feature, layerType) {
  const geom = feature.getGeometry()
  let areaMu = 0
  let lng
  let lat
  if (geom.getType() === 'Polygon') {
    areaMu = Math.round((getArea(geom) / MU) * 100) / 100
    const c = toLonLat(geom.getInteriorPoint().getCoordinates())
    lng = c[0]
    lat = c[1]
  } else {
    const c = toLonLat(geom.getCoordinates())
    lng = c[0]
    lat = c[1]
  }
  const gj = geojson.writeGeometryObject(geom, { dataProjection: 'EPSG:4326', featureProjection: 'EPSG:3857' })
  try {
    const { value: name } = await ElMessageBox.prompt(
      layerType === 'OUTLET' ? '出水口名称' : '养殖区/尾水区名称',
      '保存测绘',
      { inputValue: layerType === 'OUTLET' ? '出水口' : `新建${layerLabel(layerType)}` },
    )
    const res = await http.post('/party/ponds', {
      name,
      layerType,
      areaMu: layerType === 'OUTLET' ? 0 : areaMu,
      lng,
      lat,
      geomGeojson: JSON.stringify(gj),
      species: '大鲵',
      township: '示范镇',
      pondType: '池塘',
      enterpriseId: ponds.value[0]?.enterpriseId || 1,
    })
    ElMessage.success(`已保存 · ${areaMu ? areaMu + ' 亩' : '打点完成'}`)
    await reload()
    const row = ponds.value.find((p) => p.id === res.data?.id)
    if (row) onSelectRow(row)
  } catch (err) {
    if (err !== 'cancel') {
      /* interceptor */
    }
    srcRemove(feature)
  }
}

function srcRemove(feature) {
  ;[aquaSource, effluentSource, outletSource].forEach((s) => s.removeFeature(feature))
}

function featureFromPond(p) {
  const fid = p.id
  const attach = (geom) => {
    const f = new Feature({ geometry: geom })
    f.setId(fid)
    f.setProperties({ ...p })
    return f
  }
  const pointFallback = () => {
    if (p.lng == null || p.lat == null) return null
    return attach(new Point(fromLonLat([Number(p.lng), Number(p.lat)])))
  }
  if (!p.geomGeojson) return pointFallback()
  try {
    let obj = typeof p.geomGeojson === 'string' ? JSON.parse(p.geomGeojson) : p.geomGeojson
    if (!obj) return pointFallback()
    // 兼容 Feature / FeatureCollection / Geometry
    if (obj.type === 'Feature') obj = obj.geometry
    if (obj.type === 'FeatureCollection') {
      const g0 = obj.features?.[0]?.geometry
      if (!g0) return pointFallback()
      obj = g0
    }
    const geom = geojson.readGeometry(obj, {
      dataProjection: 'EPSG:4326',
      featureProjection: 'EPSG:3857',
    })
    return attach(geom)
  } catch (e) {
    console.warn('[gis] geom parse failed', p.code || p.id, e)
    return pointFallback()
  }
}

function findFeatureByPondId(id) {
  if (id == null) return null
  const keys = [id, String(id), Number(id)]
  for (const src of [aquaSource, effluentSource, outletSource]) {
    if (!src) continue
    for (const k of keys) {
      const f = src.getFeatureById(k)
      if (f) return f
    }
  }
  return null
}

function refreshVectors() {
  aquaSource.clear()
  effluentSource.clear()
  outletSource.clear()
  for (const p of ponds.value) {
    const f = featureFromPond(p)
    if (!f) continue
    const t = p.layerType || 'AQUACULTURE'
    f.setStyle(styleFor(t, selected.value?.id === p.id, p.name || p.code || ''))
    if (t === 'EFFLUENT') effluentSource.addFeature(f)
    else if (t === 'OUTLET') outletSource.addFeature(f)
    else aquaSource.addFeature(f)
  }
  syncLayerVis()
}

function flyTo(row) {
  if (!map || !row) return
  const f = findFeatureByPondId(row.id)
  if (f?.getGeometry()) {
    map.getView().fit(f.getGeometry().getExtent(), {
      padding: [80, 80, 80, 80],
      maxZoom: 17,
      duration: 450,
    })
    return
  }
  if (row.lng != null && row.lat != null) {
    map.getView().animate({
      center: fromLonLat([Number(row.lng), Number(row.lat)]),
      zoom: 16,
      duration: 450,
    })
  }
}

function fitAll() {
  if (!map) return
  const feats = [
    ...aquaSource.getFeatures(),
    ...effluentSource.getFeatures(),
    ...outletSource.getFeatures(),
  ]
  if (!feats.length) {
    map.getView().animate({ center: fromLonLat([DEMO_MAP_CENTER.lng, DEMO_MAP_CENTER.lat]), zoom: 13 })
    return
  }
  let extent = feats[0].getGeometry().getExtent().slice()
  feats.slice(1).forEach((f) => {
    const e = f.getGeometry().getExtent()
    extent[0] = Math.min(extent[0], e[0])
    extent[1] = Math.min(extent[1], e[1])
    extent[2] = Math.max(extent[2], e[2])
    extent[3] = Math.max(extent[3], e[3])
  })
  // 单点/极小面时给一点缓冲，避免「缩到看不见」
  const w = extent[2] - extent[0]
  const h = extent[3] - extent[1]
  if (w < 80 || h < 80) {
    const pad = 120
    extent = [extent[0] - pad, extent[1] - pad, extent[2] + pad, extent[3] + pad]
  }
  map.getView().fit(extent, { padding: [48, 48, 48, 48], maxZoom: 16, duration: 450 })
}

function onSelectRow(row) {
  if (!row) {
    selected.value = null
    refreshVectors()
    return
  }
  selected.value = row
  refreshVectors()
  if (!suppressFly) flyTo(row)
}

async function reload() {
  suppressFly = true
  try {
    const res = await http.get('/party/gis/layers', { params: { mode: props.mode } })
    const data = res.data || {}
    ponds.value = data.ponds || []
    summary.value = data.summary || {}
    if (!selected.value && ponds.value.length) selected.value = ponds.value[0]
    else if (selected.value) {
      selected.value = ponds.value.find((p) => p.id === selected.value.id) || ponds.value[0] || null
    }
    refreshVectors()
    await nextTick()
    map?.updateSize()
    fitAll()
  } finally {
    // 等表格 current-change 冒泡完再放开
    await nextTick()
    suppressFly = false
  }
}

async function audit(ok) {
  if (!selected.value?.id) return
  await http.post(`/party/ponds/${selected.value.id}/audit`, { approved: ok, opinion: ok ? '通过' : '驳回' })
  ElMessage.success(ok ? '已通过' : '已驳回')
  reload()
}

async function batchAudit(ok) {
  const ids = ponds.value.filter((p) => ['PENDING', 'SUBMITTED', 'DRAFT'].includes(p.auditStatus)).map((p) => p.id)
  if (!ids.length) {
    ElMessage.info('无待审塘口')
    return
  }
  await http.post('/party/ponds/batch-audit', { ids, approved: ok })
  ElMessage.success(`已处理 ${ids.length} 条`)
  reload()
}

async function submitPond() {
  if (!selected.value?.id) return
  await http.post(`/party/ponds/${selected.value.id}/submit`)
  ElMessage.success('已提交审核')
  reload()
}

function initMap() {
  aquaSource = new VectorSource()
  effluentSource = new VectorSource()
  outletSource = new VectorSource()
  aquaLayer = new VectorLayer({ source: aquaSource })
  effluentLayer = new VectorLayer({ source: effluentSource })
  outletLayer = new VectorLayer({ source: outletSource })
  baseLayer = makeBase(basemap.value)
  map = new Map({
    target: mapEl.value,
    layers: [baseLayer, aquaLayer, effluentLayer, outletLayer],
    view: new View({ center: fromLonLat([DEMO_MAP_CENTER.lng, DEMO_MAP_CENTER.lat]), zoom: 13 }),
  })
  select = new Select({ layers: [aquaLayer, effluentLayer, outletLayer] })
  select.on('select', (e) => {
    const f = e.selected[0]
    if (!f) return
    const id = f.getId()
    const row = ponds.value.find((p) => p.id === id || String(p.id) === String(id))
    if (row) onSelectRow(row)
  })
  map.addInteraction(select)
  map.addInteraction(new Modify({ source: aquaSource }))
  map.on('pointermove', (evt) => {
    const [lng, lat] = toLonLat(evt.coordinate)
    cursor.lng = lng.toFixed(6)
    cursor.lat = lat.toFixed(6)
  })
  // 容器刚挂载时给一次尺寸校准，避免首屏空白/错位
  requestAnimationFrame(() => map?.updateSize())
}

onMounted(async () => {
  initMap()
  await reload()
})

onBeforeUnmount(() => {
  clearDraw()
  if (map) {
    map.setTarget(null)
    map = null
  }
})

watch(isFs, () => {
  nextTick(() => map?.updateSize())
})
</script>

<style scoped>
.gis-page {
  display: grid;
  grid-template-columns: 280px 1fr 260px;
  gap: 12px;
  height: calc(100vh - 120px);
}
.gis-page.fullscreen {
  position: fixed;
  inset: 0;
  z-index: 2000;
  height: 100vh;
  padding: 12px;
  background: #0b1c18;
  grid-template-columns: 300px 1fr 280px;
}
.left, .right {
  background: #fff;
  border: 1px solid #e6eeea;
  border-radius: 8px;
  padding: 12px;
  overflow: auto;
}
.summary {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  margin-bottom: 10px;
}
.summary div {
  background: #f3faf6;
  border-radius: 6px;
  padding: 8px;
  text-align: center;
}
.summary b { display: block; font-size: 18px; color: #0b6e4f; }
.summary span { font-size: 12px; color: #678; }
.map {
  border: 1px solid #e6eeea;
  border-radius: 8px;
  overflow: hidden;
  background: #dce8e2;
  display: flex;
  flex-direction: column;
  position: relative;
}
.toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
  padding: 8px;
  background: rgba(255,255,255,.92);
  border-bottom: 1px solid #e6eeea;
  z-index: 2;
}
.map-el { flex: 1; min-height: 360px; }
.coord {
  position: absolute;
  left: 10px;
  bottom: 10px;
  z-index: 2;
  background: rgba(8,30,24,.75);
  color: #dff7ec;
  font-size: 12px;
  padding: 4px 10px;
  border-radius: 4px;
}
.muted { color: #888; }
.btns { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 12px; }
.stats p, .right p { margin: 6px 0; font-size: 13px; }
.hint-text { margin-top: 16px; color: #888; font-size: 12px; line-height: 1.5; }
.batch { margin-top: 10px; }
@media (max-width: 1100px) {
  .gis-page { grid-template-columns: 1fr; height: auto; }
  .map { min-height: 420px; }
}
</style>
