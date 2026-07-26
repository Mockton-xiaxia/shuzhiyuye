from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.common.response import ApiError, ok
from app.db import get_db
from app.deps import CurrentUser, get_current_user
from app.models import DiAlert, DiDiagnosisLink, DiReport, SysTodo

router = APIRouter(prefix="/disease", tags=["disease"])


class ReportIn(BaseModel):
    title: str
    symptom: Optional[str] = None
    pondId: Optional[int] = None
    enterpriseId: Optional[int] = None


@router.get("/reports")
def reports(cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    q = select(DiReport).where(DiReport.deleted == 0)
    if cu.user.user_type == "ENTERPRISE":
        q = q.where(DiReport.enterprise_id == cu.user.enterprise_id)
    elif cu.user.project_id:
        q = q.where(DiReport.project_id == cu.user.project_id)
    rows = db.scalars(q.order_by(DiReport.id.desc())).all()
    return ok(
        [
            {
                "id": r.id,
                "title": r.title,
                "symptom": r.symptom,
                "status": r.status,
                "enterpriseId": r.enterprise_id,
                "pondId": r.pond_id,
            }
            for r in rows
        ]
    )


@router.post("/reports")
def create_report(body: ReportIn, cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    eid = body.enterpriseId or cu.user.enterprise_id
    if not eid:
        raise ApiError(40000, "缺少 enterpriseId")
    r = DiReport(
        project_id=cu.user.project_id or 0,
        enterprise_id=eid,
        pond_id=body.pondId,
        title=body.title,
        symptom=body.symptom,
        status="SUBMITTED",
    )
    db.add(r)
    db.flush()
    db.add(
        SysTodo(
            project_id=r.project_id,
            enterprise_id=eid,
            title=f"病情测报待关注：{r.title}",
            biz_type="DISEASE_REPORT",
            biz_id=r.id,
            status="PENDING",
            portal="GOV",
            link_path="/gov/disease/reports",
        )
    )
    db.commit()
    db.refresh(r)
    return ok({"id": r.id})


@router.get("/alerts")
def alerts(cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    q = select(DiAlert).where(DiAlert.deleted == 0)
    if cu.user.project_id:
        q = q.where(DiAlert.project_id == cu.user.project_id)
    rows = db.scalars(q.order_by(DiAlert.id.desc())).all()
    return ok(
        [
            {
                "id": a.id,
                "title": a.title,
                "level": a.level,
                "content": a.content,
                "status": a.status,
                "species": "大鲵",
                "diseaseName": a.title,
                "pondName": "1号塘",
                "areaMu": 28.88,
                "occurredAt": str(a.created_at or "")[:19],
            }
            for a in rows
        ]
    )


class AlertIn(BaseModel):
    title: str
    level: str = "WARN"
    content: Optional[str] = None


@router.post("/alerts")
def create_alert(body: AlertIn, cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    if cu.portal not in ("GOV", "BOTH"):
        raise ApiError(40300, "仅区县发布预警", 403)
    a = DiAlert(project_id=cu.user.project_id or 0, title=body.title, level=body.level, content=body.content)
    db.add(a)
    db.commit()
    db.refresh(a)
    return ok({"id": a.id})


@router.put("/alerts/{aid}")
def update_alert(aid: int, body: AlertIn, cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    if cu.portal not in ("GOV", "BOTH"):
        raise ApiError(40300, "仅区县可编辑预警", 403)
    a = db.get(DiAlert, aid)
    if not a or a.deleted:
        raise ApiError(40400, "预警不存在", 404)
    a.title = body.title
    a.level = body.level
    a.content = body.content
    db.commit()
    return ok({"id": a.id})


@router.get("/diagnosis-links")
def diagnosis_links(cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.scalars(select(DiDiagnosisLink).where(DiDiagnosisLink.deleted == 0)).all()
    return ok([{"id": d.id, "name": d.name, "url": d.url, "portal": d.portal} for d in rows])
