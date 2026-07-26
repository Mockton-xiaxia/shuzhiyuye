<template>
  <el-tabs v-model="tab" class="ent-tabs">
    <el-tab-pane label="基础信息" name="base">
      <el-form label-width="120px" class="ent-form">
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="主体名称" required>
              <el-input v-model="model.name" placeholder="请输入主体名称" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="主体类型" required>
              <el-select v-model="model.subjectTypeCode" placeholder="请选择主体类型" style="width:100%">
                <el-option label="养殖个体户" value="INDIVIDUAL" />
                <el-option label="养殖企业" value="ENTERPRISE" />
                <el-option label="养殖园区" value="PARK" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="身份证号">
              <el-input v-model="model.idCard" placeholder="个体户可填身份证号" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="所属区域" required>
              <el-cascader
                v-model="model.regionPath"
                :options="regionOptions"
                :props="{ value: 'value', label: 'label', children: 'children', checkStrictly: false }"
                clearable
                filterable
                style="width:100%"
                placeholder="请选择所属区域"
                @change="onRegionChange"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="上级企业">
              <el-select v-model="model.parentEnterpriseId" clearable filterable placeholder="可选" style="width:100%">
                <el-option v-for="o in parentOptions" :key="o.value" :label="o.label" :value="o.value" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="养殖品种" required>
              <el-select v-model="model.speciesList" multiple filterable allow-create default-first-option placeholder="请选择养殖品种" style="width:100%">
                <el-option v-for="s in speciesOpts" :key="s" :label="s" :value="s" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="养殖面积（亩）">
              <el-input-number v-model="model.areaMu" :min="0" :precision="2" controls-position="right" style="width:100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="年产量（吨）">
              <el-input-number v-model="model.annualOutputTon" :min="0" :precision="2" controls-position="right" style="width:100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="养殖模式">
              <el-select v-model="model.breedingMode" placeholder="请选择养殖模式" style="width:100%">
                <el-option label="池塘" value="POND" />
                <el-option label="工厂化" value="FACTORY" />
                <el-option label="稻渔综合" value="RICE_FISH" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="联系人">
              <el-input v-model="model.contactName" placeholder="请输入联系人" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="联系方式">
              <el-input v-model="model.contactPhone" placeholder="请输入联系方式" />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
    </el-tab-pane>

    <el-tab-pane label="地图定位" name="map">
      <el-form label-width="88px" class="ent-form">
        <el-form-item label="地址搜索">
          <el-input v-model="mapSearch" placeholder="输入地址关键词（演示：仅同步到地址栏）" @keyup.enter="applySearch">
            <template #append><el-button @click="applySearch">搜索</el-button></template>
          </el-input>
        </el-form-item>
        <div ref="mapEl" class="mini-map" />
        <p class="map-tip">点击地图选点，或手动填写经纬度</p>
        <el-row :gutter="16">
          <el-col :span="24">
            <el-form-item label="地址"><el-input v-model="model.address" placeholder="请输入地址" /></el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="经度"><el-input-number v-model="model.lng" :precision="6" :step="0.0001" controls-position="right" style="width:100%" @change="syncMarker" /></el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="纬度"><el-input-number v-model="model.lat" :precision="6" :step="0.0001" controls-position="right" style="width:100%" @change="syncMarker" /></el-form-item>
          </el-col>
        </el-row>
      </el-form>
    </el-tab-pane>

    <el-tab-pane label="养殖信息" name="breed">
      <div class="breed-bar">
        <el-button type="primary" size="small" @click="addBreedRow">新增行</el-button>
        <el-button size="small" @click="syncBreedFromSpecies">从品种同步</el-button>
      </div>
      <el-table :data="model.breedingItems" stripe size="small" empty-text="暂无养殖信息，可点击「从品种同步」">
        <el-table-column prop="species" label="养殖品种" width="110" />
        <el-table-column prop="ratio" label="养殖占比(%)" width="110" />
        <el-table-column prop="outSpec" label="出塘规格" width="110" />
        <el-table-column prop="yieldPerMu" label="预计亩产(kg/亩)" width="130" />
        <el-table-column prop="outMonth" label="预计出塘月" min-width="110" />
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row, $index }">
            <el-button link type="primary" @click="editBreedRow(row, $index)">编辑</el-button>
            <el-button link type="danger" @click="model.breedingItems.splice($index, 1)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-tab-pane>

    <el-tab-pane label="其他信息" name="extra">
      <el-form label-width="120px" class="ent-form">
        <el-form-item label="渔业资质">
          <el-input v-model="model.fisheryQualification" placeholder="如水产养殖证编号" />
        </el-form-item>
        <el-form-item label="主体介绍">
          <el-input v-model="model.intro" type="textarea" :rows="4" placeholder="请输入主体介绍" />
        </el-form-item>
        <el-form-item label="宣传图片">
          <div class="media-block">
            <el-upload
              list-type="picture-card"
              :file-list="imageFileList"
              :limit="9"
              accept=".jpg,.jpeg,.gif,.png"
              :http-request="(opt) => uploadMedia(opt, 'promoImages')"
              :on-remove="(f) => removeMedia(f, 'promoImages')"
            >
              <el-icon><Plus /></el-icon>
            </el-upload>
            <p class="hint">支持 jpg/jpeg/gif/png，最多 9 张</p>
          </div>
        </el-form-item>
        <el-form-item label="宣传视频">
          <div class="media-block">
            <el-upload
              :file-list="videoFileList"
              :limit="3"
              accept=".mp4,.avi,.wma"
              :http-request="(opt) => uploadMedia(opt, 'promoVideos')"
              :on-remove="(f) => removeMedia(f, 'promoVideos')"
            >
              <el-button type="primary" plain>上传视频</el-button>
            </el-upload>
            <p class="hint">支持 mp4/avi/wma，最多 3 个</p>
          </div>
        </el-form-item>
        <el-form-item label="显示大屏打点">
          <el-switch v-model="model.showOnScreen" active-text="在大屏显示" inactive-text="不显示" />
        </el-form-item>
        <el-form-item label="企业自检附件">
          <el-upload
            :file-list="attachFileList"
            :limit="9"
            accept=".jpg,.jpeg,.gif,.png,.pdf"
            :http-request="(opt) => uploadMedia(opt, 'selfCheckFiles')"
            :on-remove="(f) => removeMedia(f, 'selfCheckFiles')"
          >
            <el-button type="primary" plain>上传文件</el-button>
          </el-upload>
          <p class="hint">支持图片/PDF，最多 9 个</p>
        </el-form-item>
      </el-form>
    </el-tab-pane>
  </el-tabs>

  <el-dialog v-model="breedDlg" title="编辑养殖信息" width="480px" append-to-body destroy-on-close>
    <el-form :model="breedForm" label-width="120px">
      <el-form-item label="养殖品种"><el-input v-model="breedForm.species" /></el-form-item>
      <el-form-item label="养殖占比(%)"><el-input-number v-model="breedForm.ratio" :min="0" :max="100" style="width:100%" /></el-form-item>
      <el-form-item label="出塘规格"><el-input v-model="breedForm.outSpec" placeholder="如 2000g" /></el-form-item>
      <el-form-item label="预计亩产"><el-input-number v-model="breedForm.yieldPerMu" :min="0" style="width:100%" /></el-form-item>
      <el-form-item label="预计出塘月"><el-input v-model="breedForm.outMonth" placeholder="如 9-10月 / 全年" /></el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="breedDlg = false">取消</el-button>
      <el-button type="primary" @click="saveBreedRow">确定</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { Plus } from '@element-plus/icons-vue'
import axios from 'axios'
import Map from 'ol/Map'
import View from 'ol/View'
import VectorLayer from 'ol/layer/Vector'
import VectorSource from 'ol/source/Vector'
import { fromLonLat, toLonLat } from 'ol/proj'
import Feature from 'ol/Feature'
import Point from 'ol/geom/Point'
import { Fill, Stroke, Style, Circle as CircleStyle } from 'ol/style'
import 'ol/ol.css'
import { makeBasemapLayer } from '@/utils/basemap'
import { useAuthStore } from '@/stores/auth'
import { DEMO_MAP_CENTER } from '@/config/demoMap'

const props = defineProps({
  modelValue: { type: Object, required: true },
  regionOptions: { type: Array, default: () => [] },
  parentOptions: { type: Array, default: () => [] },
})

const emit = defineEmits(['update:modelValue'])
const auth = useAuthStore()

const model = computed({
  get: () => props.modelValue,
  set: (v) => emit('update:modelValue', v),
})

const tab = ref('base')
const mapEl = ref(null)
const mapSearch = ref('')
let olMap = null
let markerSource = null

const speciesOpts = ['大鲵', '草鱼', '鲢', '鲤', '鲫', '黄颡鱼', '甲鱼', '鲈（淡）']

const breedDlg = ref(false)
const breedEditIdx = ref(-1)
const breedForm = reactive({ species: '', ratio: null, outSpec: '', yieldPerMu: null, outMonth: '' })

function fileListFrom(urls, isImage) {
  return (urls || []).map((url, i) => ({
    name: url.split('/').pop() || `file-${i}`,
    url: url.startsWith('http') ? url : url,
    uid: `${url}-${i}`,
  }))
}

const imageFileList = computed(() => fileListFrom(model.value.promoImages, true))
const videoFileList = computed(() => fileListFrom(model.value.promoVideos))
const attachFileList = computed(() => fileListFrom(model.value.selfCheckFiles))

function findRegionId(nodes, path, depth = 0) {
  if (!nodes?.length || !path?.length) return null
  const code = path[depth]
  const node = nodes.find((n) => n.value === code)
  if (!node) return null
  if (depth === path.length - 1) return node.id
  return findRegionId(node.children, path, depth + 1)
}

function labelsFromPath(nodes, path, depth = 0, acc = []) {
  if (!nodes?.length || !path?.length || depth >= path.length) return acc
  const node = nodes.find((n) => n.value === path[depth])
  if (!node) return acc
  acc.push(node.label)
  return labelsFromPath(node.children, path, depth + 1, acc)
}

function onRegionChange(path) {
  model.value.regionPathLabel = labelsFromPath(props.regionOptions, path || []).join(',')
  model.value.regionId = findRegionId(props.regionOptions, path || [])
}

function applySearch() {
  if (mapSearch.value?.trim()) {
    model.value.address = mapSearch.value.trim()
  }
}

function initMap() {
  if (!mapEl.value || olMap) return
  markerSource = new VectorSource()
  const markerLayer = new VectorLayer({
    source: markerSource,
    style: new Style({
      image: new CircleStyle({
        radius: 8,
        fill: new Fill({ color: '#409eff' }),
        stroke: new Stroke({ color: '#fff', width: 2 }),
      }),
    }),
  })
  const lng = model.value.lng ?? DEMO_MAP_CENTER.lng
  const lat = model.value.lat ?? DEMO_MAP_CENTER.lat
  olMap = new Map({
    target: mapEl.value,
    layers: [makeBasemapLayer('td-vec'), markerLayer],
    view: new View({ center: fromLonLat([lng, lat]), zoom: 13 }),
  })
  olMap.on('click', (evt) => {
    const [lon, latVal] = toLonLat(evt.coordinate)
    model.value.lng = Math.round(lon * 1e6) / 1e6
    model.value.lat = Math.round(latVal * 1e6) / 1e6
    syncMarker()
  })
  syncMarker()
}

function syncMarker() {
  if (!markerSource || model.value.lng == null || model.value.lat == null) return
  markerSource.clear()
  markerSource.addFeature(new Feature({ geometry: new Point(fromLonLat([model.value.lng, model.value.lat])) }))
  olMap?.getView()?.setCenter(fromLonLat([model.value.lng, model.value.lat]))
}

function refreshMap() {
  nextTick(() => {
    if (tab.value === 'map') {
      if (olMap) {
        olMap.updateSize()
        syncMarker()
      } else {
        initMap()
      }
    }
  })
}

watch(tab, (t) => {
  if (t === 'map') refreshMap()
})

function addBreedRow() {
  breedEditIdx.value = -1
  Object.assign(breedForm, { species: '', ratio: null, outSpec: '', yieldPerMu: null, outMonth: '' })
  breedDlg.value = true
}

function editBreedRow(row, idx) {
  breedEditIdx.value = idx
  Object.assign(breedForm, { ...row })
  breedDlg.value = true
}

function saveBreedRow() {
  const row = { ...breedForm }
  if (breedEditIdx.value >= 0) {
    model.value.breedingItems[breedEditIdx.value] = row
  } else {
    model.value.breedingItems.push(row)
  }
  breedDlg.value = false
}

function syncBreedFromSpecies() {
  const existing = new Set((model.value.breedingItems || []).map((r) => r.species))
  for (const s of model.value.speciesList || []) {
    if (!existing.has(s)) {
      model.value.breedingItems.push({ species: s, ratio: null, outSpec: '-', yieldPerMu: null, outMonth: '全年' })
    }
  }
}

async function uploadMedia(opt, field) {
  const fd = new FormData()
  fd.append('file', opt.file)
  const token = auth.token
  try {
    const res = await axios.post('/api/v1/platform/upload', fd, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    })
    const envelope = res.data
    if (envelope?.code != null && envelope.code !== 0) {
      throw new Error(envelope.message || '上传失败')
    }
    const data = envelope?.data ?? envelope
    const url = data.url
    if (!url) return
    if (!model.value[field]) model.value[field] = []
    model.value[field].push(url)
    opt.onSuccess?.(data)
  } catch (e) {
    opt.onError?.(e)
  }
}

function removeMedia(file, field) {
  const url = file.url
  model.value[field] = (model.value[field] || []).filter((u) => u !== url)
}

onMounted(() => {
  if (tab.value === 'map') refreshMap()
})

onBeforeUnmount(() => {
  olMap?.setTarget(null)
  olMap = null
})

defineExpose({ refreshMap })
</script>

<style scoped>
.ent-tabs { min-height: 420px; }
.ent-form { padding-top: 8px; }
.mini-map { height: 280px; border: 1px solid #dcdfe6; border-radius: 4px; margin-bottom: 8px; }
.map-tip { font-size: 12px; color: #909399; margin: 0 0 12px; }
.breed-bar { margin-bottom: 12px; display: flex; gap: 8px; }
.media-block { width: 100%; }
.hint { font-size: 12px; color: #909399; margin: 6px 0 0; }
</style>
