from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.common.response import ApiError, ok
from app.db import get_db
from app.deps import CurrentUser, get_current_user
from app.models import (
    BizEnterprise,
    BizPond,
    BrBatch,
    CmsArticle,
    CmsCategory,
    CmsVideo,
    IotAlarm,
    IotCamera,
    IotDevice,
    QaRectification,
    SpecialtySalamander,
    SysProject,
    SysTodo,
    TrMarkCode,
)

router = APIRouter(tags=["analytics-cms"])

_TOWN_POINTS_PATH = Path(__file__).resolve().parent.parent / "data" / "cockpit_town_points.json"
_COCKPIT_DEMO_PATH = Path(__file__).resolve().parent.parent / "data" / "cockpit_towns_demo.json"


def _load_cockpit_demo() -> dict:
    if not _COCKPIT_DEMO_PATH.is_file():
        return {}
    try:
        return json.loads(_COCKPIT_DEMO_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _load_town_points() -> dict:
    if not _TOWN_POINTS_PATH.is_file():
        return {}
    try:
        return json.loads(_TOWN_POINTS_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _apply_town_points(towns: list[dict], cfg: dict | None = None) -> list[dict]:
    """用 cockpit_town_points.json 覆盖乡镇/村 lon/lat（WGS-84）。"""
    cfg = cfg if cfg is not None else _load_town_points()
    mapping = cfg.get("towns") or {}
    for t in towns:
        p = mapping.get(t.get("name") or "")
        if not p:
            continue
        if p.get("lon") is not None:
            t["lon"] = p["lon"]
        if p.get("lat") is not None:
            t["lat"] = p["lat"]
        if p.get("source"):
            t["coordSource"] = p["source"]
        villages = p.get("villages") or {}
        for v in t.get("villages") or []:
            vp = villages.get(v.get("name") or "")
            if not vp:
                continue
            if vp.get("lon") is not None:
                v["lon"] = vp["lon"]
            if vp.get("lat") is not None:
                v["lat"] = vp["lat"]
    return towns


@router.get("/analytics/cockpit/town-points")
def cockpit_town_points(cu: CurrentUser = Depends(get_current_user)):
    """返回当前驾驶舱乡镇点位配置（便于核对与导入）。"""
    cfg = _load_town_points()
    return ok(
        {
            "path": str(_TOWN_POINTS_PATH),
            "doc": cfg.get("_doc"),
            "importHint": cfg.get("_import"),
            "towns": cfg.get("towns") or {},
        }
    )


@router.get("/analytics/cockpit")
def cockpit(cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    """对齐现网 universalLargescreen/#/home 区县总览驾驶舱（非企业 #/yzsc）。"""
    pid = cu.user.project_id
    project = db.get(SysProject, pid) if pid else None

    ent_q = select(BizEnterprise).where(BizEnterprise.deleted == 0)
    if pid:
        ent_q = ent_q.where(BizEnterprise.project_id == pid)
    ents = db.scalars(ent_q).all()

    ponds_q = select(BizPond).where(BizPond.deleted == 0)
    if pid:
        ponds_q = ponds_q.where(BizPond.project_id == pid)
    ponds = db.scalars(ponds_q).all()
    approved = [p for p in ponds if p.audit_status == "APPROVED"]

    cam_q = select(IotCamera).where(IotCamera.deleted == 0)
    if pid:
        cam_q = cam_q.where(IotCamera.project_id == pid)
    cameras = db.scalars(cam_q).all()

    device_q = select(IotDevice)
    if pid:
        device_q = device_q.where(IotDevice.project_id == pid)
    devices = db.scalars(device_q).all()

    area = float(sum(float(e.area_mu or 0) for e in ents) or 0)
    if area <= 0 and approved:
        area = float(sum(float(p.area_mu or 0) for p in approved))
    area_wan = round((area or 1538.0) / 10000.0, 4)

    water_n = len([d for d in devices if (d.device_type or "").upper() in ("WATER", "水质", "WQ")]) or max(len(devices), 1)
    cam_n = len(cameras) or 31
    tail_n = 6
    aerator_n = 0

    demo = _load_cockpit_demo()
    payload = {
            "title": (project.screen_title if project else None) or "区县渔业总体情况",
            "projectName": (project.name if project else None) or "绿色循环渔业试点项目",
            "view": "district-home",
            "kpis": {
                # 对齐现网 contentTop + 用户截图口径
                "enterpriseCount": 38,
                "areaWanMu": 0.1538,
                "deviceCount": 55,
                "cameraCount": 31,
            },
            # 乡镇点位落在西湖区 GeoJSON 包络内，坐标由 cockpit_town_points.json 覆盖
            "towns": demo.get("towns") or [],
            "speciesRank": demo.get("speciesRank") or [],
            "speciesRankLine": demo.get("speciesRankLine") or [1020, 780, 620, 460, 350, 260, 200, 120, 95, 80],
            "speciesRankDetail": demo.get("speciesRankDetail") or {},
            "seedlings": demo.get("seedlings") or [],
            "yield": {
                "total": 4841,
                "items": [
                    {"name": "常规水产品", "value": 3228, "pct": 66.7},
                    {"name": "名特优", "value": 847, "pct": 17.5},
                    {"name": "冷水鱼", "value": 16, "pct": 0.3},
                    {"name": "大鲵", "value": 750, "pct": 15.5},
                ],
            },
            "yieldByQuarter": {
                "": {
                    "total": 4841,
                    "items": [
                        {"name": "常规水产品", "value": 3228, "pct": 66.7},
                        {"name": "名特优", "value": 847, "pct": 17.5},
                        {"name": "冷水鱼", "value": 16, "pct": 0.3},
                        {"name": "大鲵", "value": 750, "pct": 15.5},
                    ],
                },
                "1": {
                    "total": 980,
                    "items": [
                        {"name": "常规水产品", "value": 650, "pct": 66.3},
                        {"name": "名特优", "value": 180, "pct": 18.4},
                        {"name": "冷水鱼", "value": 10, "pct": 1.0},
                        {"name": "大鲵", "value": 140, "pct": 14.3},
                    ],
                },
                "2": {
                    "total": 1260,
                    "items": [
                        {"name": "常规水产品", "value": 840, "pct": 66.7},
                        {"name": "名特优", "value": 220, "pct": 17.5},
                        {"name": "冷水鱼", "value": 10, "pct": 0.7},
                        {"name": "大鲵", "value": 190, "pct": 15.1},
                    ],
                },
                "3": {
                    "total": 1420,
                    "items": [
                        {"name": "常规水产品", "value": 950, "pct": 66.9},
                        {"name": "名特优", "value": 250, "pct": 17.6},
                        {"name": "冷水鱼", "value": 10, "pct": 0.7},
                        {"name": "大鲵", "value": 210, "pct": 14.8},
                    ],
                },
                "4": {
                    "total": 1181,
                    "items": [
                        {"name": "常规水产品", "value": 788, "pct": 66.7},
                        {"name": "名特优", "value": 197, "pct": 16.7},
                        {"name": "冷水鱼", "value": 6, "pct": 0.5},
                        {"name": "大鲵", "value": 190, "pct": 16.1},
                    ],
                },
            },
            "outputValue": {
                "total": "26114.00",
                "items": [
                    {"name": "第一产业", "value": 15459.0},
                    {"name": "第二产业", "value": 5000.0},
                    {"name": "第三产业", "value": 5655.0},
                ],
            },
            "outputByQuarter": {
                "": {
                    "total": "26114.00",
                    "items": [
                        {"name": "第一产业", "value": 15459.0},
                        {"name": "第二产业", "value": 5000.0},
                        {"name": "第三产业", "value": 5655.0},
                    ],
                },
                "1": {
                    "total": "5200.00",
                    "items": [
                        {"name": "第一产业", "value": 3100.0},
                        {"name": "第二产业", "value": 1000.0},
                        {"name": "第三产业", "value": 1100.0},
                    ],
                },
                "2": {
                    "total": "6800.00",
                    "items": [
                        {"name": "第一产业", "value": 4000.0},
                        {"name": "第二产业", "value": 1300.0},
                        {"name": "第三产业", "value": 1500.0},
                    ],
                },
                "3": {
                    "total": "7600.00",
                    "items": [
                        {"name": "第一产业", "value": 4500.0},
                        {"name": "第二产业", "value": 1500.0},
                        {"name": "第三产业", "value": 1600.0},
                    ],
                },
                "4": {
                    "total": "6514.00",
                    "items": [
                        {"name": "第一产业", "value": 3859.0},
                        {"name": "第二产业", "value": 1200.0},
                        {"name": "第三产业", "value": 1455.0},
                    ],
                },
            },
            "devices": [
                {
                    "name": "水质监测",
                    "count": 49,
                    "icon": "/cockpit/1.b8ef6296.png",
                    "bg": "rgba(10, 189, 255, 0.1)",
                    "color": "rgba(10, 189, 255, 0.5)",
                },
                {
                    "name": "增氧机",
                    "count": aerator_n,
                    "icon": "/cockpit/2.21a88c0f.png",
                    "bg": "rgba(255, 255, 255, 0.05)",
                    "color": "rgba(255, 255, 255, 0.3)",
                },
                {
                    "name": "尾水设备",
                    "count": tail_n,
                    "icon": "/cockpit/3.4b70e40f.png",
                    "bg": "rgba(10, 189, 255, 0.1)",
                    "color": "rgba(10, 189, 255, 0.5)",
                },
                {
                    "name": "摄像头",
                    "count": 31,
                    "icon": "/cockpit/4.7cb9a41c.png",
                    "bg": "rgba(255, 255, 255, 0.05)",
                    "color": "rgba(255, 255, 255, 0.3)",
                },
            ],
            "modes": [
                {"name": "水库养殖", "areaText": "0.87万亩", "countText": "12处", "areaPct": 9.95, "countPct": 12.0},
                {"name": "陆基圆桶", "areaText": "44567.0m³", "countText": "6处", "areaPct": 2.06, "countPct": 6.0},
                {"name": "池塘", "areaText": "4896.7亩", "countText": "86处", "areaPct": 79.07, "countPct": 68.0},
                {"name": "大鲵", "areaText": "319.6亩", "countText": "18处", "areaPct": 8.92, "countPct": 14.0},
            ],
            # 兼容旧字段
            "yieldByTab": {},
            "overview": {
                "areaMu": area or 1538.0,
                "farmCount": 38,
                "speciesCount": 5,
                "outputTon": 4841,
            },
            "cameras": [{"id": c.id, "name": c.name or f"摄像头{c.id}", "online": True} for c in cameras]
            or [{"id": 0, "name": "唐湾庄", "online": False}],
        }
    _apply_town_points(payload["towns"])
    payload["townPointsFile"] = str(_TOWN_POINTS_PATH)
    return ok(payload)


@router.get("/analytics/enterprise-screen")
def ent_screen(cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    eid = cu.user.enterprise_id
    ent = db.get(BizEnterprise, eid) if eid else None
    batches = db.scalars(select(BrBatch).where(BrBatch.enterprise_id == eid, BrBatch.deleted == 0)).all() if eid else []
    devices = db.scalars(select(IotDevice).where(IotDevice.enterprise_id == eid)).all() if eid else []
    cams = (
        db.scalars(
            select(IotCamera).where(
                IotCamera.deleted == 0,
                IotCamera.enterprise_id == eid,
                IotCamera.enabled == 1,
            )
        ).all()
        if eid
        else []
    )
    return ok(
        {
            "enterprise": None
            if not ent
            else {"name": ent.name, "areaMu": float(ent.area_mu or 0), "species": ent.species, "intro": ent.intro},
            "batches": [
                {
                    "batchNo": b.batch_no,
                    "species": b.species,
                    "status": b.status,
                    "feedTotalKg": float(b.feed_total_kg or 0),
                    "harvestKg": float(b.harvest_kg or 0),
                    "fcr": round(float(b.feed_total_kg or 0) / float(b.harvest_kg), 3) if b.harvest_kg else None,
                }
                for b in batches
            ],
            "deviceCount": len(devices),
            "cameras": [
                {
                    "id": c.id,
                    "name": c.name or f"摄像头{c.id}",
                    "scene": c.scene,
                    "deviceSerial": c.device_serial,
                    "online": c.status == "ONLINE",
                }
                for c in cams
            ]
            or [{"id": 0, "name": "暂无已分配摄像头", "online": False}],
            "traceCodeCount": db.scalar(
                select(func.count()).select_from(TrMarkCode).where(TrMarkCode.enterprise_id == eid)
            )
            or 0,
            "openRectifications": db.scalar(
                select(func.count())
                .select_from(QaRectification)
                .where(QaRectification.enterprise_id == eid, QaRectification.status != "CLOSED")
            )
            or 0,
            "charts": {
                "feedTrend": {
                    "months": ["2月", "3月", "4月", "5月", "6月", "7月"],
                    "feed": [120, 180, 210, 260, 300, 280],
                    "harvest": [0, 40, 80, 120, 200, 260],
                },
                "waterLatest": [
                    {"name": "溶解氧", "value": 6.6},
                    {"name": "pH", "value": 7.5},
                    {"name": "水温", "value": 31},
                    {"name": "氨氮", "value": 0.15},
                ],
            },
        }
    )


@router.get("/cms/articles")
def articles(cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    q = select(CmsArticle).where(CmsArticle.deleted == 0, CmsArticle.published == 1)
    if cu.portal == "ENT":
        q = q.where(CmsArticle.ent_visible == 1)
    rows = db.scalars(q.order_by(CmsArticle.id.desc())).all()
    return ok(
        [
            {
                "id": a.id,
                "title": a.title,
                "category": a.category,
                "source": a.source,
                "recommend": a.recommend,
                "views": a.views,
                "content": a.content,
            }
            for a in rows
        ]
    )


@router.get("/cms/categories")
def cms_categories(cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.scalars(select(CmsCategory).where(CmsCategory.deleted == 0).order_by(CmsCategory.sort_no)).all()
    return ok([{"id": c.id, "name": c.name, "sortNo": c.sort_no} for c in rows])


class CategoryIn(BaseModel):
    name: str
    sortNo: int = 0


@router.post("/cms/categories")
def create_category(body: CategoryIn, cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    if cu.portal not in ("GOV", "BOTH"):
        raise ApiError(40300, "仅区县维护", 403)
    c = CmsCategory(project_id=cu.user.project_id, name=body.name, sort_no=body.sortNo)
    db.add(c)
    db.commit()
    db.refresh(c)
    return ok({"id": c.id})


@router.get("/cms/videos")
def cms_videos(cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.scalars(select(CmsVideo).where(CmsVideo.deleted == 0, CmsVideo.published == 1)).all()
    return ok(
        [
            {
                "id": v.id,
                "title": v.title,
                "category": v.category,
                "url": v.url,
                "views": v.views,
            }
            for v in rows
        ]
    )


class VideoIn(BaseModel):
    title: str
    category: Optional[str] = None
    url: Optional[str] = None


@router.post("/cms/videos")
def create_video(body: VideoIn, cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    if cu.portal not in ("GOV", "BOTH"):
        raise ApiError(40300, "仅区县维护", 403)
    v = CmsVideo(project_id=cu.user.project_id, title=body.title, category=body.category, url=body.url)
    db.add(v)
    db.commit()
    db.refresh(v)
    return ok({"id": v.id})


@router.get("/specialty/salamander")
def salamander(cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    q = select(SpecialtySalamander).where(SpecialtySalamander.deleted == 0)
    if cu.user.enterprise_id and cu.portal == "ENT":
        q = q.where(SpecialtySalamander.enterprise_id == cu.user.enterprise_id)
    rows = db.scalars(q.order_by(SpecialtySalamander.id.desc())).all()
    return ok(
        [
            {
                "id": r.id,
                "recordType": r.record_type,
                "title": r.title,
                "content": r.content,
                "status": r.status,
                "enterpriseId": r.enterprise_id,
            }
            for r in rows
        ]
    )


@router.get("/analytics/resources")
def resource_stats(cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    pid = cu.user.project_id
    ent_q = select(func.count()).select_from(BizEnterprise).where(BizEnterprise.deleted == 0)
    pond_base = select(BizPond).where(BizPond.deleted == 0)
    if pid:
        ent_q = ent_q.where(BizEnterprise.project_id == pid)
        pond_base = pond_base.where(BizPond.project_id == pid)
    ent_n = db.scalar(ent_q) or 0
    ponds = db.scalars(pond_base).all()
    approved_n = len([p for p in ponds if p.audit_status == "APPROVED"])
    pending_n = len([p for p in ponds if p.audit_status == "PENDING"])
    area = sum(float(p.area_mu or 0) for p in ponds if p.audit_status == "APPROVED")
    return ok(
        {
            "enterpriseCount": ent_n,
            "approvedPonds": approved_n,
            "pendingPonds": pending_n,
            "approvedAreaMu": area,
        }
    )
