"""
GIS 空间工具模块
对齐现网 regionGisMap / gisMap 页面的真实交互
"""
import json
import math
from typing import Optional, Tuple, List
from dataclasses import dataclass


@dataclass
class BoundingBox:
    """包围盒"""
    min_lng: float
    max_lng: float
    min_lat: float
    max_lat: float
