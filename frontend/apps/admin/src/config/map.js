/** 地图底图配置：天地图官方 key 优先走环境变量 */
export const TIANDITU_KEY =
  import.meta.env.VITE_TIANDITU_KEY || '1048484c7368c335a7ee29d833764869'

function tdUrl(layer) {
  return `https://t{0-7}.tianditu.gov.cn/DataServer?T=${layer}&x={x}&y={y}&l={z}&tk=${TIANDITU_KEY}`
}

export const BASEMAP_OPTIONS = [
  { label: '天地图矢量', value: 'td-vec' },
  { label: '天地图影像', value: 'td-img' },
  { label: '高德矢量', value: 'gaode' },
  { label: '高德影像', value: 'gaode-sat' },
  { label: 'OSM', value: 'osm' },
]

export function tiandituTileUrls(kind) {
  if (kind === 'td-img') {
    return { base: tdUrl('img_w'), anno: tdUrl('cia_w') }
  }
  return { base: tdUrl('vec_w'), anno: tdUrl('cva_w') }
}
