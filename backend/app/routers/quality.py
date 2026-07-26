from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends
from app.common.coerce import OptionalLooseStr
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.common.response import ApiError, ok
from app.db import get_db
from app.deps import CurrentUser, get_current_user
from app.models import BizEnterprise, BizPond, QaInspection, QaLab, QaPolicy, QaRectification, QaSelfCheck, SysTodo

router = APIRouter(tags=["quality"])


class PolicyIn(BaseModel):
    name: str
    fileUrl: Optional[str] = None
    publishDate: Optional[str] = None


class InspectionIn(BaseModel):
    title: Optional[str] = "质量抽检"
    enterpriseId: Optional[int] = 1
    pondId: Optional[int] = None
    batchId: Optional[int] = None
    labId: Optional[int] = None
    year: Optional[int] = None
    quarter: Optional[str] = None
    level: Optional[str] = None
    species: Optional[str] = None
    result: str = "PENDING"
    enterpriseName: Optional[str] = None
    labName: Optional[str] = None
    sampleCount: Optional[int] = None
    unqualified: Optional[str] = None
    reportFile: Optional[str] = None


class RectifyReplyIn(BaseModel):
    reply: str
    rectifyDate: Optional[str] = None
    proofFile: Optional[str] = None


class ReviewIn(BaseModel):
    approved: bool
    opinion: Optional[str] = None
    reviewDate: Optional[str] = None


def _spawn_rect_from_inspection(db: Session, i: QaInspection, content: str | None = None) -> QaRectification | None:
    """不合格抽检 → 下发整改单 + 企业待办（幂等：同一 inspection 不重复建）。"""
    if i.result != "UNQUALIFIED":
        return None
    exists = db.scalar(
        select(QaRectification).where(
            QaRectification.inspection_id == i.id,
            QaRectification.deleted == 0,
        ).limit(1)
    )
    if exists:
        return exists
    rect = QaRectification(
        project_id=i.project_id,
        enterprise_id=i.enterprise_id,
        inspection_id=i.id,
        title=f"{i.title or '抽检'}不合格整改",
        status="PENDING",
        content=content or i.remark or "抽检不合格，请限期整改用药记录与水质管理",
    )
    db.add(rect)
    db.flush()
    db.add(
        SysTodo(
            project_id=i.project_id,
            enterprise_id=i.enterprise_id,
            title=f"待处理整改：{rect.title}",
            biz_type="QA_RECTIFICATION",
            biz_id=rect.id,
            status="PENDING",
            portal="ENT",
            link_path="/ent/quality/rectifications",
        )
    )
    return rect


def _rect_row(db: Session, r: QaRectification) -> dict:
    ent = db.get(BizEnterprise, r.enterprise_id) if r.enterprise_id else None
    insp = db.get(QaInspection, r.inspection_id) if r.inspection_id else None
    pond = db.get(BizPond, insp.pond_id) if insp and insp.pond_id else None
    lab = db.get(QaLab, insp.lab_id) if insp and insp.lab_id else None
    meta = {}
    if r.remark:
        try:
            import json

            meta = json.loads(r.remark) if r.remark.startswith("{") else {}
        except Exception:
            meta = {}
    return {
        "id": r.id,
        "title": r.title,
        "status": r.status,
        "content": r.content,
        "reply": r.reply,
        "reviewOpinion": r.review_opinion,
        "enterpriseId": r.enterprise_id,
        "enterpriseName": ent.name if ent else str(r.enterprise_id or "-"),
        "regionName": "示范县",
        "pondName": pond.name if pond else (meta.get("pondName") or "-"),
        "species": (insp.species if insp else None) or meta.get("species") or "-",
        "sampleCount": meta.get("sampleCount") or (3 if insp else None),
        "labName": (lab.name if lab else None) or meta.get("labName") or "-",
        "result": (insp.result if insp else None) or "UNQUALIFIED",
        "unqualified": meta.get("unqualified")
        or (("指标异常" if insp and insp.result == "UNQUALIFIED" else "—") if insp else "指标异常"),
        "reportFile": meta.get("reportFile") or ("不合格报告.pdf" if insp else "-"),
        "inspectedAt": insp.inspected_at.isoformat() if insp and insp.inspected_at else "",
        "inspectionId": r.inspection_id,
        "rectifyDate": meta.get("rectifyDate") or "",
        "proofFile": meta.get("proofFile") or "",
        "reviewDate": meta.get("reviewDate") or "",
    }


@router.get("/quality/policies")
def policies(cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.scalars(select(QaPolicy).where(QaPolicy.deleted == 0)).all()
    return ok([{"id": p.id, "name": p.name, "fileName": (p.file_url or "政策文件.pdf").split("/")[-1], "fileUrl": p.file_url, "publishDate": str(p.publish_date or "")} for p in rows])


@router.post("/quality/policies")
def create_policy(body: PolicyIn, cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    from datetime import date as date_cls

    pub = None
    if body.publishDate:
        pub = date_cls.fromisoformat(body.publishDate[:10])
    p = QaPolicy(project_id=cu.user.project_id, name=body.name, file_url=body.fileUrl, publish_date=pub)
    db.add(p)
    db.commit()
    db.refresh(p)
    return ok({"id": p.id})


@router.put("/quality/policies/{pid}")
def update_policy(pid: int, body: PolicyIn, cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    from datetime import date as date_cls

    p = db.get(QaPolicy, pid)
    if not p or p.deleted:
        raise ApiError(40400, "政策不存在", 404)
    p.name = body.name
    if body.fileUrl is not None:
        p.file_url = body.fileUrl
    if body.publishDate:
        p.publish_date = date_cls.fromisoformat(body.publishDate[:10])
    db.commit()
    return ok(True)


@router.get("/quality/inspections")
def inspections(cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    q = select(QaInspection).where(QaInspection.deleted == 0)
    if cu.user.user_type == "ENTERPRISE":
        q = q.where(QaInspection.enterprise_id == cu.user.enterprise_id)
    elif cu.user.project_id:
        q = q.where(QaInspection.project_id == cu.user.project_id)
    rows = db.scalars(q.order_by(QaInspection.id.desc())).all()
    from app.models import BizEnterprise, QaLab

    ents = {e.id: e.name for e in db.scalars(select(BizEnterprise)).all()}
    labs = {x.id: x.name for x in db.scalars(select(QaLab)).all()}
    return ok(
        [
            {
                "id": i.id,
                "title": i.title,
                "enterpriseId": i.enterprise_id,
                "enterpriseName": ents.get(i.enterprise_id, str(i.enterprise_id)),
                "status": i.status,
                "result": i.result,
                "unqualified": "—" if i.result != "UNQUALIFIED" else "指标异常",
                "batchId": i.batch_id,
                "labId": i.lab_id,
                "labName": labs.get(i.lab_id, "-"),
                "year": i.year or 2026,
                "quarter": i.quarter or "Q1",
                "level": i.level or "区级",
                "species": i.species or "-",
                "inspectedAt": i.inspected_at.isoformat() if i.inspected_at else "",
                "source": "政府监管",
            }
            for i in rows
        ]
    )


@router.post("/quality/inspections")
def create_inspection(body: InspectionIn, cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    eid = body.enterpriseId or cu.user.enterprise_id or 1
    import json

    remark_bits = {
        k: v
        for k, v in {
            "sampleCount": body.sampleCount,
            "unqualified": body.unqualified,
            "reportFile": body.reportFile,
            "labName": body.labName,
            "enterpriseName": body.enterpriseName,
        }.items()
        if v is not None
    }
    i = QaInspection(
        project_id=cu.user.project_id or 0,
        enterprise_id=eid,
        pond_id=body.pondId or 1,
        batch_id=body.batchId,
        lab_id=body.labId or 1,
        title=body.title or body.species or "质量抽检",
        year=body.year or 2026,
        quarter=body.quarter or "Q1",
        level=body.level or "区级",
        species=body.species,
        status="SUBMITTED",
        result=body.result,
        inspected_at=datetime.now(timezone.utc),
        remark=json.dumps(remark_bits, ensure_ascii=False) if remark_bits else None,
    )
    db.add(i)
    db.flush()
    rect = _spawn_rect_from_inspection(db, i)
    db.commit()
    db.refresh(i)
    return ok({"id": i.id, "rectificationId": rect.id if rect else None})


@router.post("/quality/inspections/{iid}/submit")
def submit_inspection(iid: int, cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    i = db.get(QaInspection, iid)
    if not i:
        raise ApiError(40400, "抽检不存在", 404)
    if i.status == "DRAFT":
        i.status = "SUBMITTED"
        i.inspected_at = datetime.now(timezone.utc)
    rect = _spawn_rect_from_inspection(db, i)
    db.commit()
    return ok({"rectificationId": rect.id if rect else None})


@router.post("/quality/inspections/{iid}/issue-rect")
def issue_rect_from_inspection(iid: int, cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    """区县对已提交的不合格抽检下发整改（对齐现网「操作→整改」）。"""
    if cu.portal not in ("GOV", "BOTH"):
        raise ApiError(40300, "仅区县可下发整改", 403)
    i = db.get(QaInspection, iid)
    if not i:
        raise ApiError(40400, "抽检不存在", 404)
    if i.result != "UNQUALIFIED":
        raise ApiError(40900, "仅不合格抽检可下发整改")
    if i.status == "DRAFT":
        i.status = "SUBMITTED"
        i.inspected_at = datetime.now(timezone.utc)
    rect = _spawn_rect_from_inspection(db, i)
    db.commit()
    return ok({"id": rect.id if rect else None})


@router.get("/quality/rectifications")
def rectifications(cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    q = select(QaRectification).where(QaRectification.deleted == 0)
    if cu.user.user_type == "ENTERPRISE":
        q = q.where(QaRectification.enterprise_id == cu.user.enterprise_id)
    elif cu.user.project_id:
        q = q.where(QaRectification.project_id == cu.user.project_id)
    rows = db.scalars(q.order_by(QaRectification.id.desc())).all()
    return ok([_rect_row(db, r) for r in rows])


@router.post("/quality/rectifications/{rid}/accept")
def accept_rect(rid: int, cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    r = db.get(QaRectification, rid)
    if not r:
        raise ApiError(40400, "整改单不存在", 404)
    if r.status != "PENDING":
        raise ApiError(40900, "状态冲突")
    r.status = "RECTIFYING"
    db.commit()
    return ok(True)


@router.post("/quality/rectifications/{rid}/reply")
def reply_rect(
    rid: int, body: RectifyReplyIn, cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)
):
    import json

    r = db.get(QaRectification, rid)
    if not r:
        raise ApiError(40400, "整改单不存在", 404)
    if r.status not in ("RECTIFYING", "PENDING"):
        raise ApiError(40900, "状态冲突")
    if r.status == "PENDING":
        r.status = "RECTIFYING"
    r.reply = body.reply
    meta = {}
    if r.remark and r.remark.startswith("{"):
        try:
            meta = json.loads(r.remark)
        except Exception:
            meta = {}
    if body.rectifyDate:
        meta["rectifyDate"] = body.rectifyDate
    if body.proofFile:
        meta["proofFile"] = body.proofFile
    r.remark = json.dumps(meta, ensure_ascii=False) if meta else r.remark
    r.status = "REVIEW"
    db.add(
        SysTodo(
            project_id=r.project_id,
            enterprise_id=r.enterprise_id,
            title=f"整改待复查：{r.title}",
            biz_type="QA_RECTIFICATION_REVIEW",
            biz_id=r.id,
            status="PENDING",
            portal="GOV",
            link_path="/gov/quality/rectifications",
        )
    )
    todos = db.scalars(
        select(SysTodo).where(
            SysTodo.biz_type == "QA_RECTIFICATION", SysTodo.biz_id == rid, SysTodo.status == "PENDING"
        )
    ).all()
    for t in todos:
        t.status = "DONE"
    db.commit()
    return ok(True)


@router.post("/quality/rectifications/{rid}/review")
def review_rect(rid: int, body: ReviewIn, cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    import json

    if cu.portal not in ("GOV", "BOTH"):
        raise ApiError(40300, "仅区县复查", 403)
    r = db.get(QaRectification, rid)
    if not r or r.status != "REVIEW":
        raise ApiError(40900, "状态冲突")
    r.review_opinion = body.opinion
    meta = {}
    if r.remark and r.remark.startswith("{"):
        try:
            meta = json.loads(r.remark)
        except Exception:
            meta = {}
    if body.reviewDate:
        meta["reviewDate"] = body.reviewDate
    meta["reviewResult"] = "通过" if body.approved else "驳回"
    r.remark = json.dumps(meta, ensure_ascii=False)
    r.status = "CLOSED" if body.approved else "RECTIFYING"
    todos = db.scalars(
        select(SysTodo).where(
            SysTodo.biz_type == "QA_RECTIFICATION_REVIEW", SysTodo.biz_id == rid, SysTodo.status == "PENDING"
        )
    ).all()
    for t in todos:
        t.status = "DONE"
    if not body.approved:
        db.add(
            SysTodo(
                project_id=r.project_id,
                enterprise_id=r.enterprise_id,
                title=f"整改复查驳回：{r.title}",
                biz_type="QA_RECTIFICATION",
                biz_id=r.id,
                status="PENDING",
                portal="ENT",
                link_path="/ent/quality/rectifications",
            )
        )
    db.commit()
    return ok(True)


@router.get("/quality/labs")
def labs(cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.scalars(select(QaLab).where(QaLab.deleted == 0)).all()
    return ok(
        [
            {
                "id": x.id,
                "name": x.name,
                "contact": x.contact,
                "phone": x.phone,
                "lng": x.lng,
                "lat": x.lat,
                "labType": "快检室",
                "regionName": "示范县",
                "createdAt": str(x.created_at or "")[:10],
            }
            for x in rows
        ]
    )


class LabIn(BaseModel):
    name: str
    contact: Optional[str] = None
    phone: OptionalLooseStr = None
    lng: Optional[float] = None
    lat: Optional[float] = None


@router.post("/quality/labs")
def create_lab(body: LabIn, cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    if cu.portal not in ("GOV", "BOTH"):
        raise ApiError(40300, "仅区县维护", 403)
    x = QaLab(
        project_id=cu.user.project_id,
        name=body.name,
        contact=body.contact,
        phone=body.phone,
        lng=body.lng,
        lat=body.lat,
    )
    db.add(x)
    db.commit()
    db.refresh(x)
    return ok({"id": x.id})


@router.put("/quality/labs/{lid}")
def update_lab(lid: int, body: LabIn, cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    if cu.portal not in ("GOV", "BOTH"):
        raise ApiError(40300, "仅区县维护", 403)
    x = db.get(QaLab, lid)
    if not x or x.deleted:
        raise ApiError(40400, "机构不存在", 404)
    x.name = body.name
    x.contact = body.contact
    x.phone = body.phone
    if body.lng is not None:
        x.lng = body.lng
    if body.lat is not None:
        x.lat = body.lat
    db.commit()
    return ok(True)


@router.get("/quality/self-checks")
def self_checks(cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    q = select(QaSelfCheck).where(QaSelfCheck.deleted == 0)
    if cu.user.enterprise_id:
        q = q.where(QaSelfCheck.enterprise_id == cu.user.enterprise_id)
    rows = db.scalars(q.order_by(QaSelfCheck.id.desc())).all()
    return ok(
        [
            {
                "id": s.id,
                "title": s.title,
                "result": s.result,
                "enterpriseId": s.enterprise_id,
                "pondName": "1号养殖塘",
                "species": "大鲵",
                "sampleCount": 1,
                "labName": "企业自检",
                "report": "-",
                "checkDate": s.checked_at.isoformat() if s.checked_at else None,
                "checkedAt": s.checked_at.isoformat() if s.checked_at else None,
            }
            for s in rows
        ]
    )


class SelfCheckIn(BaseModel):
    title: str
    result: str = "QUALIFIED"


@router.post("/quality/self-checks")
def create_self_check(body: SelfCheckIn, cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    s = QaSelfCheck(
        project_id=cu.user.project_id or 0,
        enterprise_id=cu.user.enterprise_id or 0,
        title=body.title,
        result=body.result,
        checked_at=datetime.now(timezone.utc),
    )
    db.add(s)
    db.commit()
    db.refresh(s)
    return ok({"id": s.id})


@router.get("/quality/stats")
def quality_stats(cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    q = select(QaInspection).where(QaInspection.deleted == 0)
    if cu.user.project_id:
        q = q.where(QaInspection.project_id == cu.user.project_id)
    rows = db.scalars(q).all()
    total = len(rows)
    unqualified = len([x for x in rows if x.result == "UNQUALIFIED"])
    qualified = len([x for x in rows if x.result == "QUALIFIED"])
    rect_open = (
        db.scalar(
            select(func.count()).select_from(QaRectification).where(
                QaRectification.deleted == 0, QaRectification.status != "CLOSED"
            )
        )
        or 0
    )
    return ok(
        {
            "inspectionTotal": total,
            "qualified": qualified,
            "unqualified": unqualified,
            "openRectifications": rect_open,
            "passRate": round(qualified / total, 3) if total else None,
        }
    )
