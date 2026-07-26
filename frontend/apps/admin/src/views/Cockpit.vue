<template>
  <div ref="screenRef" class="kjxx-screen">
    <!-- 现网 mapPage 同款整屏底图 -->
    <div class="screen-bg" />
    <div class="screen-vignette" />
    <div class="tech-grid" />

    <header class="page-header">
      <h1>{{ data.title || '区县渔业总体情况' }}</h1>
      <button type="button" class="btn-setting" title="设置" @click="goBack">
        <i class="gear" />
        <span>设置</span>
      </button>
    </header>

    <div class="page-body">
      <aside class="page-left">
        <section class="panel panel-rank">
          <div class="title-row">
            <i class="t-l" />
            <span>{{ drillLevel === 'town' ? `养殖品种面积排行 · ${activeTown}` : '养殖品种面积排行' }}</span>
            <i class="t-r" />
            <div class="group-btns">
              <button type="button" :class="{ on: rankUnit === 'ton' }" @click="rankUnit = 'ton'">吨</button>
              <button type="button" :class="{ on: rankUnit === 'tail' }" @click="rankUnit = 'tail'">尾</button>
            </div>
          </div>
          <div class="panel-frame">
            <div ref="rankEl" class="chart" />
          </div>
        </section>

        <section class="panel panel-seed">
          <div class="title-row">
            <i class="t-l" /><span>种苗数量</span><i class="t-r" />
          </div>
          <div class="panel-frame">
            <div ref="seedEl" class="chart" />
          </div>
        </section>

        <section class="panel panel-yield">
          <div class="title-row">
            <i class="t-l" /><span>水产品产量</span><i class="t-r" />
            <div class="group-btns dense">
              <button
                v-for="t in yieldTabs"
                :key="t.value"
                type="button"
                :class="{ on: yieldTab === t.value }"
                @click="yieldTab = t.value"
              >{{ t.label }}</button>
            </div>
          </div>
          <div class="panel-frame grow">
            <div class="scpcl-content">
              <div ref="yieldEl" class="scpcl-left" />
              <div class="scpcl-legend-list">
                <div v-for="(x, i) in yieldItems" :key="x.name" class="scpcl-legend-item">
                  <span class="legend-color" :style="{ background: DOT_COLORS[i % DOT_COLORS.length] }" />
                  <div class="legend-name">{{ x.name }}</div>
                  <div class="legend-value" :style="{ color: DOT_COLORS[i % DOT_COLORS.length] }">{{ x.pct }}%</div>
                </div>
              </div>
            </div>
          </div>
        </section>
      </aside>

      <main class="page-center">
        <div class="map-wrap">
          <div class="map-photo-bg" />
          <div class="map-glow" />
          <div ref="mapEl" class="map" />
          <!-- 标签/弹窗由 OpenLayers Overlay 挂到经纬度，随地图缩放平移 -->
          <div ref="pinHost" class="pin-host" aria-hidden="true" />
          <div class="content-top">
            <div v-for="k in kpis" :key="k.label" class="con-top-item">
              <div class="kpi-ico" :class="k.tone" :style="k.icon ? { backgroundImage: `url(${k.icon})` } : undefined" />
              <div class="rgt">
                <div class="lab">{{ k.label }}</div>
                <div class="con-top-num">{{ k.value }}</div>
              </div>
            </div>
          </div>

          <button
            v-if="drillLevel === 'town'"
            type="button"
            class="btn-back-district"
            title="返回区级"
            @click="exitDrill"
          >
            返回区级
          </button>
          <div class="map-vignette" />
        </div>
      </main>

      <aside class="page-right">
        <section class="panel panel-value">
          <div class="title-row right">
            <i class="t-l" /><span>渔业综合产值</span><i class="t-r" />
            <div class="group-btns dense">
              <button
                v-for="t in valueTabs"
                :key="'v'+t.value"
                type="button"
                :class="{ on: valueTab === t.value }"
                @click="valueTab = t.value"
              >{{ t.label }}</button>
            </div>
          </div>
          <div class="yzclyg panel-frame grow">
            <div ref="valueEl" class="yzclyg-chart" />
            <div class="customize-legend">
              <div v-for="(x, i) in valueItems" :key="x.name" class="list-item">
                <div class="list-item__left">
                  <span class="list-item__ring" :style="{ borderColor: VALUE_COLORS[i % VALUE_COLORS.length] }" />
                  <span class="list-item__label" :style="{ color: VALUE_COLORS[i % VALUE_COLORS.length] }">{{ x.name }}</span>
                </div>
                <div class="list-item__right">
                  <div class="bar-track">
                    <i :style="{ width: valueBarPct(x) + '%', background: VALUE_COLORS[i % VALUE_COLORS.length] }" />
                  </div>
                  <span class="list-item__val" :style="{ color: VALUE_COLORS[i % VALUE_COLORS.length] }">{{ x.value }}万元</span>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section class="panel panel-dev">
          <div class="title-row right">
            <i class="t-l" /><span>设备类型分析</span><i class="t-r" />
          </div>
          <div class="sblx-grid panel-frame grow">
            <div v-for="d in (data.devices || [])" :key="d.name" class="sblx-card">
              <div
                class="card-icon-wrap"
                :style="{
                  backgroundColor: d.bg || 'rgba(10,189,255,.1)',
                  borderColor: d.color || 'rgba(10,189,255,.5)',
                }"
              >
                <img v-if="d.icon" :src="d.icon" alt="" />
              </div>
              <div class="card-right">
                <div class="card-name">{{ d.name }}</div>
                <div class="card-value">{{ d.count }}<span class="unit">个</span></div>
              </div>
            </div>
          </div>
        </section>

        <section class="panel panel-mode">
          <div class="title-row right">
            <i class="t-l" /><span>养殖模式</span><i class="t-r" />
            <div class="group-btns">
              <button type="button" :class="{ on: modeDim === 'area' }" @click="modeDim = 'area'">面积</button>
              <button type="button" :class="{ on: modeDim === 'count' }" @click="modeDim = 'count'">尾数</button>
            </div>
          </div>
          <div class="yzms-progress-group panel-frame grow">
            <div v-for="m in modesView" :key="m.name" class="progress-item">
              <div class="progress-name">{{ m.name }}</div>
              <div class="progress-value">{{ m.display }}</div>
              <div class="progress-ball-wrap" :style="{ '--c': m.color, '--p': m.pct }">
                <div class="wave-ball">
                  <div class="wave" :style="{ height: m.pct + '%' }" />
                  <span>{{ m.pct }}%</span>
                </div>
              </div>
            </div>
          </div>
        </section>
      </aside>
    </div>

    <div class="bottom-frame" />
    <footer class="page-menu">
      <div class="is-menu">
        <button type="button" class="menu-item active">首页</button>
        <button type="button" class="menu-item" @click="goRecords">生产记录</button>
      </div>
      <button type="button" class="full-screen-btn" @click="toggleFs">{{ isFs ? '退出全屏' : '全屏' }}</button>
    </footer>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import Map from 'ol/Map'
import View from 'ol/View'
import Overlay from 'ol/Overlay'
import { fromLonLat, toLonLat } from 'ol/proj'
import VectorLayer from 'ol/layer/Vector'
import VectorSource from 'ol/source/Vector'
import GeoJSON from 'ol/format/GeoJSON'
import Feature from 'ol/Feature'
import Point from 'ol/geom/Point'
import { Fill, Stroke, Style, Circle as CircleStyle } from 'ol/style'
import 'ol/ol.css'
import http from '@/api/http'
import { makeBasemapLayer } from '@/utils/basemap'
import { wgs84ToGcj02 } from '@/utils/gis'
import { DEMO_MAP_CENTER, DEMO_MAP_GEOJSON } from '@/config/demoMap'

/** API 返回 WGS-84，天地图/区划 GeoJSON 按 GCJ-02 展示 */
function mapCoord(lon, lat) {
  const g = wgs84ToGcj02(Number(lon), Number(lat))
  return fromLonLat([g.lng, g.lat])
}

const ASSET = '/cockpit'
const router = useRouter()
const data = ref({})
const isFs = ref(false)
const rankUnit = ref('ton')
const yieldTab = ref('')
const valueTab = ref('')
const modeDim = ref('area')
const activeTown = ref('')
const activeVillage = ref('')
/** district = 区级总览；town = 已下钻到乡镇 */
const drillLevel = ref('district')
const districtExtent = ref(null)
const hoverTown = ref('')

const yieldTabs = [
  { label: '总计', value: '' },
  { label: '第一季度', value: '1' },
  { label: '第二季度', value: '2' },
  { label: '第三季度', value: '3' },
  { label: '第四季度', value: '4' },
]
const valueTabs = yieldTabs
const DOT_COLORS = ['#46B2FF', '#FFDF75', '#8968FF', '#26FFBA']
const VALUE_COLORS = ['#E6C07B', '#4FC3F7', '#87D068']
const MODE_COLORS = { 水库养殖: '#0AF1FF', 陆基圆桶: '#008AFF', 池塘: '#F5A623', 大鲵: '#7ED321' }
const STACK_COLORS = [
  ['#FCFF66', '#A8AD2B'],
  ['#26FFBA', '#1AAF80'],
  ['#589BFF', '#2E5FBB'],
  ['#FF5858', '#B33030'],
  ['#FF8D58', '#B35E2E'],
  ['#87FF58', '#5BB32E'],
]

const screenRef = ref(null)
const mapEl = ref(null)
const pinHost = ref(null)
const rankEl = ref(null)
const seedEl = ref(null)
const yieldEl = ref(null)
const valueEl = ref(null)
let map
let vectorSource
let townPointSource
let highlightOverlay
let popupOverlay
/** @type {import('ol/Overlay').default[]} */
let labelOverlays = []
let charts = {}

const kpis = computed(() => {
  const k = data.value.kpis || {}
  return [
    { label: '养殖主体 (户)', value: k.enterpriseCount ?? 38, tone: 't1', icon: `${ASSET}/yzcl.01b867c9.png` },
    { label: '养殖总面积 (万亩)', value: k.areaWanMu ?? 0.1538, tone: 't2', icon: `${ASSET}/yzmj.662c5220.png` },
    { label: '物联设备 (个)', value: k.deviceCount ?? 55, tone: 't3', icon: `${ASSET}/szjc_ic.090e9f6b.png` },
    { label: '视频监控 (个)', value: k.cameraCount ?? 31, tone: 't4', icon: `${ASSET}/jk_ic.af327e09.png` },
  ]
})

const yieldPack = computed(() => {
  const tabs = data.value.yieldByQuarter || {}
  const base = tabs[yieldTab.value] || tabs[''] || data.value.yield || { total: 4841, items: [] }
  if (drillLevel.value !== 'town') return base
  const town = findTown(activeTown.value)
  const ratio = Math.max(0.08, Math.min(0.55, Number(town?.areaMu || 1000) / 30000))
  return {
    total: Math.round(Number(base.total || 0) * ratio),
    items: (base.items || []).map((x) => ({
      ...x,
      value: Math.round(Number(x.value || 0) * ratio),
    })),
  }
})
const yieldItems = computed(() => yieldPack.value.items || [])

const valuePack = computed(() => {
  const tabs = data.value.outputByQuarter || {}
  const base = tabs[valueTab.value] || tabs[''] || data.value.outputValue || { total: '26114.00', items: [] }
  if (drillLevel.value !== 'town') return base
  const town = findTown(activeTown.value)
  const ratio = Math.max(0.08, Math.min(0.55, Number(town?.areaMu || 1000) / 30000))
  const items = (base.items || []).map((x) => ({
    ...x,
    value: Number((Number(x.value || 0) * ratio).toFixed(1)),
  }))
  const total = items.reduce((s, x) => s + Number(x.value || 0), 0)
  return { total: total.toFixed(2), items }
})
const valueItems = computed(() => valuePack.value.items || [])
const valueTotal = computed(() =>
  valueItems.value.reduce((s, x) => s + Number(x.value || 0), 0) || 1,
)
function valueBarPct(x) {
  return Math.max(6, Math.round((Number(x.value || 0) / valueTotal.value) * 100))
}

const modesView = computed(() =>
  (data.value.modes || []).map((m) => ({
    name: m.name,
    pct: modeDim.value === 'area' ? m.areaPct : m.countPct,
    display: modeDim.value === 'area' ? m.areaText : m.countText,
    color: MODE_COLORS[m.name] || '#0AF1FF',
  })),
)

const townPopup = computed(() => {
  if (activeVillage.value) {
    const town = findTown(activeTown.value)
    const v = (town?.villages || []).find((x) => x.name === activeVillage.value)
    if (!v) return null
    return {
      name: v.name,
      count: v.count,
      area: Number(v.areaMu).toFixed(2),
      pondCount: v.pondCount,
      species: (data.value.speciesRankDetail?.[activeTown.value] || []).slice(0, 4),
      lon: v.lon,
      lat: v.lat,
    }
  }
  const name =
    drillLevel.value === 'town'
      ? activeTown.value
      : hoverTown.value || activeTown.value
  if (!name) return null
  const town = findTown(name)
  if (!town) return null
  const detail = (data.value.speciesRankDetail || {})[name] || []
  return {
    name: town.name,
    count: town.count,
    area: Number(town.areaMu ?? 0).toFixed(2),
    pondCount: town.pondCount ?? '-',
    species: detail.slice(0, 6),
    lon: town.lon,
    lat: town.lat,
  }
})

function findTown(name) {
  return (data.value.towns || []).find((x) => x.name === name)
}

function selectTown(name) {
  activeTown.value = name
  activeVillage.value = ''
  nextTick(() => {
    renderCharts()
    syncMapLabels()
    syncPopupOverlay()
  })
}

function drillIntoTown(name) {
  const town = findTown(name)
  if (!town) return
  activeTown.value = name
  activeVillage.value = ''
  hoverTown.value = ''
  drillLevel.value = 'town'
  nextTick(() => {
    renderCharts()
    syncMapLabels()
    flyToTown(town, 12.4)
    setHighlightMarker(town)
    syncPopupOverlay()
  })
}

function selectVillage(v) {
  activeVillage.value = v.name
  if (v.lon && v.lat && map) {
    map.getView().animate({
      center: mapCoord(v.lon, v.lat),
      zoom: 13.2,
      duration: 650,
    })
    setHighlightMarker(v)
    syncMapLabels()
    syncPopupOverlay()
  }
}

function exitDrill() {
  drillLevel.value = 'district'
  activeVillage.value = ''
  hoverTown.value = ''
  clearHighlightMarker()
  nextTick(() => {
    renderCharts()
    syncMapLabels()
    syncPopupOverlay()
    if (map && districtExtent.value) {
      map.getView().fit(districtExtent.value, { padding: [100, 60, 90, 60], maxZoom: 11.5, duration: 700 })
    }
  })
}

function clearLabelOverlays() {
  if (!map) return
  labelOverlays.forEach((ov) => map.removeOverlay(ov))
  labelOverlays = []
  if (pinHost.value) pinHost.value.innerHTML = ''
}

function makePinEl(item, kind) {
  const wrap = document.createElement('div')
  wrap.className = `kjxx-map-label-wrap ol-pin ${kind === 'village' ? 'is-village' : ''}`
  const on =
    kind === 'village' ? item.name === activeVillage.value : item.name === activeTown.value
  const label = document.createElement('div')
  label.className = `kjxx-map-label${on ? ' kjxx-map-label--active' : ''}`
  if (kind === 'village') {
    label.innerHTML = `<div class="kjxx-map-label__header"><span class="kjxx-map-label__name">${item.name}</span></div>
      <div class="kjxx-map-label__body"><span class="kjxx-map-label__value">${item.areaMu}</span><span class="kjxx-map-label__unit">亩</span></div>`
  } else {
    label.innerHTML = `<div class="kjxx-map-label__header"><span class="kjxx-map-label__name">${item.name}</span></div>
      <div class="kjxx-map-label__body"><span class="kjxx-map-label__value">${item.count}</span><span class="kjxx-map-label__unit">户</span></div>`
  }
  wrap.appendChild(label)
  wrap.addEventListener('click', (e) => {
    e.stopPropagation()
    if (kind === 'village') selectVillage(item)
    else drillIntoTown(item.name)
  })
  if (kind === 'town') {
    wrap.addEventListener('mouseenter', () => {
      if (drillLevel.value !== 'district') return
      hoverTown.value = item.name
      syncPopupOverlay()
    })
    wrap.addEventListener('mouseleave', () => {
      if (drillLevel.value !== 'district') return
      if (hoverTown.value === item.name) hoverTown.value = ''
      syncPopupOverlay()
    })
  }
  return wrap
}

function syncMapLabels() {
  if (!map) return
  clearLabelOverlays()
  const host = pinHost.value || mapEl.value
  if (!host) return

  if (drillLevel.value === 'district') {
    ;(data.value.towns || []).forEach((t) => {
      if (!t.lon || !t.lat) return
      const el = makePinEl(t, 'town')
      host.appendChild(el)
      const ov = new Overlay({
        element: el,
        positioning: 'bottom-center',
        offset: [0, -4],
        stopEvent: true,
      })
      ov.setPosition(mapCoord(t.lon, t.lat))
      map.addOverlay(ov)
      labelOverlays.push(ov)
    })
  } else {
    const town = findTown(activeTown.value)
    ;(town?.villages || []).forEach((v) => {
      if (!v.lon || !v.lat) return
      const el = makePinEl(v, 'village')
      host.appendChild(el)
      const ov = new Overlay({
        element: el,
        positioning: 'bottom-center',
        offset: [0, -4],
        stopEvent: true,
      })
      ov.setPosition(mapCoord(v.lon, v.lat))
      map.addOverlay(ov)
      labelOverlays.push(ov)
    })
  }
  // 点图层：区级显示全部乡镇点，下钻只显示当前乡镇中心点
  if (townPointSource) {
    townPointSource.clear()
    if (drillLevel.value === 'district') {
      ;(data.value.towns || []).forEach((t) => {
        if (!t.lon || !t.lat) return
        townPointSource.addFeature(
          new Feature({
            geometry: new Point(mapCoord(t.lon, t.lat)),
            name: t.name,
            kind: 'town',
          }),
        )
      })
    } else {
      const town = findTown(activeTown.value)
      ;(town?.villages || []).forEach((v) => {
        if (!v.lon || !v.lat) return
        townPointSource.addFeature(
          new Feature({
            geometry: new Point(mapCoord(v.lon, v.lat)),
            name: v.name,
            kind: 'village',
            payload: v,
          }),
        )
      })
    }
  }
}

function ensurePopupOverlay() {
  if (!map || popupOverlay) return
  const el = document.createElement('div')
  el.className = 'map-popup ol-popup'
  el.style.display = 'none'
  ;(pinHost.value || mapEl.value)?.appendChild(el)
  popupOverlay = new Overlay({
    element: el,
    positioning: 'bottom-left',
    offset: [14, -12],
    stopEvent: false,
  })
  map.addOverlay(popupOverlay)
}

function syncPopupOverlay() {
  if (!map) return
  ensurePopupOverlay()
  const el = popupOverlay.getElement()
  const pop = townPopup.value
  // 区级：悬停才显示；乡镇级：常驻
  const show =
    !!pop?.lon &&
    !!pop?.lat &&
    (drillLevel.value === 'town' || (drillLevel.value === 'district' && !!hoverTown.value))
  if (!show) {
    el.style.display = 'none'
    popupOverlay.setPosition(undefined)
    return
  }
  const speciesHtml = (pop.species || [])
    .map(
      (s, i) =>
        `<div class="mp-row"><em><i style="background:${DOT_COLORS[i % DOT_COLORS.length]}"></i>${s.name}</em><b>${s.value}</b></div>`,
    )
    .join('')
  el.innerHTML = `<div class="mp-h">${pop.name}</div>
    <div class="mp-row"><em>养殖户</em><b>${pop.count}户</b></div>
    <div class="mp-row"><em>塘口面积</em><b>${pop.area}亩</b></div>
    <div class="mp-row"><em>塘口数量</em><b>${pop.pondCount}块</b></div>
    ${speciesHtml}`
  el.style.display = 'block'
  popupOverlay.setPosition(mapCoord(pop.lon, pop.lat))
}

function setHighlightMarker(pt) {
  if (!map || !pt?.lon || !pt?.lat) return
  clearHighlightMarker()
  const el = document.createElement('div')
  el.className = 'kjxx-map-marker'
  el.innerHTML = '<i class="pulse"></i><i class="core"></i>'
  highlightOverlay = new Overlay({
    element: el,
    positioning: 'center-center',
    stopEvent: false,
  })
  map.addOverlay(highlightOverlay)
  highlightOverlay.setPosition(mapCoord(pt.lon, pt.lat))
}

function clearHighlightMarker() {
  if (highlightOverlay && map) {
    map.removeOverlay(highlightOverlay)
    highlightOverlay = null
  }
}

function flyToTown(town, zoom = 12.2) {
  if (!map || !town?.lon || !town?.lat) return
  map.getView().animate({
    center: mapCoord(town.lon, town.lat),
    zoom,
    duration: 800,
  })
}

function toast(msg) {
  ElMessage.info(`${msg}：演示入口`)
}
function goBack() {
  router.push('/gov/workbench')
}
function goRecords() {
  router.push('/gov/party/enterprises')
}

function initMap() {
  if (!mapEl.value || map) return
  vectorSource = new VectorSource()
  townPointSource = new VectorSource()
  const base = makeBasemapLayer('td-img')
  base.setOpacity(0.5)
  map = new Map({
    target: mapEl.value,
    layers: [
      base,
      new VectorLayer({
        source: vectorSource,
        style: new Style({
          fill: new Fill({ color: 'rgba(10, 90, 200, 0.28)' }),
          stroke: new Stroke({ color: '#4de6ff', width: 2.6 }),
        }),
      }),
      new VectorLayer({
        source: townPointSource,
        zIndex: 20,
        // 透明命中圆：视觉交给 kjxx-map-label，避免双重点位
        style: () =>
          new Style({
            image: new CircleStyle({
              radius: 16,
              fill: new Fill({ color: 'rgba(0,0,0,0)' }),
              stroke: new Stroke({ color: 'rgba(0,0,0,0)', width: 0 }),
            }),
          }),
      }),
    ],
    view: new View({ center: mapCoord(DEMO_MAP_CENTER.lng, DEMO_MAP_CENTER.lat), zoom: 10.2 }),
    controls: [],
  })
  map.on('singleclick', (evt) => {
    const hit = map.forEachFeatureAtPixel(evt.pixel, (f) => f, {
      layerFilter: (ly) => ly.getSource() === townPointSource,
    })
    if (hit) {
      const kind = hit.get('kind')
      if (kind === 'village') {
        const payload = hit.get('payload')
        if (payload) selectVillage(payload)
        else {
          const [lon, lat] = toLonLat(hit.getGeometry().getCoordinates())
          selectVillage({ name: hit.get('name'), lon, lat, areaMu: '-', count: '-', pondCount: '-' })
        }
      } else {
        const name = hit.get('name')
        if (name) drillIntoTown(name)
      }
      return
    }
    if (drillLevel.value === 'town') {
      activeVillage.value = ''
      const town = findTown(activeTown.value)
      if (town) setHighlightMarker(town)
      syncMapLabels()
      syncPopupOverlay()
    }
  })
}

async function loadLayers() {
  const fmt = new GeoJSON()
  vectorSource.clear()
  try {
    const gj = await fetch(DEMO_MAP_GEOJSON).then((r) => r.json())
    const feats = fmt.readFeatures(gj, { dataProjection: 'EPSG:4326', featureProjection: 'EPSG:3857' })
    feats.forEach((f) => vectorSource.addFeature(f))
  } catch {
    /* ignore */
  }
  try {
    const res = await http.get('/party/gis/layers', { params: { mode: 'stats' } })
    for (const p of res.data?.ponds || []) {
      if (!p.geomGeojson) continue
      try {
        const obj = typeof p.geomGeojson === 'string' ? JSON.parse(p.geomGeojson) : p.geomGeojson
        const geom = fmt.readGeometry(obj, { dataProjection: 'EPSG:4326', featureProjection: 'EPSG:3857' })
        vectorSource.addFeature(new Feature({ geometry: geom, _pond: true }))
      } catch {
        /* skip */
      }
    }
  } catch {
    /* ignore */
  }
  map.getLayers().item(1).setStyle((feature) => {
    if (feature.get('_pond')) {
      return new Style({
        fill: new Fill({ color: 'rgba(61, 255, 232, 0.18)' }),
        stroke: new Stroke({ color: 'rgba(61, 255, 232, 0.55)', width: 1 }),
      })
    }
    const on = drillLevel.value === 'town' && activeTown.value
    return new Style({
      fill: new Fill({ color: on ? 'rgba(0, 102, 255, 0.22)' : 'rgba(12, 100, 210, 0.32)' }),
      stroke: new Stroke({ color: on ? 'rgba(0, 220, 255, 0.95)' : '#4de6ff', width: on ? 2.2 : 2.8 }),
    })
  })
  if (vectorSource.getFeatures().length) {
    const ext = vectorSource.getExtent()
    districtExtent.value = ext
    map.getView().fit(ext, { padding: [100, 60, 90, 60], maxZoom: 11.2 })
  }
  syncMapLabels()
  syncPopupOverlay()
}

function ensureChart(key, el) {
  if (!el) return null
  if (!charts[key]) charts[key] = echarts.init(el)
  return charts[key]
}

function renderCharts() {
  renderRank()
  renderSeed()
  renderYield()
  renderValue()
}

function renderRank() {
  const rank = ensureChart('rank', rankEl.value)
  const allTowns = (data.value.speciesRank || []).map((x) => x.name)
  // 下钻后只展示当前乡镇品种构成（横轴品种），区级则展示各乡镇堆叠
  const drilled = drillLevel.value === 'town'
  const detail = data.value.speciesRankDetail || {}
  const lineRaw = data.value.speciesRankLine || allTowns.map((_, i) => (data.value.speciesRank?.[i]?.value || 0) * 0.12)

  let towns = allTowns
  let speciesNames = []
  let categories = allTowns
  let series

  if (drilled) {
    const rows = detail[activeTown.value] || []
    categories = rows.map((x) => x.name)
    speciesNames = categories
    series = [
      {
        name: '面积(亩)',
        type: 'bar',
        barWidth: 18,
        yAxisIndex: 0,
        data: rows.map((x) => Number(x.value)),
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: '#FCFF66' },
            { offset: 1, color: '#A8AD2B' },
          ]),
        },
      },
      {
        name: rankUnit.value === 'tail' ? '尾' : '吨',
        type: 'line',
        yAxisIndex: 1,
        smooth: true,
        symbol: 'circle',
        symbolSize: 7,
        lineStyle: { width: 2, color: '#FFDF75' },
        itemStyle: { color: '#FFDF75' },
        data: rows.map((x, i) => Number((x.value * (rankUnit.value === 'tail' ? 0.9 : 0.12) * (1.1 - i * 0.05)).toFixed(1))),
      },
    ]
  } else {
    towns.forEach((t) => {
      ;(detail[t] || []).forEach((s) => {
        if (!speciesNames.includes(s.name)) speciesNames.push(s.name)
      })
    })
    const lineName = rankUnit.value === 'tail' ? '尾' : '吨'
    const lineScale = rankUnit.value === 'tail' ? 8 : 1
    series = speciesNames.slice(0, 6).map((sp, i) => {
      const [c0, c1] = STACK_COLORS[i % STACK_COLORS.length]
      return {
        name: sp,
        type: 'bar',
        stack: 'area',
        barWidth: 14,
        yAxisIndex: 0,
        data: towns.map((t) => {
          const row = (detail[t] || []).find((x) => x.name === sp)
          return row ? Number(row.value.toFixed(1)) : 0
        }),
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: c0 },
            { offset: 1, color: c1 },
          ]),
        },
      }
    })
    series.push({
      name: lineName,
      type: 'line',
      yAxisIndex: 1,
      smooth: true,
      symbol: 'circle',
      symbolSize: 7,
      lineStyle: { width: 2, color: '#FFDF75' },
      itemStyle: { color: '#FFDF75' },
      data: lineRaw.map((v) => Number((Number(v) * lineScale).toFixed(1))),
    })
  }

  const lineName = rankUnit.value === 'tail' ? '尾' : '吨'
  rank?.setOption({
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(4,20,48,.95)',
      borderColor: '#0abdff',
      textStyle: { color: '#e8f4ff', fontSize: 11 },
    },
    legend: {
      top: 0,
      right: 0,
      textStyle: { color: '#9fd4ff', fontSize: 10 },
      itemWidth: 10,
      itemHeight: 8,
      type: 'scroll',
    },
    grid: { left: 44, right: 44, top: 28, bottom: 28 },
    xAxis: {
      type: 'category',
      data: categories,
      axisLabel: {
        color: (v) => (!drilled && v === activeTown.value ? '#02EEFF' : '#9fd4ff'),
        fontSize: 10,
        rotate: categories.length > 6 ? 25 : 0,
      },
      axisLine: { lineStyle: { color: 'rgba(33,148,206,.45)' } },
      axisTick: { show: false },
      triggerEvent: true,
    },
    yAxis: [
      {
        type: 'value',
        name: '单位：亩',
        nameTextStyle: { color: '#8eb4d8', fontSize: 10 },
        splitLine: { lineStyle: { color: 'rgba(33,148,206,.22)' } },
        axisLabel: { color: '#fff', fontSize: 10 },
        axisLine: { show: false },
        axisTick: { show: false },
      },
      {
        type: 'value',
        name: '单位：' + lineName,
        nameTextStyle: { color: '#8eb4d8', fontSize: 10 },
        splitLine: { show: false },
        axisLabel: { color: '#FFDF75', fontSize: 10 },
        axisLine: { show: false },
        axisTick: { show: false },
      },
    ],
    series,
  }, true)
  rank?.off('click')
  rank?.on('click', (p) => {
    if (drilled) return
    const name = p?.name
    if (typeof name === 'string' && allTowns.includes(name)) drillIntoTown(name)
  })
}

function renderSeed() {
  const seed = ensureChart('seed', seedEl.value)
  const seeds = data.value.seedlings || []
  const active =
    seeds.find((x) => x.name === activeTown.value) ||
    seeds.find((x) => x.name === '红庙镇') ||
    seeds[0]
  seed?.setOption({
    backgroundColor: 'transparent',
    tooltip: { trigger: 'item', formatter: '{b}<br/>{c} 万尾' },
    title: {
      text: active ? `${active.name}\n${active.value}万尾` : '',
      left: 'center',
      top: '40%',
      textStyle: { color: '#fff', fontSize: 13, fontWeight: 700, lineHeight: 18 },
    },
    angleAxis: {
      type: 'category',
      data: seeds.map((x) => x.name),
      startAngle: 90,
      axisLabel: { color: '#9fd4ff', fontSize: 10, interval: 6 },
      axisLine: { lineStyle: { color: 'rgba(11,125,255,.35)' } },
      splitLine: { show: false },
    },
    radiusAxis: {
      axisLabel: { show: false },
      axisTick: { show: false },
      axisLine: { show: false },
      splitLine: { lineStyle: { color: 'rgba(11,125,255,.16)' } },
    },
    polar: { radius: ['26%', '74%'] },
    series: [
      {
        type: 'bar',
        coordinateSystem: 'polar',
        roundCap: true,
        data: seeds.map((x) => ({
          value: x.value,
          itemStyle: {
            color:
              x.name === (active?.name || '')
                ? new echarts.graphic.LinearGradient(0, 0, 1, 0, [
                    { offset: 0, color: 'rgba(2,238,255,0)' },
                    { offset: 1, color: '#02EEFF' },
                  ])
                : new echarts.graphic.LinearGradient(0, 0, 1, 0, [
                    { offset: 0, color: 'rgba(11,125,255,0)' },
                    { offset: 1, color: '#0B7DFF' },
                  ]),
          },
        })),
        barWidth: 10,
      },
    ],
  }, true)
  seed?.off('click')
  seed?.on('click', (p) => {
    const name = typeof p?.name === 'string' ? p.name : seeds[p?.dataIndex]?.name
    if (name) drillIntoTown(name)
  })
}

function renderYield() {
  const yld = ensureChart('yield', yieldEl.value)
  const pack = yieldPack.value
  const items = pack.items || []
  const totalPct = items.reduce((s, x) => s + (x.pct || 0), 0) || 1
  const dots = []
  let ang = -Math.PI / 2
  items.forEach((it, idx) => {
    const share = (it.pct || 0) / totalPct
    const n = Math.max(10, Math.round(140 * share))
    for (let i = 0; i < n; i++) {
      const a = ang + (share * Math.PI * 2 * i) / n
      const r = 36 + (i % 4) * 2.2
      dots.push({
        value: [50 + Math.cos(a) * r, 50 + Math.sin(a) * r],
        itemStyle: { color: DOT_COLORS[idx % DOT_COLORS.length] },
      })
    }
    ang += share * Math.PI * 2
  })
  yld?.setOption({
    backgroundColor: 'transparent',
    grid: { left: 0, right: 0, top: 0, bottom: 0 },
    xAxis: { min: 0, max: 100, show: false },
    yAxis: { min: 0, max: 100, show: false },
    series: [
      { type: 'scatter', symbolSize: 4, data: dots, silent: true },
      {
        type: 'scatter',
        symbolSize: 78,
        data: [{ value: [50, 50] }],
        itemStyle: { color: 'rgba(6,24,52,.82)', borderColor: '#46B2FF', borderWidth: 1 },
        label: {
          show: true,
          formatter: `${pack.total ?? 4841}\n总产量(吨)`,
          color: '#fff',
          fontSize: 13,
          fontWeight: 700,
          lineHeight: 18,
        },
        z: 3,
      },
    ],
  }, true)
}

function renderValue() {
  const val = ensureChart('value', valueEl.value)
  const pack = valuePack.value
  const items = pack.items || []
  val?.setOption({
    backgroundColor: 'transparent',
    title: {
      text: `${pack.total ?? '26114.00'}\n总产值(万元)`,
      left: 'center',
      top: '36%',
      textStyle: { color: '#fff', fontSize: 13, fontWeight: 700, lineHeight: 18, fontFamily: 'kufang, Microsoft YaHei' },
    },
    series: [{
      type: 'pie',
      radius: ['58%', '78%'],
      center: ['50%', '50%'],
      label: { show: false },
      data: items.map((x, i) => ({
        name: x.name,
        value: x.value,
        itemStyle: { color: VALUE_COLORS[i % VALUE_COLORS.length] },
      })),
    }],
  }, true)
}

function resizeAll() {
  Object.values(charts).forEach((c) => c?.resize())
  map?.updateSize()
}

function applyScreenScale() {
  const el = screenRef.value
  if (!el) return
  const baseW = 1920
  const baseH = 1080
  const scale = Math.min(window.innerWidth / baseW, window.innerHeight / baseH, 1.25)
  el.style.transform = `translate(-50%, -50%) scale(${scale})`
  nextTick(resizeAll)
}

async function load() {
  try {
    const res = await http.get('/analytics/cockpit')
    data.value = res.data || {}
  } catch {
    data.value = {}
  }
  await nextTick()
  initMap()
  await loadLayers()
  renderCharts()
}

async function toggleFs() {
  if (!document.fullscreenElement) {
    await document.documentElement.requestFullscreen?.()
    isFs.value = true
  } else {
    await document.exitFullscreen?.()
    isFs.value = false
  }
  nextTick(resizeAll)
}
function onFs() {
  isFs.value = !!document.fullscreenElement
  nextTick(resizeAll)
}

watch([rankUnit, yieldTab, valueTab, modeDim, drillLevel, activeTown], () => nextTick(renderCharts))
onMounted(() => {
  load()
  document.addEventListener('fullscreenchange', onFs)
  window.addEventListener('resize', applyScreenScale)
  applyScreenScale()
})
onUnmounted(() => {
  document.removeEventListener('fullscreenchange', onFs)
  window.removeEventListener('resize', applyScreenScale)
  clearHighlightMarker()
  clearLabelOverlays()
  if (popupOverlay && map) {
    map.removeOverlay(popupOverlay)
    popupOverlay = null
  }
  if (map) {
    map.setTarget(null)
    map = null
  }
  Object.values(charts).forEach((c) => c?.dispose())
})
</script>

<style scoped>
@font-face {
  font-family: youshe;
  src: url('/cockpit/youshe.ttf') format('truetype');
  font-display: swap;
}
@font-face {
  font-family: pangmen;
  src: url('/cockpit/pangmen.ttf') format('truetype');
  font-display: swap;
}
@font-face {
  font-family: douyu;
  src: url('/cockpit/douyu.otf') format('opentype');
  font-display: swap;
}
@font-face {
  font-family: kufang;
  src: url('/cockpit/kufang.ttf') format('truetype');
  font-display: swap;
}

.kjxx-screen {
  --cyan: #02eeff;
  --blue: #0abdff;
  position: fixed;
  top: 50%;
  left: 50%;
  z-index: 50;
  width: 1920px;
  height: 1080px;
  transform: translate(-50%, -50%);
  transform-origin: center center;
  overflow: hidden;
  color: #e8f4ff;
  background: #000b1a;
}
/* 对齐现网 .mapPage { background: url(bg_wrap) } */
.screen-bg {
  position: absolute;
  inset: 0;
  z-index: 0;
  background: url('/cockpit/bg_wrap.9eb85a01.jpg') no-repeat center center / cover;
  filter: saturate(0.85) brightness(0.72) contrast(1.08) hue-rotate(8deg);
  transform: scale(1.02);
  pointer-events: none;
}
.screen-vignette {
  position: absolute;
  inset: 0;
  z-index: 1;
  pointer-events: none;
  background:
    radial-gradient(ellipse at 50% 42%, rgba(10, 80, 160, 0.18), transparent 42%),
    radial-gradient(ellipse at center, transparent 30%, rgba(0, 8, 20, 0.72) 100%),
    linear-gradient(180deg, rgba(0, 12, 28, 0.55), transparent 18%, transparent 78%, rgba(0, 8, 18, 0.7));
}
.tech-grid {
  position: absolute;
  inset: 0;
  z-index: 1;
  pointer-events: none;
  opacity: 0.18;
  background-image:
    linear-gradient(rgba(2, 238, 255, 0.07) 1px, transparent 1px),
    linear-gradient(90deg, rgba(2, 238, 255, 0.07) 1px, transparent 1px);
  background-size: 48px 48px;
  mask-image: radial-gradient(ellipse at center, #000 35%, transparent 78%);
}

.page-header {
  position: absolute;
  top: 0;
  left: 0;
  z-index: 6;
  width: 100%;
  height: 86px;
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding-top: 18px;
  box-sizing: border-box;
  background: url('/cockpit/bg_header.3f43da79.png') no-repeat center / 100% 100%;
  pointer-events: none;
}
.page-header h1 {
  margin: 0;
  font-family: youshe, pangmen, "Microsoft YaHei", sans-serif;
  font-size: 34px;
  letter-spacing: 6px;
  font-weight: 400;
  color: #fff;
  text-shadow: 0 0 18px rgba(16, 96, 255, 0.65);
}
.btn-setting {
  pointer-events: auto;
  position: absolute;
  right: 22px;
  top: 18px;
  border: 0;
  background: transparent;
  color: #cfe9ff;
  font-family: douyu, Microsoft YaHei, sans-serif;
  font-size: 14px;
  cursor: pointer;
  padding: 6px 10px;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}
.btn-setting .gear {
  width: 16px;
  height: 16px;
  display: inline-block;
  background:
    radial-gradient(circle at center, transparent 35%, #cfe9ff 36% 48%, transparent 49%),
    conic-gradient(from 20deg, #cfe9ff 0 12%, transparent 0 25%, #cfe9ff 0 37%, transparent 0 50%, #cfe9ff 0 62%, transparent 0 75%, #cfe9ff 0 87%, transparent 0);
  border-radius: 50%;
  box-shadow: inset 0 0 0 1.5px #cfe9ff;
}

.page-body {
  position: absolute;
  inset: 78px 10px 88px;
  display: grid;
  grid-template-columns: 360px minmax(0, 1fr) 360px;
  gap: 8px;
  z-index: 4;
}
.page-left,
.page-right {
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-height: 0;
  position: relative;
  /* 现网：左右栏整块装饰底，透出背后 mapPage 底图 */
  background-repeat: no-repeat;
  background-size: 100% 100%;
  background-position: center;
}
.page-left {
  background-image: url('/cockpit/bg_left.4af176d4.png');
  padding: 8px 6px 8px 10px;
}
.page-right {
  background-image: url('/cockpit/bg_right.528b0034.png');
  padding: 8px 10px 8px 6px;
}
.page-left > *,
.page-right > * { position: relative; z-index: 1; }

.panel {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  padding: 4px 8px 6px;
  /* 玻璃态：让 bg_wrap 透出来 */
  background: linear-gradient(180deg, rgba(4, 24, 56, 0.22), rgba(2, 12, 28, 0.08));
}
.panel-frame {
  position: relative;
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  border: 1px solid rgba(64, 180, 255, 0.28);
  backdrop-filter: blur(2px);
  box-shadow: inset 0 0 24px rgba(20, 100, 220, 0.08);
  --corner: linear-gradient(var(--cyan), var(--cyan));
  background-color: rgba(2, 14, 36, 0.28);
  background-image:
    var(--corner), var(--corner),
    var(--corner), var(--corner);
  background-size: 14px 2px, 2px 14px, 14px 2px, 2px 14px;
  background-position:
    left bottom, left bottom,
    right bottom, right bottom;
  background-repeat: no-repeat;
}
.panel-frame.grow { flex: 1; }
.panel-frame::before,
.panel-frame::after {
  content: '';
  position: absolute;
  width: 14px;
  height: 14px;
  border: 2px solid var(--cyan);
  pointer-events: none;
  z-index: 2;
}
.panel-frame::before {
  top: -1px;
  left: -1px;
  border-right: 0;
  border-bottom: 0;
  box-shadow: -2px -2px 8px rgba(2, 238, 255, 0.25);
}
.panel-frame::after {
  top: -1px;
  right: -1px;
  border-left: 0;
  border-bottom: 0;
  box-shadow: 2px -2px 8px rgba(2, 238, 255, 0.25);
}
.panel-rank { flex: 1.2; }
.panel-seed { flex: 1; }
.panel-yield { flex: 1.15; }
.panel-value { flex: 1.05; }
.panel-dev { flex: 0.9; }
.panel-mode { flex: 1.05; }

.title-row {
  display: flex;
  align-items: center;
  gap: 6px;
  min-height: 28px;
  margin-bottom: 2px;
  font-family: pangmen, Microsoft YaHei, sans-serif;
  font-size: 16px;
  letter-spacing: 1px;
  color: #fff;
  position: relative;
}
.title-row .t-l,
.title-row .t-r {
  width: 18px;
  height: 18px;
  background: url('/cockpit/bg_title_left.3b5b0477.png') no-repeat center / contain;
  flex: 0 0 auto;
}
.title-row .t-r {
  background-image: url('/cockpit/bg_title_right.8b2703f3.png');
}
.title-row .group-btns {
  margin-left: auto;
  display: flex;
  gap: 3px;
  flex-wrap: wrap;
  justify-content: flex-end;
  max-width: 58%;
}
.group-btns button {
  border: 1px solid rgba(10, 189, 255, 0.35);
  background: rgba(0, 40, 80, 0.45);
  color: rgba(255, 255, 255, 0.7);
  font-size: 11px;
  line-height: 1;
  padding: 3px 6px;
  cursor: pointer;
}
.group-btns button.on {
  color: #fff;
  border-color: var(--cyan);
  box-shadow: 0 0 8px rgba(2, 238, 255, 0.35);
  background: rgba(10, 120, 220, 0.45);
}
.group-btns.dense button { padding: 2px 4px; font-size: 10px; }

.chart { flex: 1; min-height: 120px; width: 100%; }

.scpcl-content {
  flex: 1;
  min-height: 140px;
  display: flex;
  align-items: center;
  gap: 4px;
}
.scpcl-left { width: 48%; height: 100%; }
.scpcl-legend-list {
  width: 52%;
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding-left: 4px;
}
.scpcl-legend-item {
  display: grid;
  grid-template-columns: 10px 1fr auto;
  gap: 6px;
  align-items: start;
  font-size: 12px;
}
.legend-color {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  margin-top: 4px;
}
.legend-name { color: #cfe6ff; }
.legend-value { font-weight: 700; }

.map-wrap {
  position: relative;
  height: 100%;
  overflow: hidden;
  background: transparent;
  border: 0;
}
.pin-host {
  position: absolute;
  inset: 0;
  z-index: 3;
  pointer-events: none;
  overflow: hidden;
}
.pin-host :deep(.town-pin),
.pin-host :deep(.map-popup) {
  pointer-events: auto;
}
.map-photo-bg {
  position: absolute;
  inset: 0;
  z-index: 0;
  background: url('/cockpit/mapBg.197d328a.jpg') center / cover no-repeat;
  filter: saturate(0.5) brightness(0.38) contrast(1.12) hue-rotate(8deg);
  opacity: 0.55;
  pointer-events: none;
  mask-image: radial-gradient(ellipse at center, #000 48%, transparent 90%);
  -webkit-mask-image: radial-gradient(ellipse at center, #000 48%, transparent 90%);
}
.map-glow {
  position: absolute;
  inset: 4% 6%;
  z-index: 0;
  background: radial-gradient(ellipse at center, rgba(20, 140, 255, 0.28), transparent 70%);
  filter: blur(10px);
  pointer-events: none;
}
.map {
  position: absolute;
  inset: 0;
  z-index: 1;
  /* 暗蓝滤镜，和 bg_wrap 冷色统一 */
  filter: saturate(0.45) brightness(0.55) contrast(1.2) hue-rotate(12deg);
  opacity: 0.78;
  border-radius: 2px;
  mask-image: radial-gradient(ellipse at center, #000 55%, transparent 92%);
  -webkit-mask-image: radial-gradient(ellipse at center, #000 55%, transparent 92%);
}
.map-vignette {
  pointer-events: none;
  position: absolute;
  inset: 0;
  z-index: 2;
  background:
    radial-gradient(ellipse at center, transparent 38%, rgba(0, 8, 20, 0.55) 100%);
}
.content-top {
  position: absolute;
  top: 8px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 6;
  display: flex;
  gap: 28px;
  padding: 8px 18px;
  background: linear-gradient(90deg, transparent, rgba(4, 24, 56, 0.55), transparent);
}
.con-top-item { display: flex; align-items: center; gap: 10px; min-width: 128px; }
.kpi-ico {
  width: 48px;
  height: 48px;
  border-radius: 8px;
  background-color: rgba(8, 40, 96, 0.55);
  background-position: center;
  background-repeat: no-repeat;
  background-size: 70%;
  box-shadow: 0 0 14px rgba(20, 120, 255, 0.35);
  border: 1px solid rgba(120, 200, 255, 0.35);
  flex: 0 0 auto;
}
.kpi-ico.t2 { background-color: rgba(8, 70, 90, 0.55); }
.kpi-ico.t3 { background-color: rgba(30, 50, 120, 0.55); }
.kpi-ico.t4 { background-color: rgba(70, 50, 20, 0.55); }
.con-top-item .lab { font-size: 12px; color: rgba(255, 255, 255, 0.75); }
.con-top-num {
  margin-top: 2px;
  font-size: 24px;
  font-family: kufang, pangmen, sans-serif;
  color: #0abdff;
  font-weight: 700;
  text-shadow: 0 0 10px rgba(10, 189, 255, 0.45);
}

.town-pin {
  position: relative;
  transform: translateY(0);
  z-index: 4;
  cursor: pointer;
  pointer-events: auto;
  transition: transform 0.15s ease;
}
.town-pin:hover { transform: translateY(-4px); }
.pin-lab {
  background: rgba(0, 0, 0, 0.78);
  border: 1px solid rgba(160, 210, 255, 0.5);
  padding: 4px 8px;
  min-width: 72px;
  text-align: center;
  white-space: nowrap;
}
.pin-lab.sm { min-width: 64px; padding: 3px 6px; }
.pin-lab.sm .n { font-size: 11px; }
.pin-lab.sm .c { font-size: 11px; }
.town-pin.on .pin-lab {
  border-color: var(--cyan);
  box-shadow: 0 0 14px rgba(2, 238, 255, 0.45);
}
.pin-lab .n { font-size: 12px; color: #fff; }
.pin-lab .c { font-size: 13px; color: var(--cyan); font-weight: 700; }
.pin-dot {
  display: block;
  width: 8px;
  height: 8px;
  margin: 4px auto 0;
  border-radius: 50%;
  background: #02eeff;
  box-shadow: 0 0 10px #02eeff;
}
.village-pin .pin-dot {
  background: #ffdf75;
  box-shadow: 0 0 10px #ffdf75;
}
.village-pin.on .pin-lab {
  border-color: #ffdf75;
  box-shadow: 0 0 14px rgba(255, 223, 117, 0.45);
}

.btn-back-district {
  position: absolute;
  left: 18px;
  bottom: 18px;
  z-index: 8;
  min-width: 96px;
  height: 36px;
  border: 0;
  cursor: pointer;
  color: #e8f4ff;
  font-size: 13px;
  letter-spacing: 1px;
  background: url('/cockpit/fanh_bg.eae2e7d6.png') center / 100% 100% no-repeat;
  text-shadow: 0 0 8px rgba(2, 238, 255, 0.55);
}

.yzclyg {
  flex: 1;
  min-height: 130px;
  display: flex;
  align-items: center;
  gap: 6px;
}
.yzclyg-chart { width: 46%; height: 100%; min-height: 120px; }
.customize-legend {
  width: 54%;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.list-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
  font-size: 12px;
}
.list-item__left { display: flex; align-items: center; gap: 6px; min-width: 0; }
.list-item__ring {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  border: 2px solid #E6C07B;
  box-sizing: border-box;
}
.list-item__label { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.list-item__right {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 3px;
  min-width: 110px;
}
.bar-track {
  width: 100%;
  height: 4px;
  border-radius: 2px;
  background: rgba(255, 255, 255, 0.08);
  overflow: hidden;
}
.bar-track i {
  display: block;
  height: 100%;
  border-radius: 2px;
}
.list-item__val { font-weight: 700; white-space: nowrap; font-size: 11px; }

.sblx-grid {
  flex: 1;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px 10px;
  align-content: center;
  padding: 8px 4px;
}
.sblx-card { display: flex; align-items: center; gap: 10px; }
.card-icon-wrap {
  width: 48px;
  height: 48px;
  border-radius: 8px;
  border: 1px solid rgba(10, 189, 255, 0.45);
  display: grid;
  place-items: center;
  box-sizing: border-box;
  flex: 0 0 auto;
  overflow: hidden;
}
.card-icon-wrap img {
  width: 70%;
  height: 70%;
  object-fit: contain;
}
.card-name { font-size: 12px; color: rgba(255, 255, 255, 0.7); }
.card-value {
  margin-top: 2px;
  font-size: 22px;
  font-family: kufang, sans-serif;
  color: #fff;
  font-weight: 700;
}
.card-value .unit { font-size: 12px; color: var(--cyan); margin-left: 2px; }

.yzms-progress-group {
  flex: 1;
  display: flex;
  justify-content: space-around;
  align-items: center;
  gap: 6px;
  padding: 4px 2px;
}
.progress-item {
  width: 25%;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: 4px;
}
.progress-name {
  font-size: 12px;
  color: #cfe6ff;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 100%;
}
.progress-value { font-size: 11px; color: var(--cyan); }
.progress-ball-wrap {
  width: 58px;
  height: 58px;
}
.wave-ball {
  position: relative;
  width: 100%;
  height: 100%;
  border-radius: 50%;
  overflow: hidden;
  border: 1.5px solid color-mix(in srgb, var(--c) 80%, #fff);
  box-shadow: 0 0 12px color-mix(in srgb, var(--c) 45%, transparent), inset 0 0 10px rgba(0, 0, 0, 0.35);
  background: rgba(4, 16, 36, 0.85);
  display: grid;
  place-items: center;
}
.wave-ball .wave {
  position: absolute;
  left: -20%;
  bottom: 0;
  width: 140%;
  background: color-mix(in srgb, var(--c) 70%, transparent);
  border-radius: 40% 40% 0 0;
  animation: wave-shift 2.8s ease-in-out infinite;
  opacity: 0.85;
}
.wave-ball span {
  position: relative;
  z-index: 1;
  font-size: 12px;
  font-weight: 700;
  color: #fff;
  text-shadow: 0 1px 4px rgba(0, 0, 0, 0.65);
}
@keyframes wave-shift {
  0%, 100% { transform: translateX(-6%) rotate(0deg); }
  50% { transform: translateX(6%) rotate(3deg); }
}

.bottom-frame {
  position: absolute;
  left: 8%;
  right: 8%;
  bottom: 0;
  height: 70px;
  z-index: 3;
  pointer-events: none;
  border: 2px solid transparent;
  border-image: linear-gradient(90deg, transparent, rgba(2, 238, 255, 0.55), transparent) 1;
  border-top: 0;
  background:
    linear-gradient(90deg, transparent, rgba(2, 238, 255, 0.35), transparent) top / 100% 1px no-repeat,
    linear-gradient(180deg, transparent, rgba(2, 120, 255, 0.08));
  clip-path: polygon(0 0, 100% 0, 92% 100%, 8% 100%);
}

.page-menu {
  position: absolute;
  left: 50%;
  bottom: 8px;
  transform: translateX(-50%);
  z-index: 5;
  display: flex;
  flex-direction: column;
  align-items: center;
}
.is-menu { display: flex; align-items: center; justify-content: center; }
.menu-item {
  border: 0;
  min-width: 118px;
  height: 48px;
  margin: 0 14px;
  padding: 0 12px;
  cursor: pointer;
  color: #cfe9ff;
  font-family: pangmen, Microsoft YaHei, sans-serif;
  font-size: 18px;
  letter-spacing: 2px;
  background: url('/cockpit/bottom_tab.ef307880.png') no-repeat center / 100% 100%;
}
.menu-item.active {
  color: #fff;
  text-shadow: 0 0 10px rgba(2, 238, 255, 0.55);
  background-image: url('/cockpit/bottom_tab_active.d44e4f9d.png');
}
.full-screen-btn {
  border: 0;
  width: 280px;
  height: 36px;
  margin-top: 4px;
  cursor: pointer;
  color: #fff;
  font-family: pangmen, Microsoft YaHei, sans-serif;
  font-size: 14px;
  background: url('/cockpit/bg_bottom.fd759d3b.png') no-repeat center / 100% 100%;
  text-shadow: 0 0 8px #1060ff;
}

.kjxx-screen.fullscreen { position: fixed; inset: 0; z-index: 9999; }

@media (max-width: 1400px) {
  .page-body { grid-template-columns: 300px minmax(0, 1fr) 300px; }
  .page-header h1 { font-size: 28px; letter-spacing: 3px; }
  .con-top-num { font-size: 18px; }
  .menu-item { min-width: 96px; font-size: 15px; margin: 0 8px; }
}
</style>

<!-- Overlay 挂到 map 容器外，需非 scoped -->
<style>
.kjxx-map-marker {
  position: relative;
  width: 28px;
  height: 28px;
  pointer-events: none;
}
.kjxx-map-marker .core {
  position: absolute;
  left: 50%;
  top: 50%;
  width: 10px;
  height: 10px;
  margin: -5px 0 0 -5px;
  border-radius: 50%;
  background: #02eeff;
  box-shadow: 0 0 12px #02eeff;
}
.kjxx-map-marker .pulse {
  position: absolute;
  left: 50%;
  top: 50%;
  width: 28px;
  height: 28px;
  margin: -14px 0 0 -14px;
  border-radius: 50%;
  border: 2px solid rgba(2, 238, 255, 0.85);
  animation: kjxx-pulse 1.4s ease-out infinite;
}
@keyframes kjxx-pulse {
  0% { transform: scale(0.45); opacity: 1; }
  100% { transform: scale(1.35); opacity: 0; }
}

/* Overlay 创建的标签/弹窗不在 scoped 内 */
.kjxx-map-label-wrap {
  pointer-events: auto;
  cursor: pointer;
  white-space: nowrap;
}
.kjxx-map-label {
  min-width: 76px;
  text-align: center;
  border-radius: 4px;
  overflow: hidden;
  background: rgba(0, 9, 18, 0.8);
  border: 1px solid rgba(39, 118, 255, 0.35);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.45);
  font-family: pangmen, "Microsoft YaHei", sans-serif;
  letter-spacing: 1px;
}
.kjxx-map-label__header {
  min-height: 20px;
  padding: 3px 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(90deg, rgba(67, 135, 255, 0.5), rgba(67, 135, 255, 0));
}
.kjxx-map-label__name {
  font-size: 12px;
  color: #fff;
  font-weight: 500;
  line-height: 1.2;
}
.kjxx-map-label__body {
  padding: 4px 10px 6px;
  line-height: 1;
}
.kjxx-map-label__value,
.kjxx-map-label__unit {
  font-size: 16px;
  color: #fff;
  font-weight: 700;
}
.kjxx-map-label__unit {
  margin-left: 2px;
  font-size: 13px;
}
.kjxx-map-label--active {
  border: 1px solid rgba(255, 255, 255, 0.35);
  background: rgba(0, 68, 185, 0.55);
}
.is-village .kjxx-map-label__value {
  color: #ffdf75;
}

.map-popup.ol-popup {
  min-width: 188px;
  padding: 0 0 10px;
  background: rgba(4, 18, 42, 0.94);
  border: 1px solid rgba(10, 189, 255, 0.55);
  box-shadow: 0 0 18px rgba(10, 120, 255, 0.35);
  pointer-events: none;
  color: #cfe6ff;
}
.map-popup.ol-popup .mp-h {
  font-size: 14px;
  color: #fff;
  font-weight: 700;
  margin-bottom: 6px;
  padding: 8px 14px 6px;
  border-bottom: 1px solid rgba(254, 226, 0, 0.5);
  background: url('/cockpit/bg_pop_header.da00819c.png') center / 100% 100% no-repeat;
}
.map-popup.ol-popup .mp-row {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  font-size: 12px;
  padding: 4px 14px;
}
.map-popup.ol-popup .mp-row em {
  font-style: normal;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: #fee200;
  width: 42%;
}
.map-popup.ol-popup .mp-row em i {
  width: 7px;
  height: 7px;
  display: inline-block;
}
.map-popup.ol-popup .mp-row b {
  color: #fff;
  width: 58%;
  text-align: left;
  font-weight: 600;
}
</style>
