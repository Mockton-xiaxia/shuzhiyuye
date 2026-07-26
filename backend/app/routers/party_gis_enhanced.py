"""
party.py 路由增强：添加完整的GIS空间功能
对齐现网 regionGisMap / gisMap 的真实交互
"""
from __future__ import annotations

import json
from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.common.response import ApiError, ok
from app.db import get_db
from app.deps import CurrentUser, get_current_user
from app.models import BizEnterprise, BizPond, SysTodo
from app.utils.geometry import GeometryUtils, BoundingBox

router = APIRouter(prefix="/party", tags=["party-gis"])


class GeometryIn(BaseModel):
    """几何数据输入"""
    geomGeojson: str
    layerType: str = "AQUACULTURE"


class PondIn(BaseModel):
    """塘口输入"""
    name: str
    code: Optional[str] = None
    pondType: Optional[str] = None
    areaMu: Optional[float] = None
    species: Optional[str] = None
    township: Optional[str] = None
    lng: Optional[float] = None
    lat: Optional[float] = None
    geomGeojson: Optional[str] = None
    layerType: str = "AQUACULTURE"
    enterpriseId: Optional[int] = None


class AuditIn(BaseModel):
    """审核输入"""
    approved: bool
    opinion: Optional[str] = None


# === 新增：空间校验接口 ===

@router.post("/ponds/validate-geometry")
def validate_geometry(body: GeometryIn, cu: CurrentUser = Depends(get_current_user)):
    """
    几何校验
    对齐现网：绘制完成后的前端校验逻辑
    
    现网交互：
    1. 用户绘制完成多边形
    2. 前端调用此接口校验
    3. 返回面积、中心点、包围盒
    4. 前端提示用户确认
    """
    # 校验几何有效性
    valid, msg = GeometryUtils.validate_polygon(body.geomGeojson)
    if not valid:
        raise ApiError(40000, msg)
    
    # 计算面积
    area = GeometryUtils.calculate_area_mu(body.geomGeojson)
    
    # 计算包围盒
    bbox = GeometryUtils.calculate_bbox(body.geomGeojson)
    
    # 计算中心点
    center = GeometryUtils.calculate_center(body.geomGeojson)
    
    return ok({
        "valid": True,
        "areaMu": area,
        "bbox": {
            "minLng": bbox.min_lng if bbox else None,
            "maxLng": bbox.max_lng if bbox else None,
            "minLat": bbox.min_lat if bbox else None,
            "maxLat": bbox.max_lat if bbox else None
        },
        "center": {
            "lng": center[0] if center else None,
            "lat": center[1] if center else None
        },
        "wkt": GeometryUtils.geojson_to_wkt(body.geomGeojson)
    })


@router.get("/ponds/spatial-query")
def spatial_query(
    bounds: str,  # minLng,maxLng,minLat,maxLat
    layerType: Optional[str] = None,
    auditStatus: Optional[str] = None,
    cu: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    框画查询
    对齐现网：RegionGisStatisticsMap 的自定义框画功能
    
    现网交互：
    1. 用户在地图上绘制矩形或多边形
    2. 前端获取bounds范围
    3. 调用此接口查询范围内的塘口
    4. 返回列表和统计数据
    """
    try:
        min_lng, max_lng, min_lat, max_lat = map(float, bounds.split(','))
    except:
        raise ApiError(40000, "bounds 格式错误，应为：minLng,maxLng,minLat,maxLat")
    
    # 基础查询
    q = select(BizPond).where(BizPond.deleted == 0)
    
    # 权限过滤
    if cu.user.user_type == "ENTERPRISE" and cu.user.enterprise_id:
        q = q.where(BizPond.enterprise_id == cu.user.enterprise_id)
    elif cu.user.project_id:
        q = q.where(BizPond.project_id == cu.user.project_id)
    
    # 空间范围过滤（使用包围盒粗筛）
    q = q.where(
        BizPond.bbox_min_lng >= min_lng,
        BizPond.bbox_max_lng <= max_lng,
        BizPond.bbox_min_lat >= min_lat,
        BizPond.bbox_max_lat <= max_lat
    )
    
    # 图层类型过滤
    if layerType:
        q = q.where(BizPond.layer_type == layerType)
    
    # 审核状态过滤
    if auditStatus:
        q = q.where(BizPond.audit_status == auditStatus)
    
    ponds = db.scalars(q).all()
    
    # 统计计算
    total_area = sum(float(p.area_mu or 0) for p in ponds)
    species_set = set()
    for p in ponds:
        if p.species:
            species_set.update([s.strip() for s in p.species.split(',')])
    
    return ok({
        "ponds": [_pond_dict(p) for p in ponds],
        "summary": {
            "count": len(ponds),
            "totalAreaMu": round(total_area, 2),
            "species": list(species_set),
            "approvedCount": len([p for p in ponds if p.audit_status == "APPROVED"]),
            "pendingCount": len([p for p in ponds if p.audit_status in ("PENDING", "SUBMITTED", "DRAFT")])
        }
    })


@router.post("/ponds/check-overlap")
def check_overlap(
    geojson: str,
    excludeId: Optional[int] = None,
    cu: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    塘口重叠检测
    对齐现网：绘制时实时检测是否与其他塘口重叠
    
    现网交互：
    1. 用户绘制过程中
    2. 前端实时调用此接口
    3. 检测是否与已审核塘口重叠
    4. 返回重叠的塘口列表
    """
    q = select(BizPond).where(
        BizPond.deleted == 0,
        BizPond.audit_status == 'APPROVED'
    )
    if excludeId:
        q = q.where(BizPond.id != excludeId)
    
    existing_ponds = db.scalars(q).all()
    
    overlapping = []
    for pond in existing_ponds:
        if pond.geom_geojson:
            # 简化版：检查包围盒是否相交
            bbox1 = GeometryUtils.calculate_bbox(geojson)
            bbox2 = GeometryUtils.calculate_bbox(pond.geom_geojson)
            
            if bbox1 and bbox2:
                # 包围盒相交检测
                if not (bbox1.max_lng < bbox2.min_lng or bbox2.max_lng < bbox1.min_lng):
                    if not (bbox1.max_lat < bbox2.min_lat or bbox2.max_lat < bbox1.min_lat):
                        overlapping.append({
                            "id": pond.id,
                            "name": pond.name,
                            "enterpriseId": pond.enterprise_id,
                            "layerType": pond.layer_type
                        })
    
    return ok({
        "hasOverlap": len(overlapping) > 0,
        "overlappingPonds": overlapping,
        "message": f"发现 {len(overlapping)} 个重叠塘口" if overlapping else "无重叠"
    })


# === 原有功能增强 ===

@router.get("/gis/layers")
def get_gis_layers(
    mode: str = "collect",  # collect / audit / stats
    keyword: Optional[str] = None,
    cu: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    GIS 图层数据
    对齐现网：塘口信息采集页左侧列表 + 地图图层
    
    现网交互：
    - mode='collect': 采集模式（企业侧）
    - mode='audit': 审核模式（区县侧）
    - mode='stats': 统计模式（框画查询）
    """
    q = select(BizPond).where(BizPond.deleted == 0)
    
    # 权限过滤
    if cu.user.user_type == "ENTERPRISE" and cu.user.enterprise_id:
        q = q.where(BizPond.enterprise_id == cu.user.enterprise_id)
    elif cu.user.project_id:
        q = q.where(BizPond.project_id == cu.user.project_id)
    
    # 关键词搜索
    if keyword:
        q = q.where(BizPond.name.contains(keyword))
    
    ponds = db.scalars(q.order_by(BizPond.id.desc())).all()
    
    # 统计数据（对齐现网信息汇总）
    approved_count = len([p for p in ponds if p.audit_status == "APPROVED"])
    pending_count = len([p for p in ponds if p.audit_status in ("PENDING", "SUBMITTED", "DRAFT")])
    total_area = sum(float(p.area_mu or 0) for p in ponds if p.audit_status == "APPROVED")
    species_list = []
    for p in ponds:
        if p.species:
            species_list.extend([s.strip() for s in p.species.split(',')])
    
    return ok({
        "ponds": [_pond_dict(p) for p in ponds],
        "summary": {
            "approvedCount": approved_count,
            "pendingCount": pending_count,
            "drawnCount": len(ponds),  # 已画塘口数
            "areaMu": round(total_area, 2),
            "species": list(set(species_list))
        }
    })


def _pond_dict(p: BizPond) -> dict:
    """塘口字典，对齐现网字段"""
    return {
        "id": p.id,
        "name": p.name,
        "code": p.code,
        "enterpriseId": p.enterprise_id,
        "pondType": p.pond_type,
        "areaMu": float(p.area_mu or 0),
        "areaMuCalc": float(p.area_mu_calc or 0) if p.area_mu_calc else None,
        "species": p.species,
        "township": p.township,
        "lng": p.lng,
        "lat": p.lat,
        "centerLng": p.center_lng,
        "centerLat": p.center_lat,
        "geomGeojson": p.geom_geojson,
        "layerType": p.layer_type,
        "auditStatus": p.audit_status,
        "auditOpinion": p.audit_opinion,
        "geomVersion": p.geom_version,
    }


# === 原有的 CRUD 接口 ===

# ... (保持原有的接口不变，这里省略以节省空间)
