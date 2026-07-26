from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends
from app.common.coerce import OptionalLooseStr
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.common.response import ApiError, ok
from app.db import get_db
from app.deps import CurrentUser, get_current_user
from app.models import BizEnterprise, EfDischargePlan, EfDispatch, EfFacility, EfPatrol, EfRectification, EfWaterBody, SysTodo

router = APIRouter(prefix="/effluent", tags=["effluent"])


class WaterIn(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    level: Optional[str] = None
    zone: Optional[str] = None


class WaterUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    level: Optional[str] = None
    zone: Optional[str] = None


class PlanIn(BaseModel):
    title: str
    enterpriseId: int
    waterBodyId: Optional[int] = None
    planMonth: Optional[str] = None
    volume: Optional[float] = None
    contactName: Optional[str] = None
    contactPhone: OptionalLooseStr = None
    dischargeStart: Optional[str] = None
    dischargeEnd: Optional[str] = None


class PatrolIn(BaseModel):
    title: str
    enterpriseId: Optional[int] = None
    result: Optional[str] = None


@router.get("/waters")
def waters(cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.scalars(select(EfWaterBody).where(EfWaterBody.deleted == 0)).all()
    return ok(
        [
            {
                "id": w.id,
                "name": w.name,
                "code": w.code,
                "level": w.level or "Ⅲ",
                "enterpriseName": "示范养殖场",
                "subjectType": "个体",
                "regionName": "西湖区",
                "zone": w.name,
            }
            for w in rows
        ]
    )


@router.post("/waters")
def create_water(body: WaterIn, cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    name = (body.zone or body.name or "").strip()
    if not name:
        raise ApiError(40001, "水域名称不能为空", 400)
    w = EfWaterBody(project_id=cu.user.project_id or 0, name=name, code=body.code, level=body.level)
    db.add(w)
    db.commit()
    db.refresh(w)
    return ok({"id": w.id})


@router.put("/waters/{water_id}")
def update_water(
    water_id: int,
    body: WaterUpdate,
    cu: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    w = db.get(EfWaterBody, water_id)
    if not w or w.deleted:
        raise ApiError(40400, "水域不存在", 404)
    if body.zone is not None and str(body.zone).strip():
        w.name = str(body.zone).strip()
    elif body.name is not None and str(body.name).strip():
        w.name = str(body.name).strip()
    if body.code is not None:
        w.code = body.code
    if body.level is not None:
        w.level = body.level
    db.commit()
    return ok({"id": w.id})


@router.get("/plans")
def plans(cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    import json

    q = select(EfDischargePlan).where(EfDischargePlan.deleted == 0)
    if cu.user.user_type == "ENTERPRISE":
        q = q.where(EfDischargePlan.enterprise_id == cu.user.enterprise_id)
    rows = db.scalars(q.order_by(EfDischargePlan.id.desc())).all()
    ents = {e.id: e.name for e in db.scalars(select(BizEnterprise)).all()}
    waters_map = {w.id: w.name for w in db.scalars(select(EfWaterBody)).all()}
    out = []
    for p in rows:
        meta = {}
        if p.remark and str(p.remark).startswith("{"):
            try:
                meta = json.loads(p.remark)
            except Exception:
                meta = {}
        out.append(
            {
                "id": p.id,
                "title": p.title,
                "enterpriseId": p.enterprise_id,
                "enterpriseName": ents.get(p.enterprise_id, str(p.enterprise_id)),
                "waterBodyId": p.water_body_id,
                "waterZone": waters_map.get(p.water_body_id) if p.water_body_id else meta.get("zone") or "尾水示范区",
                "planMonth": p.plan_month,
                "volume": float(p.volume or 0),
                "status": p.status,
                "county": "示范县",
                "township": meta.get("township") or "示范街道",
                "village": meta.get("village") or "-",
                "zone": waters_map.get(p.water_body_id) if p.water_body_id else meta.get("zone") or "尾水示范区",
                "planTime": meta.get("dischargeStart") or p.plan_month or "",
                "dischargeEnd": meta.get("dischargeEnd") or "",
                "contactName": meta.get("contactName") or "-",
                "contactPhone": meta.get("contactPhone") or "-",
                "fileDate": meta.get("fileDate") or (str(p.updated_at or "")[:10] if p.status == "FILED" else ""),
            }
        )
    return ok(out)


@router.get("/plans/unfiled-enterprises")
def unfiled_enterprises(cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    if cu.portal not in ("GOV", "BOTH"):
        raise ApiError(40300, "仅区县查看", 403)
    ents = db.scalars(select(BizEnterprise).where(BizEnterprise.deleted == 0)).all()
    filed_eids = {
        p.enterprise_id
        for p in db.scalars(
            select(EfDischargePlan).where(EfDischargePlan.status == "FILED", EfDischargePlan.deleted == 0)
        ).all()
    }
    return ok(
        [
            {"id": e.id, "name": e.name, "species": e.species, "areaMu": float(e.area_mu or 0)}
            for e in ents
            if e.id not in filed_eids
        ]
    )


@router.post("/plans")
def create_plan(body: PlanIn, cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    import json

    meta = {
        k: v
        for k, v in {
            "contactName": body.contactName,
            "contactPhone": body.contactPhone,
            "dischargeStart": body.dischargeStart,
            "dischargeEnd": body.dischargeEnd,
        }.items()
        if v
    }
    p = EfDischargePlan(
        project_id=cu.user.project_id or 0,
        enterprise_id=body.enterpriseId,
        water_body_id=body.waterBodyId,
        title=body.title,
        plan_month=body.planMonth or (body.dischargeStart or "")[:7] or None,
        volume=body.volume,
        status="DRAFT",
        remark=json.dumps(meta, ensure_ascii=False) if meta else None,
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    return ok({"id": p.id})


@router.put("/plans/{pid}")
def update_plan(pid: int, body: PlanIn, cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    import json

    p = db.get(EfDischargePlan, pid)
    if not p or p.deleted:
        raise ApiError(40400, "计划不存在", 404)
    if p.status not in ("DRAFT", "REJECTED"):
        raise ApiError(40900, "仅草稿或已驳回状态可编辑")
    if cu.user.user_type == "ENTERPRISE" and cu.user.enterprise_id != p.enterprise_id:
        raise ApiError(40300, "无权限", 403)
    meta = {}
    if p.remark and str(p.remark).startswith("{"):
        try:
            meta = json.loads(p.remark)
        except Exception:
            meta = {}
    for k, v in {
        "contactName": body.contactName,
        "contactPhone": body.contactPhone,
        "dischargeStart": body.dischargeStart,
        "dischargeEnd": body.dischargeEnd,
    }.items():
        if v not in (None, ""):
            meta[k] = v
    p.title = body.title
    p.enterprise_id = body.enterpriseId
    if body.waterBodyId is not None:
        p.water_body_id = body.waterBodyId
    if body.volume is not None:
        p.volume = body.volume
    if body.dischargeStart:
        p.plan_month = body.planMonth or body.dischargeStart[:7]
    elif body.planMonth:
        p.plan_month = body.planMonth
    p.remark = json.dumps(meta, ensure_ascii=False) if meta else p.remark
    db.commit()
    return ok({"id": p.id})


@router.post("/plans/{pid}/submit")
def submit_plan(pid: int, cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    p = db.get(EfDischargePlan, pid)
    if not p or p.status not in ("DRAFT", "REJECTED"):
        raise ApiError(40900, "状态冲突")
    p.status = "SUBMITTED"
    db.commit()
    return ok(True)


@router.post("/plans/{pid}/reject")
def reject_plan(pid: int, cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    if cu.portal not in ("GOV", "BOTH"):
        raise ApiError(40300, "仅区县驳回", 403)
    p = db.get(EfDischargePlan, pid)
    if not p or p.status != "SUBMITTED":
        raise ApiError(40900, "状态冲突")
    p.status = "REJECTED"
    db.commit()
    return ok(True)


@router.post("/plans/{pid}/file")
def file_plan(pid: int, cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    import json
    from datetime import date

    if cu.portal not in ("GOV", "BOTH"):
        raise ApiError(40300, "仅区县备案", 403)
    p = db.get(EfDischargePlan, pid)
    if not p or p.status != "SUBMITTED":
        raise ApiError(40900, "状态冲突")
    meta = {}
    if p.remark and str(p.remark).startswith("{"):
        try:
            meta = json.loads(p.remark)
        except Exception:
            meta = {}
    meta["fileDate"] = str(date.today())
    p.remark = json.dumps(meta, ensure_ascii=False)
    p.status = "FILED"
    db.commit()
    return ok(True)


@router.get("/facilities")
def facilities(cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.scalars(select(EfFacility).where(EfFacility.deleted == 0)).all()
    return ok(
        [{"id": f.id, "name": f.name, "facilityType": f.facility_type, "enterpriseId": f.enterprise_id, "pondId": f.pond_id} for f in rows]
    )


@router.post("/patrols")
def create_patrol(body: PatrolIn, cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    p = EfPatrol(
        project_id=cu.user.project_id or 0,
        enterprise_id=body.enterpriseId or cu.user.enterprise_id or 1,
        title=body.title,
        result=body.result,
        status="DONE",
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    return ok({"id": p.id})


@router.get("/patrols")
def list_patrols(cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    q = select(EfPatrol).where(EfPatrol.deleted == 0)
    if cu.user.user_type == "ENTERPRISE":
        q = q.where(EfPatrol.enterprise_id == cu.user.enterprise_id)
    rows = db.scalars(q.order_by(EfPatrol.id.desc())).all()
    return ok(
        [
            {
                "id": p.id,
                "title": p.title,
                "result": p.result,
                "status": p.status,
                "enterpriseId": p.enterprise_id,
                "createdAt": p.created_at.isoformat() if p.created_at else "",
            }
            for p in rows
        ]
    )


@router.put("/patrols/{pid}")
def update_patrol(pid: int, body: PatrolIn, cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    p = db.get(EfPatrol, pid)
    if not p or p.deleted:
        raise ApiError(40400, "巡检记录不存在", 404)
    if cu.user.enterprise_id and p.enterprise_id != cu.user.enterprise_id:
        raise ApiError(40300, "无权限", 403)
    p.title = body.title
    p.result = body.result
    db.commit()
    return ok({"id": p.id})


class DispatchIn(BaseModel):
    title: str
    enterpriseId: int
    content: Optional[str] = None
    officerName: Optional[str] = None
    labName: Optional[str] = None
    result: Optional[str] = None
    unqualified: Optional[str] = None


@router.get("/dispatches")
def dispatches(cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    import json

    q = select(EfDispatch).where(EfDispatch.deleted == 0)
    if cu.user.user_type == "ENTERPRISE":
        q = q.where(EfDispatch.enterprise_id == cu.user.enterprise_id)
    rows = db.scalars(q.order_by(EfDispatch.id.desc())).all()
    ents = {e.id: e.name for e in db.scalars(select(BizEnterprise)).all()}
    out = []
    for d in rows:
        meta = {}
        if d.remark and str(d.remark).startswith("{"):
            try:
                meta = json.loads(d.remark)
            except Exception:
                meta = {}
        out.append(
            {
                "id": d.id,
                "title": d.title,
                "content": d.content,
                "status": d.status,
                "feedback": d.feedback,
                "enterpriseId": d.enterprise_id,
                "enterpriseName": ents.get(d.enterprise_id, str(d.enterprise_id)),
                "officerName": meta.get("officerName") or "区县渔政执法",
                "labName": meta.get("labName") or "区县水产检测中心",
                "result": meta.get("result") or "需处置",
                "unqualified": meta.get("unqualified") or "—",
                "reportFile": meta.get("reportFile") or "调度通知.pdf",
                "disposeDate": meta.get("disposeDate") or (str(d.created_at or "")[:10]),
            }
        )
    return ok(out)


@router.post("/dispatches")
def create_dispatch(body: DispatchIn, cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    import json

    if cu.portal not in ("GOV", "BOTH"):
        raise ApiError(40300, "仅区县下发调度", 403)
    meta = {
        k: v
        for k, v in {
            "officerName": body.officerName,
            "labName": body.labName,
            "result": body.result,
            "unqualified": body.unqualified,
        }.items()
        if v
    }
    d = EfDispatch(
        project_id=cu.user.project_id or 0,
        enterprise_id=body.enterpriseId,
        title=body.title,
        content=body.content,
        status="PENDING",
        remark=json.dumps(meta, ensure_ascii=False) if meta else None,
    )
    db.add(d)
    db.flush()
    db.add(
        SysTodo(
            project_id=d.project_id,
            enterprise_id=body.enterpriseId,
            title=f"尾水调度待处理：{d.title}",
            biz_type="EF_DISPATCH",
            biz_id=d.id,
            status="PENDING",
            portal="ENT",
            link_path="/ent/effluent/dispatches",
        )
    )
    db.commit()
    db.refresh(d)
    return ok({"id": d.id})


@router.post("/dispatches/{did}/accept")
def accept_dispatch(did: int, cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    d = db.get(EfDispatch, did)
    if not d or d.status != "PENDING":
        raise ApiError(40900, "状态冲突")
    d.status = "DOING"
    db.commit()
    return ok(True)


class FeedbackIn(BaseModel):
    feedback: str


@router.post("/dispatches/{did}/feedback")
def feedback_dispatch(did: int, body: FeedbackIn, cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    d = db.get(EfDispatch, did)
    if not d or d.status not in ("PENDING", "DOING"):
        raise ApiError(40900, "状态冲突")
    d.feedback = body.feedback
    d.status = "DONE"
    for t in db.scalars(
        select(SysTodo).where(SysTodo.biz_type == "EF_DISPATCH", SysTodo.biz_id == did, SysTodo.status == "PENDING")
    ):
        t.status = "DONE"
    db.commit()
    return ok(True)


class EfRectIn(BaseModel):
    title: str
    enterpriseId: int
    content: Optional[str] = None


@router.get("/rectifications")
def ef_rects(cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    q = select(EfRectification).where(EfRectification.deleted == 0)
    if cu.user.user_type == "ENTERPRISE":
        q = q.where(EfRectification.enterprise_id == cu.user.enterprise_id)
    rows = db.scalars(q.order_by(EfRectification.id.desc())).all()
    ents = {e.id: e.name for e in db.scalars(select(BizEnterprise)).all()}
    return ok(
        [
            {
                "id": r.id,
                "title": r.title,
                "content": r.content,
                "status": r.status,
                "reply": r.reply,
                "enterpriseId": r.enterprise_id,
                "enterpriseName": ents.get(r.enterprise_id, str(r.enterprise_id)),
                "superviseType": "尾水监管",
                "officerName": "区县渔政执法",
                "labName": "区县水产检测中心",
                "unqualified": "排放口标识",
                "reportFile": "整改通知.pdf",
                "disposeDate": str(r.created_at or "")[:10],
                "rectifyDate": "",
                "reviewDate": "",
            }
            for r in rows
        ]
    )


@router.post("/rectifications")
def create_ef_rect(body: EfRectIn, cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    if cu.portal not in ("GOV", "BOTH"):
        raise ApiError(40300, "仅区县下发", 403)
    r = EfRectification(
        project_id=cu.user.project_id or 0,
        enterprise_id=body.enterpriseId,
        title=body.title,
        content=body.content,
        status="PENDING",
    )
    db.add(r)
    db.flush()
    db.add(
        SysTodo(
            project_id=r.project_id,
            enterprise_id=body.enterpriseId,
            title=f"尾水整改：{r.title}",
            biz_type="EF_RECTIFICATION",
            biz_id=r.id,
            status="PENDING",
            portal="ENT",
            link_path="/ent/effluent/rectifications",
        )
    )
    db.commit()
    db.refresh(r)
    return ok({"id": r.id})


@router.post("/rectifications/{rid}/accept")
def accept_ef_rect(rid: int, cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    r = db.get(EfRectification, rid)
    if not r or r.status != "PENDING":
        raise ApiError(40900, "状态冲突")
    r.status = "RECTIFYING"
    db.commit()
    return ok(True)


@router.post("/rectifications/{rid}/reply")
def reply_ef_rect(rid: int, body: FeedbackIn, cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    r = db.get(EfRectification, rid)
    if not r:
        raise ApiError(40400, "不存在", 404)
    if r.status not in ("PENDING", "RECTIFYING"):
        raise ApiError(40900, "状态冲突")
    r.reply = body.feedback
    r.status = "REVIEW"
    for t in db.scalars(
        select(SysTodo).where(SysTodo.biz_type == "EF_RECTIFICATION", SysTodo.biz_id == rid, SysTodo.status == "PENDING")
    ):
        t.status = "DONE"
    db.add(
        SysTodo(
            project_id=r.project_id,
            enterprise_id=r.enterprise_id,
            title=f"尾水整改待验收：{r.title}",
            biz_type="EF_RECTIFICATION_REVIEW",
            biz_id=r.id,
            status="PENDING",
            portal="GOV",
            link_path="/gov/effluent/plans",
        )
    )
    db.commit()
    return ok(True)


class EfReviewIn(BaseModel):
    approved: bool = True
    opinion: Optional[str] = None


@router.post("/rectifications/{rid}/review")
def review_ef_rect(rid: int, body: EfReviewIn, cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    if cu.portal not in ("GOV", "BOTH"):
        raise ApiError(40300, "仅区县验收", 403)
    r = db.get(EfRectification, rid)
    if not r or r.status != "REVIEW":
        raise ApiError(40900, "状态冲突")
    r.status = "CLOSED" if body.approved else "RECTIFYING"
    if body.opinion:
        r.remark = body.opinion
    for t in db.scalars(
        select(SysTodo).where(
            SysTodo.biz_type == "EF_RECTIFICATION_REVIEW", SysTodo.biz_id == rid, SysTodo.status == "PENDING"
        )
    ):
        t.status = "DONE"
    db.commit()
    return ok(True)
