import TileLayer from 'ol/layer/Tile'
import Group from 'ol/layer/Group'
import XYZ from 'ol/source/XYZ'
import OSM from 'ol/source/OSM'
import { TIANDITU_KEY, tiandituTileUrls } from '@/config/map'

function xyz(url, attributions = '© 高德') {
  return new TileLayer({
    source: new XYZ({
      url,
      maxZoom: 18,
      crossOrigin: 'anonymous',
      attributions,
    }),
  })
}

/** 返回可直接塞进 map 的底图 Layer（天地图为 Group：底图+注记） */
export function makeBasemapLayer(kind = 'td-vec') {
  if (kind === 'osm') {
    return new TileLayer({ source: new OSM() })
  }
  if (kind === 'gaode-sat') {
    return xyz('https://webst0{1-4}.is.autonavi.com/appmaptile?style=6&x={x}&y={y}&z={z}')
  }
  if (kind === 'gaode') {
    return xyz(
      'https://webrd0{1-4}.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=8&x={x}&y={y}&z={z}',
    )
  }
  // 天地图矢量 / 影像（含注记）
  if (!TIANDITU_KEY) {
    return xyz(
      'https://webrd0{1-4}.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=8&x={x}&y={y}&z={z}',
    )
  }
  const { base, anno } = tiandituTileUrls(kind === 'td-img' ? 'td-img' : 'td-vec')
  return new Group({
    layers: [
      xyz(base, '© 国家基础地理信息中心 · 天地图'),
      xyz(anno, '© 天地图注记'),
    ],
  })
}

export { TIANDITU_KEY }
