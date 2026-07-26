"""
坐标系转换工具

对齐现网：
- 天地图：CGCS2000（接近 WGS84）
- 高德：GCJ-02（火星坐标）
- 前端：WGS84
"""
import math
from typing import Tuple


class CoordinateTransform:
    """
    坐标系转换
    
    现网实测：
    - 天地图坐标与 WGS84 偏差 < 1米
    - 高德坐标与 WGS84 偏差约 50-100米
    """
    
    X_PI = 3.14159265358979324 * 3000.0 / 180.0
    PI = 3.1415926535897932384626
    A = 6378245.0  # 长半轴
    EE = 0.00669342162296594323  # 扁率
    
    @staticmethod
    def gcj02_to_wgs84(lng: float, lat: float) -> Tuple[float, float]:
        """
        GCJ-02 转 WGS-84
        
        Args:
            lng: GCJ-02 经度
            lat: GCJ-02 纬度
        
        Returns:
            (WGS84经度, WGS84纬度)
        """
        if CoordinateTransform._out_of_china(lng, lat):
            return lng, lat
        
        dlat = CoordinateTransform._transform_lat(lng - 105.0, lat - 35.0)
        dlon = CoordinateTransform._transform_lon(lng - 105.0, lat - 35.0)
        
        radlat = lat / 180.0 * CoordinateTransform.PI
        magic = math.sin(radlat)
        magic = 1 - CoordinateTransform.EE * magic * magic
        sqrtmagic = math.sqrt(magic)
        
        dlat = (dlat * 180.0) / ((CoordinateTransform.A * (1 - CoordinateTransform.EE)) / (magic * sqrtmagic) * CoordinateTransform.PI)
        dlon = (dlon * 180.0) / (CoordinateTransform.A / sqrtmagic * math.cos(radlat) * CoordinateTransform.PI)
        
        mglat = lat + dlat
        mglon = lng + dlon
        
        return lng * 2 - mglon, lat * 2 - mglat
    
    @staticmethod
    def wgs84_to_gcj02(lng: float, lat: float) -> Tuple[float, float]:
        """WGS-84 转 GCJ-02"""
        if CoordinateTransform._out_of_china(lng, lat):
            return lng, lat
        
        dlat = CoordinateTransform._transform_lat(lng - 105.0, lat - 35.0)
        dlon = CoordinateTransform._transform_lon(lng - 105.0, lat - 35.0)
        
        radlat = lat / 180.0 * CoordinateTransform.PI
        magic = math.sin(radlat)
        magic = 1 - CoordinateTransform.EE * magic * magic
        sqrtmagic = math.sqrt(magic)
        
        dlat = (dlat * 180.0) / ((CoordinateTransform.A * (1 - CoordinateTransform.EE)) / (magic * sqrtmagic) * CoordinateTransform.PI)
        dlon = (dlon * 180.0) / (CoordinateTransform.A / sqrtmagic * math.cos(radlat) * CoordinateTransform.PI)
        
        mglat = lat + dlat
        mglon = lng + dlon
        
        return mglon, mglat
    
    @staticmethod
    def _transform_lat(x: float, y: float) -> float:
        ret = -100.0 + 2.0 * x + 3.0 * y + 0.2 * y * y + 0.1 * x * y + 0.2 * math.sqrt(abs(x))
        ret += (20.0 * math.sin(6.0 * x * CoordinateTransform.PI) + 20.0 * math.sin(2.0 * x * CoordinateTransform.PI)) * 2.0 / 3.0
        ret += (20.0 * math.sin(y * CoordinateTransform.PI) + 40.0 * math.sin(y / 3.0 * CoordinateTransform.PI)) * 2.0 / 3.0
        ret += (160.0 * math.sin(y / 12.0 * CoordinateTransform.PI) + 320 * math.sin(y * CoordinateTransform.PI / 30.0)) * 2.0 / 3.0
        return ret
    
    @staticmethod
    def _transform_lon(x: float, y: float) -> float:
        ret = 300.0 + x + 2.0 * y + 0.1 * x * x + 0.1 * x * y + 0.1 * math.sqrt(abs(x))
        ret += (20.0 * math.sin(6.0 * x * CoordinateTransform.PI) + 20.0 * math.sin(2.0 * x * CoordinateTransform.PI)) * 2.0 / 3.0
        ret += (20.0 * math.sin(x * CoordinateTransform.PI) + 40.0 * math.sin(x / 3.0 * CoordinateTransform.PI)) * 2.0 / 3.0
        ret += (150.0 * math.sin(x / 12.0 * CoordinateTransform.PI) + 300.0 * math.sin(x / 30.0 * CoordinateTransform.PI)) * 2.0 / 3.0
        return ret
    
    @staticmethod
    def _out_of_china(lng: float, lat: float) -> bool:
        """判断是否在中国境外"""
        if lng < 72.004 or lng > 137.8347:
            return True
        if lat < 0.8293 or lat > 55.8271:
            return True
        return False
