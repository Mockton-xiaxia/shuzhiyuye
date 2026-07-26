/**
 * 前端 GIS 工具
 * 对齐后端 Python 实现
 * 对齐现网：regionGisMap / gisMap 页面的前端校验
 */

/**
 * 计算面积（亩）
 * 对齐后端：GeometryUtils.calculate_area_mu
 * 
 * @param {Object} geojson - GeoJSON Polygon 对象
 * @returns {number} 面积（亩）
 */
export function calculateAreaMu(geojson) {
  if (!geojson || geojson.type !== 'Polygon') return 0
  
  const coords = geojson.coordinates[0]
  let area = 0
  
  // 鞋带公式
  for (let i = 0; i < coords.length; i++) {
    const j = (i + 1) % coords.length
    area += (coords[j][0] - coords[i][0]) * (coords[i][1] + coords[j][1])
  }
  
  // 西湖区纬度约 30°
  const latRad = 30.0 * Math.PI / 180.0
  const metersPerDegLat = 111320.0
  const metersPerDegLng = 111320.0 * Math.cos(latRad)
  
  area = Math.abs(area) * metersPerDegLat * metersPerDegLng / 666.67
  
  return area
}

/**
 * 校验 GeoJSON
 * 对齐后端：GeometryUtils.validate_polygon
 * 
 * @param {Object} geojson - GeoJSON 对象
 * @returns {Object} { valid: boolean, error: string }
 */
export function validateGeoJSON(geojson) {
  if (!geojson || !geojson.type) {
    return { valid: false, error: '缺少 type 字段' }
  }
  
  if (geojson.type === 'Polygon') {
    if (!geojson.coordinates || !geojson.coordinates[0]) {
      return { valid: false, error: '缺少坐标数据' }
    }
    
    const ring = geojson.coordinates[0]
    
    // 现网要求至少4个点（闭合）
    if (ring.length < 4) {
      return { valid: false, error: '多边形至少需要4个点' }
    }
    
    // 检查闭合
    const first = ring[0]
    const last = ring[ring.length - 1]
    if (Math.abs(first[0] - last[0]) > 1e-9 || Math.abs(first[1] - last[1]) > 1e-9) {
      return { valid: false, error: '多边形未闭合' }
    }
    
    // 计算面积
    const area = calculateAreaMu(geojson)
    if (area < 0.1) {
      return { valid: false, error: '绘制面积过小，请重新绘制' }
    }
  } else if (geojson.type === 'Point') {
    if (!geojson.coordinates) {
      return { valid: false, error: '缺少坐标数据' }
    }
  } else {
    return { valid: false, error: '仅支持 Polygon 和 Point 类型' }
  }
  
  return { valid: true, error: '' }
}

/**
 * 计算中心点
 * 
 * @param {Object} geojson - GeoJSON Polygon 对象
 * @returns {Object} { lng, lat }
 */
export function calculateCenter(geojson) {
  if (!geojson || geojson.type !== 'Polygon') return null
  
  const coords = geojson.coordinates[0]
  const lons = coords.map(c => c[0])
  const lats = coords.map(c => c[1])
  
  return {
    lng: (Math.min(...lons) + Math.max(...lons)) / 2,
    lat: (Math.min(...lats) + Math.max(...lats)) / 2
  }
}

/**
 * 计算包围盒
 * 
 * @param {Object} geojson - GeoJSON Polygon 对象
 * @returns {Object} { minLng, maxLng, minLat, maxLat }
 */
export function calculateBBox(geojson) {
  if (!geojson || geojson.type !== 'Polygon') return null
  
  const coords = geojson.coordinates[0]
  const lons = coords.map(c => c[0])
  const lats = coords.map(c => c[1])
  
  return {
    minLng: Math.min(...lons),
    maxLng: Math.max(...lons),
    minLat: Math.min(...lats),
    maxLat: Math.max(...lats)
  }
}

/**
 * Haversine 距离计算
 * 
 * @param {number} lng1 - 起点经度
 * @param {number} lat1 - 起点纬度
 * @param {number} lng2 - 终点经度
 * @param {number} lat2 - 终点纬度
 * @returns {number} 距离（米）
 */
export function haversineDistance(lng1, lat1, lng2, lat2) {
  const R = 6371000 // 地球半径（米）
  
  const phi1 = lat1 * Math.PI / 180
  const phi2 = lat2 * Math.PI / 180
  const deltaPhi = (lat2 - lat1) * Math.PI / 180
  const deltaLambda = (lng2 - lng1) * Math.PI / 180
  
  const a = Math.sin(deltaPhi / 2) ** 2 +
            Math.cos(phi1) * Math.cos(phi2) * Math.sin(deltaLambda / 2) ** 2
  
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a))
  
  return R * c
}

/**
 * 判断点是否在多边形内
 * 
 * @param {number} pointLng - 点经度
 * @param {number} pointLat - 点纬度
 * @param {Object} geojson - GeoJSON Polygon 对象
 * @returns {boolean} 是否在多边形内
 */
export function pointInPolygon(pointLng, pointLat, geojson) {
  if (!geojson || geojson.type !== 'Polygon') return false
  
  const coords = geojson.coordinates[0]
  const n = coords.length
  let inside = false
  
  let j = n - 1
  for (let i = 0; i < n; i++) {
    const xi = coords[i][0]
    const yi = coords[i][1]
    const xj = coords[j][0]
    const yj = coords[j][1]
    
    if ((yi > pointLat) !== (yj > pointLat) &&
        pointLng < (xj - xi) * (pointLat - yi) / (yj - yi) + xi) {
      inside = !inside
    }
    
    j = i
  }
  
  return inside
}

/**
 * 坐标系转换：GCJ-02 转 WGS-84
 * 对齐后端：CoordinateTransform.gcj02_to_wgs84
 * 
 * @param {number} lng - GCJ-02 经度
 * @param {number} lat - GCJ-02 纬度
 * @returns {Object} { lng, lat } WGS-84 坐标
 */
export function gcj02ToWgs84(lng, lat) {
  const PI = 3.1415926535897932384626
  const A = 6378245.0
  const EE = 0.00669342162296594323
  
  if (outOfChina(lng, lat)) {
    return { lng, lat }
  }
  
  let dlat = transformLat(lng - 105.0, lat - 35.0)
  let dlon = transformLon(lng - 105.0, lat - 35.0)
  
  const radlat = lat / 180.0 * PI
  let magic = Math.sin(radlat)
  magic = 1 - EE * magic * magic
  const sqrtmagic = Math.sqrt(magic)
  
  dlat = (dlat * 180.0) / ((A * (1 - EE)) / (magic * sqrtmagic) * PI)
  dlon = (dlon * 180.0) / (A / sqrtmagic * Math.cos(radlat) * PI)
  
  const mglat = lat + dlat
  const mglon = lng + dlon
  
  return {
    lng: lng * 2 - mglon,
    lat: lat * 2 - mglat
  }
}

/**
 * 坐标系转换：WGS-84 转 GCJ-02
 * 
 * @param {number} lng - WGS-84 经度
 * @param {number} lat - WGS-84 纬度
 * @returns {Object} { lng, lat } GCJ-02 坐标
 */
export function wgs84ToGcj02(lng, lat) {
  const PI = 3.1415926535897932384626
  const A = 6378245.0
  const EE = 0.00669342162296594323
  
  if (outOfChina(lng, lat)) {
    return { lng, lat }
  }
  
  let dlat = transformLat(lng - 105.0, lat - 35.0)
  let dlon = transformLon(lng - 105.0, lat - 35.0)
  
  const radlat = lat / 180.0 * PI
  let magic = Math.sin(radlat)
  magic = 1 - EE * magic * magic
  const sqrtmagic = Math.sqrt(magic)
  
  dlat = (dlat * 180.0) / ((A * (1 - EE)) / (magic * sqrtmagic) * PI)
  dlon = (dlon * 180.0) / (A / sqrtmagic * Math.cos(radlat) * PI)
  
  return {
    lng: lng + dlon,
    lat: lat + dlat
  }
}

// 辅助函数
function transformLat(x, y) {
  const PI = 3.1415926535897932384626
  let ret = -100.0 + 2.0 * x + 3.0 * y + 0.2 * y * y + 0.1 * x * y + 0.2 * Math.sqrt(Math.abs(x))
  ret += (20.0 * Math.sin(6.0 * x * PI) + 20.0 * Math.sin(2.0 * x * PI)) * 2.0 / 3.0
  ret += (20.0 * Math.sin(y * PI) + 40.0 * Math.sin(y / 3.0 * PI)) * 2.0 / 3.0
  ret += (160.0 * Math.sin(y / 12.0 * PI) + 320 * Math.sin(y * PI / 30.0)) * 2.0 / 3.0
  return ret
}

function transformLon(x, y) {
  const PI = 3.1415926535897932384626
  let ret = 300.0 + x + 2.0 * y + 0.1 * x * x + 0.1 * x * y + 0.1 * Math.sqrt(Math.abs(x))
  ret += (20.0 * Math.sin(6.0 * x * PI) + 20.0 * Math.sin(2.0 * x * PI)) * 2.0 / 3.0
  ret += (20.0 * Math.sin(x * PI) + 40.0 * Math.sin(x / 3.0 * PI)) * 2.0 / 3.0
  ret += (150.0 * Math.sin(x / 12.0 * PI) + 300.0 * Math.sin(x / 30.0 * PI)) * 2.0 / 3.0
  return ret
}

function outOfChina(lng, lat) {
  if (lng < 72.004 || lng > 137.8347) return true
  if (lat < 0.8293 || lat > 55.8271) return true
  return false
}

export default {
  calculateAreaMu,
  validateGeoJSON,
  calculateCenter,
  calculateBBox,
  haversineDistance,
  pointInPolygon,
  gcj02ToWgs84,
  wgs84ToGcj02
}
