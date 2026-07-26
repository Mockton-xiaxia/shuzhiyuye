from __future__ import annotations

import csv
import io
import json
from typing import Any, Optional

from pathlib import Path

from fastapi import APIRouter, Depends, Query, UploadFile, File
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, Field
from app.common.coerce import OptionalLooseStr
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.common.response import ApiError, ok
from app.db import get_db
from app.deps import CurrentUser, get_current_user
from app.models import BizEnterprise, BizInfoSubmit, BizPond, BizStaff, SysProject, SysRegion, SysTodo

# 导入GIS工具
try:
    from app.utils.geometry import GeometryUtils
    GIS_UTILS_AVAILABLE = True
except ImportError:
    GIS_UTILS_AVAILABLE = False

router = APIRouter(prefix="/party", tags=["party-gis"])
TEMPLATE_DIR = Path(__file__).resolve().parents[1] / "data" / "templates"


class BreedingItemIn(BaseModel):
    species: str = ""
    ratio: Optional[float] = None
    outSpec: Optional[str] = None
    yieldPerMu: Optional[float] = None
    outMonth: Optional[str] = None


class EnterpriseIn(BaseModel):
    name: str
    code: Optional[str] = None
    subjectType: Optional[str] = None
    regionId: Optional[int] = None
    regionPath: Optional[list[str]] = None
    regionPathLabel: Optional[str] = None
    contactName: Optional[str] = None
    contactPhone: OptionalLooseStr = None
    address: Optional[str] = None
    lng: Optional[float] = None
    lat: Optional[float] = None
    areaMu: Optional[float] = None
    species: Optional[str] = None
    speciesList: Optional[list[str]] = None
    intro: Optional[str] = None
    parentEnterpriseId: Optional[int] = None
    annualOutputTon: Optional[float] = None
    breedingMode: Optional[str] = None
    idCard: OptionalLooseStr = None
    fisheryQualification: Optional[str] = None
    breedingItems: Optional[list[BreedingItemIn]] = None
    promoImages: Optional[list[str]] = None
    promoVideos: Optional[list[str]] = None
    showOnScreen: Optional[bool] = None
    selfCheckFiles: Optional[list[str]] = None
    status: Optional[str] = None


class EnterpriseBatchDeleteIn(BaseModel):
    ids: list[int] = Field(default_factory=list)


class PondIn(BaseModel):
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
    approved: bool
    opinion: Optional[str] = None


class GeometryIn(BaseModel):
    geomGeojson: str
    layerType: str = "AQUACULTURE"


def _ent_filter(q, cu: CurrentUser):
    if cu.user.user_type == "ENTERPRISE" and cu.user.enterprise_id:
        return q.where(BizEnterprise.id == cu.user.enterprise_id)
    if cu.user.project_id:
        return q.where(BizEnterprise.project_id == cu.user.project_id)
    return q


def _parse_extra(raw: Optional[str]) -> dict:
    if not raw:
        return {}
    try:
        data = json.loads(raw)
        return data if isinstance(data, dict) else {}
    except json.JSONDecodeError:
        return {}


def _merge_extra(e: BizEnterprise, body: EnterpriseIn) -> None:
    extra = _parse_extra(e.extra_json)
    mapping = {
        "parentEnterpriseId": body.parentEnterpriseId,
        "annualOutputTon": body.annualOutputTon,
        "breedingMode": body.breedingMode,
        "idCard": body.idCard,
        "regionPath": body.regionPath,
        "regionPathLabel": body.regionPathLabel,
        "speciesList": body.speciesList,
        "fisheryQualification": body.fisheryQualification,
        "showOnScreen": body.showOnScreen,
    }
    for k, v in mapping.items():
        if v is not None:
            extra[k] = v
    if body.breedingItems is not None:
        extra["breedingItems"] = [x.model_dump() for x in body.breedingItems]
    if body.promoImages is not None:
        extra["promoImages"] = body.promoImages
    if body.promoVideos is not None:
        extra["promoVideos"] = body.promoVideos
    if body.selfCheckFiles is not None:
        extra["selfCheckFiles"] = body.selfCheckFiles
    e.extra_json = json.dumps(extra, ensure_ascii=False)


def _subject_type_label(v: Optional[str]) -> str:
    return {
        "INDIVIDUAL": "养殖个体户",
        "ENTERPRISE": "养殖企业",
        "PARK": "养殖园区",
    }.get(v or "", v or "养殖企业")


def _enterprise_dict(e: BizEnterprise, db: Session, brief: bool = False) -> dict:
    extra = _parse_extra(e.extra_json)
    region_name = "示范县"
    if e.region_id:
        r = db.get(SysRegion, e.region_id)
        if r:
            region_name = r.name
    project_name = "绿色循环渔业试点项目"
    if e.project_id:
        p = db.get(SysProject, e.project_id)
        if p:
            project_name = p.name
    parent_name = ""
    pid = extra.get("parentEnterpriseId")
    if pid:
        pe = db.get(BizEnterprise, pid)
        if pe and not pe.deleted:
            parent_name = pe.name
    species = e.species or ""
    species_list = extra.get("speciesList") or []
    if not species and species_list:
        species = "、".join(species_list) if isinstance(species_list[0], str) else species
    base = {
        "id": e.id,
        "name": e.name,
        "code": e.code,
        "contactName": e.contact_name,
        "contactPhone": e.contact_phone,
        "address": e.address,
        "lng": e.lng,
        "lat": e.lat,
        "areaMu": float(e.area_mu or 0),
        "species": species,
        "status": e.status,
        "projectId": e.project_id,
        "regionId": e.region_id,
        "subjectType": _subject_type_label(e.subject_type),
        "subjectTypeCode": e.subject_type or "ENTERPRISE",
        "regionName": extra.get("regionPathLabel") or region_name,
        "projectName": project_name,
    }
    if brief:
        return base
    return {
        **base,
        "intro": e.intro,
        "parentEnterpriseId": extra.get("parentEnterpriseId"),
        "parentEnterpriseName": parent_name,
        "annualOutputTon": extra.get("annualOutputTon"),
        "breedingMode": extra.get("breedingMode"),
        "idCard": extra.get("idCard"),
        "regionPath": extra.get("regionPath") or [],
        "regionPathLabel": extra.get("regionPathLabel") or region_name,
        "speciesList": species_list,
        "breedingItems": extra.get("breedingItems") or [],
        "fisheryQualification": extra.get("fisheryQualification"),
        "promoImages": extra.get("promoImages") or [],
        "promoVideos": extra.get("promoVideos") or [],
        "showOnScreen": bool(extra.get("showOnScreen", False)),
        "selfCheckFiles": extra.get("selfCheckFiles") or [],
    }


def _apply_enterprise(e: BizEnterprise, body: EnterpriseIn) -> None:
    e.name = body.name
    if body.code is not None:
        e.code = body.code
    if body.subjectType is not None:
        e.subject_type = body.subjectType
    if body.regionId is not None:
        e.region_id = body.regionId
    e.contact_name = body.contactName
    e.contact_phone = body.contactPhone
    e.address = body.address
    e.lng = body.lng
    e.lat = body.lat
    e.area_mu = body.areaMu
    if body.speciesList:
        e.species = "、".join(body.speciesList)
    elif body.species is not None:
        e.species = body.species
    e.intro = body.intro
    if body.status is not None:
        e.status = body.status
    _merge_extra(e, body)


# === 新增：GIS 空间功能接口 ===

@router.post("/ponds/validate-geometry")
def validate_geometry(body: GeometryIn, cu: CurrentUser = Depends(get_current_user)):
    """
    几何校验接口
    对齐现网：绘制完成后的前端校验
    """
    if not GIS_UTILS_AVAILABLE:
        return ok({"valid": True, "message": "GIS工具未加载，跳过校验"})
    
    # 校验几何
    valid, msg = GeometryUtils.validate_polygon(body.geomGeojson)
    if not valid:
        raise ApiError(40000, msg)
    
    # 计算面积
    area = GeometryUtils.calculate_area_mu(body.geomGeojson)
    
    # 计算中心点
    center = GeometryUtils.calculate_center(body.geomGeojson)
    
    # 计算包围盒
    bbox = GeometryUtils.calculate_bbox(body.geomGeojson)
    
    return ok({
        "valid": True,
        "areaMu": area,
        "center": {"lng": center[0], "lat": center[1]} if center else None,
        "bbox": {
            "minLng": bbox.min_lng,
            "maxLng": bbox.max_lng,
            "minLat": bbox.min_lat,
            "maxLat": bbox.max_lat
        } if bbox else None
    })


@router.get("/ponds/spatial-query")
def spatial_query(
    bounds: str,  # minLng,maxLng,minLat,maxLat
    layerType: Optional[str] = None,
    cu: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    框画查询接口
    对齐现网：RegionGisStatisticsMap 的自定义框画
    """
    try:
        min_lng, max_lng, min_lat, max_lat = map(float, bounds.split(','))
    except:
        raise ApiError(40000, "bounds 格式错误")
    
    q = select(BizPond).where(BizPond.deleted == 0)
    
    # 权限过滤
    if cu.user.user_type == "ENTERPRISE" and cu.user.enterprise_id:
        q = q.where(BizPond.enterprise_id == cu.user.enterprise_id)
    elif cu.user.project_id:
        q = q.where(BizPond.project_id == cu.user.project_id)
    
    # 空间范围过滤（使用经纬度粗筛）
    q = q.where(
        BizPond.lng >= min_lng,
        BizPond.lng <= max_lng,
        BizPond.lat >= min_lat,
        BizPond.lat <= max_lat
    )
    
    if layerType:
        q = q.where(BizPond.layer_type == layerType)
    
    ponds = db.scalars(q).all()
    
    # 统计
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
            "species": list(species_set)
        }
    })


# === 原有接口（保持不变）===

@router.get("/enterprises")
def list_enterprises(
    page: int = 1,
    size: int = 20,
    keyword: Optional[str] = None,
    subjectType: Optional[str] = None,
    regionName: Optional[str] = None,
    species: Optional[str] = None,
    cu: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = select(BizEnterprise).where(BizEnterprise.deleted == 0)
    q = _ent_filter(q, cu)
    if keyword:
        q = q.where(BizEnterprise.name.contains(keyword))
    if subjectType:
        q = q.where(BizEnterprise.subject_type == subjectType)
    if species:
        q = q.where(BizEnterprise.species.contains(species))
    rows_all = db.scalars(q.order_by(BizEnterprise.id.desc())).all()
    if regionName:
        rows_all = [e for e in rows_all if regionName in (_enterprise_dict(e, db, brief=True).get("regionName") or "")]
    total = len(rows_all)
    rows = rows_all[(page - 1) * size : page * size]
    return ok(
        {
            "list": [_enterprise_dict(e, db, brief=True) for e in rows],
            "page": page,
            "size": size,
            "total": total,
        }
    )


@router.post("/enterprises")
def create_enterprise(body: EnterpriseIn, cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    if cu.user.user_type == "ENTERPRISE":
        raise ApiError(40300, "企业用户不可新建主体", 403)
    e = BizEnterprise(
        project_id=cu.user.project_id or 1,
        region_id=body.regionId or cu.user.region_id,
        name=body.name,
        status=body.status or "APPROVED",
    )
    _apply_enterprise(e, body)
    db.add(e)
    db.commit()
    db.refresh(e)
    return ok(_enterprise_dict(e, db))


@router.get("/enterprises/{eid}")
def get_enterprise(eid: int, cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    e = db.get(BizEnterprise, eid)
    if not e or e.deleted:
        raise ApiError(40400, "主体不存在", 404)
    if cu.user.user_type == "ENTERPRISE" and cu.user.enterprise_id != eid:
        raise ApiError(40300, "无权限", 403)
    return ok(_enterprise_dict(e, db))


@router.put("/enterprises/{eid}")
def update_enterprise(
    eid: int, body: EnterpriseIn, cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)
):
    e = db.get(BizEnterprise, eid)
    if not e or e.deleted:
        raise ApiError(40400, "主体不存在", 404)
    if cu.user.user_type == "ENTERPRISE" and cu.user.enterprise_id != eid:
        raise ApiError(40300, "无权限", 403)
    _apply_enterprise(e, body)
    db.commit()
    return ok(_enterprise_dict(e, db))


@router.delete("/enterprises/{eid}")
def delete_enterprise(eid: int, cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    if cu.user.user_type == "ENTERPRISE":
        raise ApiError(40300, "无权限", 403)
    e = db.get(BizEnterprise, eid)
    if not e or e.deleted:
        raise ApiError(40400, "主体不存在", 404)
    e.deleted = 1
    db.commit()
    return ok(True)


@router.post("/enterprises/batch-delete")
def batch_delete_enterprises(
    body: EnterpriseBatchDeleteIn, cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)
):
    if cu.user.user_type == "ENTERPRISE":
        raise ApiError(40300, "无权限", 403)
    if not body.ids:
        return ok({"count": 0})
    rows = db.scalars(select(BizEnterprise).where(BizEnterprise.id.in_(body.ids), BizEnterprise.deleted == 0)).all()
    for e in rows:
        e.deleted = 1
    db.commit()
    return ok({"count": len(rows)})


@router.get("/enterprises-export")
def export_enterprises(cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    q = select(BizEnterprise).where(BizEnterprise.deleted == 0)
    q = _ent_filter(q, cu)
    rows = db.scalars(q.order_by(BizEnterprise.id.desc())).all()
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["名称", "主体类型", "所属区域", "养殖面积(亩)", "品种", "联系人", "电话", "地址"])
    for e in rows:
        d = _enterprise_dict(e, db, brief=True)
        w.writerow(
            [
                d["name"],
                d["subjectType"],
                d["regionName"],
                d["areaMu"],
                d["species"],
                d["contactName"],
                d["contactPhone"],
                d["address"],
            ]
        )
    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue().encode("utf-8-sig")]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=enterprises.csv"},
    )


@router.post("/enterprises-import")
async def import_enterprises(
    file: UploadFile = File(...),
    cu: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if cu.user.user_type == "ENTERPRISE":
        raise ApiError(40300, "无权限", 403)
    raw = (await file.read()).decode("utf-8-sig", errors="ignore")
    reader = csv.DictReader(io.StringIO(raw))
    count = 0
    for row in reader:
        name = (row.get("名称") or row.get("name") or "").strip()
        if not name:
            continue
        e = BizEnterprise(
            project_id=cu.user.project_id or 1,
            region_id=cu.user.region_id,
            name=name,
            subject_type={"养殖个体户": "INDIVIDUAL", "养殖企业": "ENTERPRISE", "养殖园区": "PARK"}.get(
                (row.get("主体类型") or row.get("subjectType") or "").strip(), "ENTERPRISE"
            ),
            area_mu=float(row.get("养殖面积(亩)") or row.get("areaMu") or 0) or None,
            species=(row.get("品种") or row.get("species") or "").strip() or None,
            contact_name=(row.get("联系人") or row.get("contactName") or "").strip() or None,
            contact_phone=(row.get("电话") or row.get("contactPhone") or "").strip() or None,
            address=(row.get("地址") or row.get("address") or "").strip() or None,
            status="APPROVED",
        )
        db.add(e)
        count += 1
    db.commit()
    return ok({"count": count})


@router.get("/enterprises-import-template")
def enterprises_import_template(cu: CurrentUser = Depends(get_current_user)):
    """养殖主体 CSV 导入模板（含表头与示例行）。"""
    path = TEMPLATE_DIR / "enterprises_import.csv"
    if not path.is_file():
        buf = io.StringIO()
        w = csv.writer(buf)
        w.writerow(["名称", "主体类型", "所属区域", "养殖面积(亩)", "品种", "联系人", "电话", "地址"])
        w.writerow(["周建华", "养殖个体户", "陕西省,示范市,示范县,圣水镇", "35", "鲫、鲤、鲢、草鱼", "周建华", "13800000001", "示范县圣水镇王营村"])
        buf.seek(0)
        return StreamingResponse(
            iter([buf.getvalue().encode("utf-8-sig")]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=enterprises_import_template.csv"},
        )
    return FileResponse(path, media_type="text/csv", filename="enterprises_import_template.csv")


@router.get("/ponds/geojson-template")
def ponds_geojson_template(cu: CurrentUser = Depends(get_current_user)):
    """塘口 GeoJSON 导入模板（FeatureCollection 示例）。"""
    path = TEMPLATE_DIR / "pond_import.geojson"
    if not path.is_file():
        sample = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {"name": "示例养殖区", "layerType": "AQUACULTURE", "species": "草鱼"},
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [[[120.150, 30.243], [120.152, 30.243], [120.152, 30.245], [120.150, 30.245], [120.150, 30.243]]],
                    },
                }
            ],
        }
        return StreamingResponse(
            iter([json.dumps(sample, ensure_ascii=False, indent=2).encode("utf-8")]),
            media_type="application/geo+json",
            headers={"Content-Disposition": "attachment; filename=pond_import_template.geojson"},
        )
    return FileResponse(path, media_type="application/geo+json", filename="pond_import_template.geojson")


@router.get("/regions/tree")
def region_tree(cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.scalars(select(SysRegion).where(SysRegion.deleted == 0).order_by(SysRegion.sort_no, SysRegion.id)).all()
    if not rows:
        return ok([])
    by_parent: dict[int, list[SysRegion]] = {}
    for r in rows:
        by_parent.setdefault(r.parent_id or 0, []).append(r)

    def build(pid: int) -> list[dict]:
        out = []
        for r in by_parent.get(pid, []):
            out.append({"value": r.code, "label": r.name, "id": r.id, "children": build(r.id)})
        return out

    return ok(build(0))


def _pond_dict(p: BizPond) -> dict:
    return {
        "id": p.id,
        "name": p.name,
        "code": p.code,
        "enterpriseId": p.enterprise_id,
        "pondType": p.pond_type,
        "areaMu": float(p.area_mu or 0),
        "species": p.species,
        "township": p.township,
        "lng": p.lng,
        "lat": p.lat,
        "geomGeojson": p.geom_geojson,
        "layerType": p.layer_type,
        "auditStatus": p.audit_status,
        "auditOpinion": p.audit_opinion,
        "enterpriseName": "示范养殖场",
    }


@router.get("/ponds")
def list_ponds(
    auditStatus: Optional[str] = None,
    page: int = 1,
    size: int = 20,
    cu: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = select(BizPond).where(BizPond.deleted == 0)
    if cu.user.user_type == "ENTERPRISE" and cu.user.enterprise_id:
        q = q.where(BizPond.enterprise_id == cu.user.enterprise_id)
    elif cu.user.project_id:
        q = q.where(BizPond.project_id == cu.user.project_id)
    if auditStatus:
        q = q.where(BizPond.audit_status == auditStatus)
    total = db.scalar(select(func.count()).select_from(q.subquery())) or 0
    rows = db.scalars(q.order_by(BizPond.id.desc()).offset((page - 1) * size).limit(size)).all()
    return ok({"list": [_pond_dict(p) for p in rows], "page": page, "size": size, "total": total})


class StaffIn(BaseModel):
    name: str
    phone: OptionalLooseStr = None
    post: Optional[str] = None
    status: Optional[int] = 1


@router.get("/staffs")
def list_staffs(
    page: int = 1,
    size: int = 20,
    cu: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = select(BizStaff)
    if cu.user.user_type == "ENTERPRISE" and cu.user.enterprise_id:
        q = q.where(BizStaff.enterprise_id == cu.user.enterprise_id)
    total = db.scalar(select(func.count()).select_from(q.subquery())) or 0
    rows = db.scalars(q.order_by(BizStaff.id.desc()).offset((page - 1) * size).limit(size)).all()
    return ok(
        {
            "list": [
                {
                    "id": s.id,
                    "name": s.name,
                    "phone": s.phone or "",
                    "post": s.post or "",
                    "gender": "",
                    "status": s.status,
                    "enterpriseId": s.enterprise_id,
                }
                for s in rows
            ],
            "page": page,
            "size": size,
            "total": total,
        }
    )


@router.post("/staffs")
def create_staff(body: StaffIn, cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    eid = cu.user.enterprise_id or 0
    if not eid:
        raise ApiError(40300, "企业用户才可维护人员", 403)
    s = BizStaff(enterprise_id=eid, name=body.name, phone=body.phone, post=body.post, status=body.status or 1)
    db.add(s)
    db.commit()
    db.refresh(s)
    return ok({"id": s.id})


@router.put("/staffs/{sid}")
def update_staff(sid: int, body: StaffIn, cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    s = db.get(BizStaff, sid)
    if not s or s.deleted:
        raise ApiError(40400, "人员不存在", 404)
    if cu.user.enterprise_id and s.enterprise_id != cu.user.enterprise_id:
        raise ApiError(40300, "无权限", 403)
    s.name = body.name
    s.phone = body.phone
    s.post = body.post
    if body.status is not None:
        s.status = body.status
    db.commit()
    return ok({"id": s.id})


@router.post("/ponds")
def create_pond(body: PondIn, cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    p = BizPond(
        project_id=cu.user.project_id or 0,
        enterprise_id=body.enterpriseId or cu.user.enterprise_id or 0,
        name=body.name,
        code=body.code,
        pond_type=body.pondType,
        area_mu=body.areaMu,
        species=body.species,
        township=body.township,
        lng=body.lng,
        lat=body.lat,
        geom_geojson=body.geomGeojson,
        layer_type=body.layerType,
        audit_status="DRAFT",
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    return ok({"id": p.id})


class GeoJsonImportIn(BaseModel):
    geojson: str
    defaultLayerType: str = "AQUACULTURE"
    enterpriseId: Optional[int] = None


@router.post("/ponds/import-geojson")
def import_geojson(body: GeoJsonImportIn, cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    """批量导入 GeoJSON Feature/FeatureCollection 为塘口图层（采集页「导入 GeoJSON」）。"""
    import json

    try:
        data = json.loads(body.geojson)
    except json.JSONDecodeError:
        raise ApiError(40000, "GeoJSON 格式错误")

    feats = []
    if data.get("type") == "FeatureCollection":
        feats = data.get("features") or []
    elif data.get("type") == "Feature":
        feats = [data]
    elif data.get("type") in ("Polygon", "Point", "MultiPolygon"):
        feats = [{"type": "Feature", "geometry": data, "properties": {}}]
    else:
        raise ApiError(40000, "仅支持 Feature、FeatureCollection 或 Polygon/Point")

    ent_id = body.enterpriseId or cu.user.enterprise_id or 0
    created = 0
    skipped = 0
    ids = []

    for i, feat in enumerate(feats):
        geom = feat.get("geometry")
        if not geom:
            skipped += 1
            continue
        gtype = geom.get("type")
        if gtype not in ("Polygon", "Point", "MultiPolygon"):
            skipped += 1
            continue

        props = feat.get("properties") or {}
        layer_type = (
            props.get("layerType")
            or props.get("layer_type")
            or ("OUTLET" if gtype == "Point" else body.defaultLayerType)
        )
        if layer_type not in ("AQUACULTURE", "EFFLUENT", "OUTLET"):
            layer_type = body.defaultLayerType

        if gtype == "MultiPolygon" and geom.get("coordinates"):
            geom = {"type": "Polygon", "coordinates": geom["coordinates"][0]}
            gtype = "Polygon"

        geom_str = json.dumps(geom, ensure_ascii=False)
        area_mu = 0.0
        lng = lat = None

        if gtype == "Point":
            coords = geom.get("coordinates") or []
            if len(coords) < 2:
                skipped += 1
                continue
            lng, lat = float(coords[0]), float(coords[1])
            layer_type = "OUTLET"
        elif gtype == "Polygon":
            if GIS_UTILS_AVAILABLE:
                valid, _msg = GeometryUtils.validate_polygon(geom_str)
                if not valid:
                    skipped += 1
                    continue
                area_mu = GeometryUtils.calculate_area_mu(geom_str)
                center = GeometryUtils.calculate_center(geom_str)
                if center:
                    lng, lat = center[0], center[1]
            else:
                ring = geom.get("coordinates", [[]])[0]
                if ring:
                    lng = sum(c[0] for c in ring) / len(ring)
                    lat = sum(c[1] for c in ring) / len(ring)
        else:
            skipped += 1
            continue

        name = (
            props.get("name")
            or props.get("NAME")
            or props.get("塘口名称")
            or f"导入{layerLabel(layer_type)}{i + 1}"
        )

        p = BizPond(
            project_id=cu.user.project_id or 0,
            enterprise_id=ent_id,
            name=str(name),
            code=props.get("code"),
            pond_type=props.get("pondType") or "池塘",
            area_mu=area_mu if layer_type != "OUTLET" else 0,
            species=props.get("species") or "大鲵",
            township=props.get("township") or "示范镇",
            lng=lng,
            lat=lat,
            geom_geojson=geom_str,
            layer_type=layer_type,
            audit_status="DRAFT",
        )
        db.add(p)
        db.flush()
        ids.append(p.id)
        created += 1

    db.commit()
    return ok({"count": created, "skipped": skipped, "ids": ids})


def layerLabel(t: str) -> str:
    return {"AQUACULTURE": "养殖区", "EFFLUENT": "尾水区", "OUTLET": "出水口"}.get(t, t)


@router.get("/ponds/{pid}")
def get_pond(pid: int, cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    p = db.get(BizPond, pid)
    if not p or p.deleted:
        raise ApiError(40400, "塘口不存在", 404)
    return ok(_pond_dict(p))


@router.put("/ponds/{pid}")
def update_pond(pid: int, body: PondIn, cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    p = db.get(BizPond, pid)
    if not p or p.deleted:
        raise ApiError(40400, "塘口不存在", 404)
    p.name = body.name
    p.code = body.code
    p.pond_type = body.pondType
    p.area_mu = body.areaMu
    p.species = body.species
    p.township = body.township
    p.lng = body.lng
    p.lat = body.lat
    p.geom_geojson = body.geomGeojson
    p.layer_type = body.layerType
    db.commit()
    return ok(True)


@router.post("/ponds/{pid}/submit")
def submit_pond(pid: int, cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    p = db.get(BizPond, pid)
    if not p or p.audit_status not in ("DRAFT", "REJECTED"):
        raise ApiError(40900, "状态冲突")
    p.audit_status = "SUBMITTED"
    db.add(
        SysTodo(
            project_id=p.project_id,
            enterprise_id=p.enterprise_id,
            title=f"塘口待审：{p.name}",
            biz_type="POND_AUDIT",
            biz_id=p.id,
            status="PENDING",
            portal="GOV",
            link_path="/gov/party/ponds",
        )
    )
    db.commit()
    return ok(True)


@router.post("/ponds/{pid}/audit")
def audit_pond(pid: int, body: AuditIn, cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    if cu.portal not in ("GOV", "BOTH"):
        raise ApiError(40300, "仅区县审核", 403)
    p = db.get(BizPond, pid)
    if not p or p.audit_status not in ("SUBMITTED", "PENDING"):
        raise ApiError(40900, "状态冲突")
    p.audit_status = "APPROVED" if body.approved else "REJECTED"
    p.audit_opinion = body.opinion
    for t in db.scalars(
        select(SysTodo).where(SysTodo.biz_type == "POND_AUDIT", SysTodo.biz_id == pid, SysTodo.status == "PENDING")
    ):
        t.status = "DONE"
    db.commit()
    return ok(True)


@router.post("/ponds/batch-audit")
def batch_audit_ponds(body: dict, cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    if cu.portal not in ("GOV", "BOTH"):
        raise ApiError(40300, "仅区县审核", 403)
    ids = body.get("ids", [])
    approved = body.get("approved", True)
    opinion = body.get("opinion", "批量审核")
    count = 0
    for pid in ids:
        p = db.get(BizPond, pid)
        if p and p.audit_status in ("SUBMITTED", "PENDING", "DRAFT"):
            p.audit_status = "APPROVED" if approved else "REJECTED"
            p.audit_opinion = opinion
            count += 1
            for t in db.scalars(
                select(SysTodo).where(SysTodo.biz_type == "POND_AUDIT", SysTodo.biz_id == pid, SysTodo.status == "PENDING")
            ):
                t.status = "DONE"
    db.commit()
    return ok({"count": count})


@router.get("/gis/layers")
def get_gis_layers(
    mode: str = "collect",
    keyword: Optional[str] = None,
    cu: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = select(BizPond).where(BizPond.deleted == 0)
    if cu.user.user_type == "ENTERPRISE" and cu.user.enterprise_id:
        q = q.where(BizPond.enterprise_id == cu.user.enterprise_id)
    elif cu.user.project_id:
        q = q.where(BizPond.project_id == cu.user.project_id)
    if keyword:
        q = q.where(BizPond.name.contains(keyword))
    ponds = db.scalars(q.order_by(BizPond.id.desc())).all()
    approved = len([p for p in ponds if p.audit_status == "APPROVED"])
    pending = len([p for p in ponds if p.audit_status in ("PENDING", "SUBMITTED", "DRAFT")])
    area = sum(float(p.area_mu or 0) for p in ponds if p.audit_status == "APPROVED")
    species_list = []
    for p in ponds:
        if p.species:
            species_list.extend([s.strip() for s in p.species.split(",")])
    return ok(
        {
            "ponds": [_pond_dict(p) for p in ponds],
            "summary": {
                "approvedCount": approved,
                "pendingCount": pending,
                "drawnCount": len(ponds),
                "areaMu": round(area, 2),
                "species": list(set(species_list)),
            },
        }
    )
