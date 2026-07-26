from __future__ import annotations

import json
from datetime import date, datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.common.response import ApiError, ok
from app.db import get_db
from app.deps import CurrentUser, get_current_user
from app.models import UavMission, UavPilot

router = APIRouter(prefix="/uav", tags=["uav"])


def _json_list(raw: Optional[str]) -> list:
    if not raw:
        return []
    try:
        data = json.loads(raw)
        return data if isinstance(data, list) else []
    except json.JSONDecodeError:
        return []


def _dump_list(items: Optional[list]) -> Optional[str]:
    if items is None:
        return None
    return json.dumps(items, ensure_ascii=False)


def _next_code(db: Session, prefix: str, model) -> str:
    year = datetime.now().year
    pat = f"{prefix}{year}%"
    n = db.scalar(select(func.count()).select_from(model).where(model.code.like(pat))) or 0
    return f"{prefix}{year}{n + 1:04d}"


class PilotIn(BaseModel):
    name: str
    level: Optional[str] = None
    registerDate: Optional[date] = None
    flightHours: Optional[float] = None
    violationCount: Optional[int] = 0
    attachments: Optional[list[str]] = None


class MissionIn(BaseModel):
    name: str
    taskType: Optional[str] = None
    location: Optional[str] = None
    leader: Optional[str] = None
    pilotId: Optional[int] = None
    startTime: Optional[datetime] = None
    endTime: Optional[datetime] = None
    planHours: Optional[float] = None
    actualHours: Optional[float] = None
    status: Optional[str] = "NOT_STARTED"
    acceptResult: Optional[str] = "QUALIFIED"
    remark: Optional[str] = None
    images: Optional[list[str]] = None
    videos: Optional[list[str]] = None


def _pilot_dict(p: UavPilot) -> dict:
    return {
        "id": p.id,
        "code": p.code,
        "name": p.name,
        "level": p.level,
        "registerDate": p.register_date.isoformat() if p.register_date else None,
        "flightHours": float(p.flight_hours or 0),
        "violationCount": p.violation_count or 0,
        "attachments": _json_list(p.attachments),
    }


def _mission_dict(m: UavMission, pilot: Optional[UavPilot] = None) -> dict:
    pilot_label = ""
    if pilot:
        pilot_label = f"{pilot.name}/{pilot.code}"
    elif m.pilot_id:
        pilot_label = str(m.pilot_id)
    return {
        "id": m.id,
        "code": m.code,
        "name": m.name,
        "taskType": m.task_type,
        "location": m.location,
        "leader": m.leader,
        "pilotId": m.pilot_id,
        "pilotLabel": pilot_label,
        "startTime": m.start_time.isoformat() if m.start_time else None,
        "endTime": m.end_time.isoformat() if m.end_time else None,
        "planHours": float(m.plan_hours or 0),
        "actualHours": float(m.actual_hours or 0) if m.actual_hours is not None else None,
        "status": m.status,
        "acceptResult": m.accept_result,
        "remark": m.remark,
        "images": _json_list(m.images),
        "videos": _json_list(m.videos),
    }


def _mission_status_label(s: str) -> str:
    return {
        "NOT_STARTED": "未开始",
        "IN_PROGRESS": "进行中",
        "COMPLETED": "已完成",
        "CANCELLED": "已取消",
    }.get(s, s)


def _accept_label(s: str) -> str:
    return {"QUALIFIED": "合格", "UNQUALIFIED": "不合格", "PENDING": "待验收"}.get(s, s)


@router.get("/stats")
def uav_stats(cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    pid = cu.user.project_id or 0
    pilots = db.scalar(
        select(func.count()).select_from(UavPilot).where(UavPilot.deleted == 0, UavPilot.project_id == pid)
    ) or 0
    missions = db.scalar(
        select(func.count()).select_from(UavMission).where(UavMission.deleted == 0, UavMission.project_id == pid)
    ) or 0
    pending = db.scalar(
        select(func.count()).select_from(UavMission).where(
            UavMission.deleted == 0, UavMission.project_id == pid, UavMission.status.in_(["NOT_STARTED", "IN_PROGRESS"])
        )
    ) or 0
    total_hours = db.scalar(
        select(func.coalesce(func.sum(UavPilot.flight_hours), 0)).where(UavPilot.deleted == 0, UavPilot.project_id == pid)
    ) or 0
    return ok(
        {
            "pilotCount": pilots,
            "missionCount": missions,
            "pendingCount": pending,
            "totalFlightHours": float(total_hours or 0),
        }
    )


@router.get("/pilots")
def list_pilots(
    keyword: Optional[str] = None,
    page: int = 1,
    size: int = 50,
    cu: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = select(UavPilot).where(UavPilot.deleted == 0)
    if cu.user.project_id:
        q = q.where(UavPilot.project_id == cu.user.project_id)
    if keyword:
        q = q.where(UavPilot.name.contains(keyword) | UavPilot.code.contains(keyword))
    total = db.scalar(select(func.count()).select_from(q.subquery())) or 0
    rows = db.scalars(q.order_by(UavPilot.id.desc()).offset((page - 1) * size).limit(size)).all()
    return ok({"list": [_pilot_dict(p) for p in rows], "total": total, "page": page, "size": size})


@router.post("/pilots")
def create_pilot(body: PilotIn, cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    p = UavPilot(
        project_id=cu.user.project_id or 0,
        code=_next_code(db, "FS", UavPilot),
        name=body.name,
        level=body.level,
        register_date=body.registerDate,
        flight_hours=body.flightHours,
        violation_count=body.violationCount or 0,
        attachments=_dump_list(body.attachments or []),
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    return ok(_pilot_dict(p))


@router.put("/pilots/{pid}")
def update_pilot(pid: int, body: PilotIn, cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    p = db.get(UavPilot, pid)
    if not p or p.deleted:
        raise ApiError(40400, "飞手不存在", 404)
    p.name = body.name
    p.level = body.level
    p.register_date = body.registerDate
    p.flight_hours = body.flightHours
    p.violation_count = body.violationCount or 0
    if body.attachments is not None:
        p.attachments = _dump_list(body.attachments)
    db.commit()
    return ok(_pilot_dict(p))


@router.delete("/pilots/{pid}")
def delete_pilot(pid: int, cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    p = db.get(UavPilot, pid)
    if not p or p.deleted:
        raise ApiError(40400, "飞手不存在", 404)
    p.deleted = 1
    db.commit()
    return ok(True)


@router.get("/missions")
def list_missions(
    keyword: Optional[str] = None,
    status: Optional[str] = None,
    page: int = 1,
    size: int = 50,
    cu: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = select(UavMission).where(UavMission.deleted == 0)
    if cu.user.project_id:
        q = q.where(UavMission.project_id == cu.user.project_id)
    if keyword:
        q = q.where(UavMission.name.contains(keyword) | UavMission.code.contains(keyword))
    if status:
        q = q.where(UavMission.status == status)
    total = db.scalar(select(func.count()).select_from(q.subquery())) or 0
    rows = db.scalars(q.order_by(UavMission.id.desc()).offset((page - 1) * size).limit(size)).all()
    pilot_map = {}
    pids = [m.pilot_id for m in rows if m.pilot_id]
    if pids:
        for p in db.scalars(select(UavPilot).where(UavPilot.id.in_(pids))).all():
            pilot_map[p.id] = p
    items = []
    for m in rows:
        d = _mission_dict(m, pilot_map.get(m.pilot_id))
        d["statusLabel"] = _mission_status_label(m.status)
        d["acceptResultLabel"] = _accept_label(m.accept_result)
        items.append(d)
    return ok({"list": items, "total": total, "page": page, "size": size})


@router.post("/missions")
def create_mission(body: MissionIn, cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    m = UavMission(
        project_id=cu.user.project_id or 0,
        code=_next_code(db, "RW", UavMission),
        name=body.name,
        task_type=body.taskType,
        location=body.location,
        leader=body.leader,
        pilot_id=body.pilotId,
        start_time=body.startTime,
        end_time=body.endTime,
        plan_hours=body.planHours,
        actual_hours=body.actualHours,
        status=body.status or "NOT_STARTED",
        accept_result=body.acceptResult or "QUALIFIED",
        remark=body.remark,
        images=_dump_list(body.images or []),
        videos=_dump_list(body.videos or []),
    )
    db.add(m)
    db.commit()
    db.refresh(m)
    pilot = db.get(UavPilot, m.pilot_id) if m.pilot_id else None
    d = _mission_dict(m, pilot)
    d["statusLabel"] = _mission_status_label(m.status)
    d["acceptResultLabel"] = _accept_label(m.accept_result)
    return ok(d)


@router.put("/missions/{mid}")
def update_mission(mid: int, body: MissionIn, cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    m = db.get(UavMission, mid)
    if not m or m.deleted:
        raise ApiError(40400, "任务不存在", 404)
    m.name = body.name
    m.task_type = body.taskType
    m.location = body.location
    m.leader = body.leader
    m.pilot_id = body.pilotId
    m.start_time = body.startTime
    m.end_time = body.endTime
    m.plan_hours = body.planHours
    m.actual_hours = body.actualHours
    if body.status:
        m.status = body.status
    if body.acceptResult:
        m.accept_result = body.acceptResult
    m.remark = body.remark
    if body.images is not None:
        m.images = _dump_list(body.images)
    if body.videos is not None:
        m.videos = _dump_list(body.videos)
    db.commit()
    pilot = db.get(UavPilot, m.pilot_id) if m.pilot_id else None
    d = _mission_dict(m, pilot)
    d["statusLabel"] = _mission_status_label(m.status)
    d["acceptResultLabel"] = _accept_label(m.accept_result)
    return ok(d)


@router.delete("/missions/{mid}")
def delete_mission(mid: int, cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    m = db.get(UavMission, mid)
    if not m or m.deleted:
        raise ApiError(40400, "任务不存在", 404)
    m.deleted = 1
    db.commit()
    return ok(True)
