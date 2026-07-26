"""
尾水监管 GIS 功能
对齐现网：尾水区绘制、出水口打点、空间关联
"""
from __future__ import annotations

import json
from typing import Optional, List

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.common.response import ApiError, ok
from app.db import get_db
from app.deps import CurrentUser, get_current_user
from app.models import BizEnterprise, BizPond, EfFacility, EfDischargePlan
from app.utils.geometry import GeometryUtils

router = APIRouter(prefix="/effluent", tags=["effluent-gis"])


class FacilityIn(BaseModel):
    """尾水设施输入"""
    name: str
    facilityType: str  # EFFLUENT / OUTLET
    geomGeojson: str
    enterpriseId: int
    status: str = "ACTIVE"


@router.get("/facilities/geojson")
def get_facilities_geojson(
    enterpriseId: Optional[int] = None,
    facilityType: Optional[str] = None,
    cu: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取尾水设施 GeoJSON
    对齐现网：尾水监管地图图层
    
    现网交互：
    1. 地图加载时调用
    2. 获取所有尾水区和出水口
    3. 在地图上展示不同颜色的图层
    """
    q = select(EfFacility).where(EfFacility.deleted == 0)
    
    # 权限过滤
    if cu.user.user_type == "ENTERPRISE" and cu.user.enterprise_id:
        q = q.where(EfFacility.enterprise_id == cu.user.enterprise_id)
    elif cu.user.project_id:
        q = q.where(EfFacility.project_id == cu.user.project_id)
    
    if enterpriseId:
        q = q.where(EfFacility.enterprise_id == enterpriseId)
    
    if facilityType:
        q = q.where(EfFacility.facility_type == facilityType)
    
    facilities = db.scalars(q).all()
    
    # 构建 GeoJSON FeatureCollection
    features = []
    for f in facilities:
        if f.geom_geojson:
            feature = {
                "type": "Feature",
                "id": f.id,
                "geometry": json.loads(f.geom_geojson),
                "properties": {
                    "name": f.name,
                    "type": f.facility_type,
                    "enterpriseId": f.enterprise_id,
                    "status": f.status,
                    "areaMu": float(f.area_mu or 0) if f.area_mu else None
                }
            }
            features.append(feature)
    
    return ok({
        "type": "FeatureCollection",
        "features": features,
        "summary": {
            "count": len(features),
            "effluentCount": len([f for f in facilities if f.facility_type == "EFFLUENT"]),
            "outletCount": len([f for f in facilities if f.facility_type == "OUTLET"])
        }
    })


@router.post("/facilities")
def create_facility(
    body: FacilityIn,
    cu: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    创建尾水设施
    对齐现网：尾水区测绘、出水口打点
    
    现网交互：
    1. 用户在地图上绘制多边形或点
    2. 前端校验几何
    3. 提交到后端保存
    """
    # 校验几何
    if body.facilityType == "EFFLUENT":
        # 尾水区必须是多边形
        valid, msg = GeometryUtils.validate_polygon(body.geomGeojson)
        if not valid:
            raise ApiError(40000, f"尾水区几何校验失败：{msg}")
        
        # 计算面积
        area = GeometryUtils.calculate_area_mu(body.geomGeojson)
        center = GeometryUtils.calculate_center(body.geomGeojson)
        bbox = GeometryUtils.calculate_bbox(body.geomGeojson)
    else:
        # 出水口可以忽略严格校验
        area = None
        center = None
        bbox = None
    
    # 权限检查
    if cu.user.user_type == "ENTERPRISE" and body.enterpriseId != cu.user.enterprise_id:
        raise ApiError(40300, "无权限", 403)
    
    facility = EfFacility(
        project_id=cu.user.project_id or 0,
        enterprise_id=body.enterpriseId,
        name=body.name,
        facility_type=body.facilityType,
        geom_geojson=body.geomGeojson,
        geom_wkt=GeometryUtils.geojson_to_wkt(body.geomGeojson),
        area_mu=area,
        center_lng=center[0] if center else None,
        center_lat=center[1] if center else None,
        status=body.status
    )
    
    db.add(facility)
    db.commit()
    db.refresh(facility)
    
    return ok({
        "id": facility.id,
        "areaMu": area,
        "center": {"lng": center[0], "lat": center[1]} if center else None
    })


@router.get("/facilities/{id}/nearby-ponds")
def get_nearby_ponds(
    id: int,
    radius: float = 500,  # 米
    cu: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    查询附近塘口
    对齐现网：尾水区关联塘口
    
    现网交互：
    1. 用户点击尾水区
    2. 查询附近500米内的塘口
    3. 展示关联关系
    """
    facility = db.get(EfFacility, id)
    if not facility or facility.deleted:
        raise ApiError(40400, "设施不存在", 404)
    
    if not facility.geom_geojson:
        return ok([])
    
    # 获取设施中心点
    center = GeometryUtils.calculate_center(facility.geom_geojson)
    if not center:
        return ok([])
    
    lng, lat = center
    
    # 粗筛：经纬度范围
    delta_deg = radius / 111320.0  # 粗略转换
    
    ponds = db.scalars(
        select(BizPond).where(
            BizPond.deleted == 0,
            BizPond.audit_status == "APPROVED",
            BizPond.center_lng >= lng - delta_deg,
            BizPond.center_lng <= lng + delta_deg,
            BizPond.center_lat >= lat - delta_deg,
            BizPond.center_lat <= lat + delta_deg
        )
    ).all()
    
    # 精确计算距离
    nearby = []
    for p in ponds:
        if p.center_lng and p.center_lat:
            dist = _haversine_distance(lng, lat, p.center_lng, p.center_lat)
            if dist <= radius:
                nearby.append({
                    "id": p.id,
                    "name": p.name,
                    "distance": round(dist, 2),
                    "enterpriseId": p.enterprise_id,
                    "species": p.species,
                    "areaMu": float(p.area_mu or 0)
                })
    
    # 按距离排序
    nearby.sort(key=lambda x: x["distance"])
    
    return ok(nearby)


@router.post("/facilities/{id}/check-outlet")
def check_outlet_in_facility(
    id: int,
    outletGeomJson: str,
    cu: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    检查出水口是否在尾水区内
    对齐现网：出水口打点校验
    
    现网交互：
    1. 用户绘制出水口
    2. 检查是否在对应的尾水区范围内
    3. 不在范围内给出警告
    """
    facility = db.get(EfFacility, id)
    if not facility or facility.deleted:
        raise ApiError(40400, "设施不存在", 404)
    
    if not facility.geom_geojson:
        raise ApiError(40900, "尾水设施无几何数据")
    
    # 解析出水口坐标
    try:
        outlet_geojson = json.loads(outletGeomJson)
        if outlet_geojson.get('type') != 'Point':
            raise ApiError(40000, "出水口必须是 Point 类型")
        
        lng, lat = outlet_geojson['coordinates']
    except Exception as e:
        raise ApiError(40000, f"出水口坐标解析失败：{str(e)}")
    
    # 判断点是否在多边形内
    is_inside = GeometryUtils.point_in_polygon(lng, lat, facility.geom_geojson)
    
    return ok({
        "isInside": is_inside,
        "message": "出水口在尾水区范围内" if is_inside else "警告：出水口不在尾水区范围内"
    })


@router.get("/discharge-plans/map")
def get_discharge_plans_map(
    year: Optional[int] = None,
    month: Optional[int] = None,
    cu: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    排放计划地图展示
    对齐现网：尾水排放计划查看地图
    
    现网交互：
    1. 用户点击排放计划列表
    2. 地图定位到对应企业
    3. 展示尾水区和出水口
    """
    q = select(EfDischargePlan).where(EfDischargePlan.deleted == 0)
    
    if cu.user.user_type == "ENTERPRISE" and cu.user.enterprise_id:
        q = q.where(EfDischargePlan.enterprise_id == cu.user.enterprise_id)
    elif cu.user.project_id:
        q = q.where(EfDischargePlan.project_id == cu.user.project_id)
    
    plans = db.scalars(q).all()
    
    # 构建地图数据
    map_data = []
    enterprises = {e.id: e for e in db.scalars(select(BizEnterprise)).all()}
    
    for p in plans:
        ent = enterprises.get(p.enterprise_id)
        if ent and ent.lng and ent.lat:
            map_data.append({
                "id": p.id,
                "title": p.title,
                "enterpriseId": p.enterprise_id,
                "enterpriseName": ent.name,
                "lng": ent.lng,
                "lat": ent.lat,
                "planMonth": p.plan_month,
                "volume": float(p.volume or 0),
                "status": p.status
            })
    
    return ok(map_data)


def _haversine_distance(lng1: float, lat1: float, lng2: float, lat2: float) -> float:
    """
    计算两点间的距离（米）
    使用 Haversine 公式
    """
    import math
    
    R = 6371000  # 地球半径（米）
    
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lng2 - lng1)
    
    a = math.sin(delta_phi / 2) ** 2 + \
        math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c
