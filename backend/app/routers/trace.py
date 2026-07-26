from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.common.response import ApiError, ok
from app.db import get_db
from app.deps import CurrentUser, get_current_user
from app.models import TrMarkApply, TrMarkCode, TrMarkIssue, BizEnterprise, BrActivity, BrBatch, BrHarvest, SysTodo
from app.services.withdrawal import assert_withdrawal_ok

router = APIRouter(tags=["trace"])

_BRAND_REPLACEMENTS = (
    ("南郑大鲵", "本地大鲵"),
    ("南郑", "示范"),
)


def _scrub_brand(value: str | None) -> str:
    if not value:
        return "本地大鲵"
    out = value
    for old, new in _BRAND_REPLACEMENTS:
        out = out.replace(old, new)
    return out


class ApplyIn(BaseModel):
    batchId: Optional[int] = 1
    applyQty: int = 1
    species: Optional[str] = None
    brand: Optional[str] = None


class AuditIn(BaseModel):
    approved: bool
    opinion: Optional[str] = None


@router.get("/trace/applies")
def list_applies(cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    q = select(TrMarkApply).where(TrMarkApply.deleted == 0)
    if cu.user.user_type == "ENTERPRISE":
        q = q.where(TrMarkApply.enterprise_id == cu.user.enterprise_id)
    elif cu.user.project_id:
        q = q.where(TrMarkApply.project_id == cu.user.project_id)
    rows = db.scalars(q.order_by(TrMarkApply.id.desc())).all()
    ents = {e.id: e for e in db.scalars(select(BizEnterprise)).all()}
    batches = {b.id: b for b in db.scalars(select(BrBatch)).all()}
    import json

    out = []
    for a in rows:
        meta = {}
        if a.remark and str(a.remark).startswith("{"):
            try:
                meta = json.loads(a.remark)
            except Exception:
                meta = {}
        batch = batches.get(a.batch_id)
        out.append(
            {
                "id": a.id,
                "batchId": a.batch_id,
                "applyQty": a.apply_qty,
                "status": a.status,
                "enterpriseId": a.enterprise_id,
                "enterpriseName": ents[a.enterprise_id].name if a.enterprise_id in ents else str(a.enterprise_id),
                "regionName": "西湖区",
                "species": meta.get("species") or (batch.species if batch else "大鲵"),
                "brand": _scrub_brand(meta.get("brand") or "本地大鲵"),
                "applyDate": str(a.created_at or "")[:10],
                "auditOpinion": a.audit_opinion,
            }
        )
    return ok(out)


@router.post("/trace/applies")
def create_apply(body: ApplyIn, cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    import json

    batch = db.get(BrBatch, body.batchId or 0)
    if not batch:
        batch = db.scalars(select(BrBatch).where(BrBatch.deleted == 0)).first()
    if not batch:
        raise ApiError(40400, "批次不存在", 404)
    assert_withdrawal_ok(db, batch.id)
    meta = {k: v for k, v in {"species": body.species, "brand": body.brand}.items() if v}
    a = TrMarkApply(
        project_id=batch.project_id,
        enterprise_id=cu.user.enterprise_id or batch.enterprise_id,
        batch_id=batch.id,
        apply_qty=body.applyQty,
        status="PENDING",
        remark=json.dumps(meta, ensure_ascii=False) if meta else None,
    )
    db.add(a)
    db.flush()
    db.add(
        SysTodo(
            project_id=a.project_id,
            enterprise_id=a.enterprise_id,
            title="标识申请待审核",
            biz_type="TRACE_APPLY",
            biz_id=a.id,
            status="PENDING",
            portal="GOV",
            link_path="/gov/trace/applies",
        )
    )
    db.commit()
    db.refresh(a)
    return ok({"id": a.id})


@router.post("/trace/applies/{aid}/submit")
def submit_apply(aid: int, cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    a = db.get(TrMarkApply, aid)
    if not a or a.status not in ("DRAFT", "REJECTED"):
        raise ApiError(40900, "状态冲突")
    assert_withdrawal_ok(db, a.batch_id)
    a.status = "PENDING"
    db.add(
        SysTodo(
            project_id=a.project_id,
            enterprise_id=a.enterprise_id,
            title="标识申请待审核",
            biz_type="TRACE_APPLY",
            biz_id=a.id,
            status="PENDING",
            portal="GOV",
            link_path="/gov/trace/applies",
        )
    )
    db.commit()
    return ok(True)


@router.post("/trace/applies/{aid}/audit")
def audit_apply(aid: int, body: AuditIn, cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    if cu.portal not in ("GOV", "BOTH"):
        raise ApiError(40300, "仅区县审核", 403)
    a = db.get(TrMarkApply, aid)
    if not a or a.status != "PENDING":
        raise ApiError(40900, "状态冲突")
    a.status = "APPROVED" if body.approved else "REJECTED"
    a.audit_opinion = body.opinion
    for t in db.scalars(
        select(SysTodo).where(SysTodo.biz_type == "TRACE_APPLY", SysTodo.biz_id == aid, SysTodo.status == "PENDING")
    ):
        t.status = "DONE"
    db.commit()
    return ok(True)


@router.post("/trace/applies/{aid}/issue")
def issue_codes(aid: int, cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    if cu.portal not in ("GOV", "BOTH"):
        raise ApiError(40300, "仅区县分发", 403)
    a = db.get(TrMarkApply, aid)
    if not a or a.status != "APPROVED":
        raise ApiError(40900, "需先审核通过")
    codes = []
    for i in range(a.apply_qty):
        code_str = f"NZTRACE{a.id:04d}{i+1:04d}"
        c = TrMarkCode(
            project_id=a.project_id,
            enterprise_id=a.enterprise_id,
            apply_id=a.id,
            batch_id=a.batch_id,
            code=code_str,
            status="BOUND",
        )
        db.add(c)
        codes.append(code_str)
    a.status = "ISSUED"
    issue = TrMarkIssue(
        project_id=a.project_id,
        enterprise_id=a.enterprise_id,
        apply_id=a.id,
        issue_qty=a.apply_qty,
        start_code=codes[0] if codes else None,
        end_code=codes[-1] if codes else None,
        issued_by=cu.user.id,
    )
    db.add(issue)
    db.commit()
    return ok({"codes": codes, "issueId": issue.id})


@router.get("/trace/codes")
def list_codes(cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    q = select(TrMarkCode).where(TrMarkCode.deleted == 0)
    if cu.user.user_type == "ENTERPRISE":
        q = q.where(TrMarkCode.enterprise_id == cu.user.enterprise_id)
    rows = db.scalars(q.order_by(TrMarkCode.id.desc()).limit(200)).all()
    ents = {e.id: e.name for e in db.scalars(select(BizEnterprise)).all()}
    return ok(
        [
            {
                "id": c.id,
                "code": c.code,
                "status": c.status,
                "batchId": c.batch_id,
                "applyId": c.apply_id,
                "enterpriseId": c.enterprise_id,
                "adminCode": "610703",
                "enterpriseName": ents.get(c.enterprise_id, str(c.enterprise_id)),
                "regionName": "示范县",
                "serialCode": c.code,
                "speciesCode": "DN",
                "brand": "本地大鲵",
                "applyDate": str(c.created_at or "")[:10],
                "boundAt": str(c.bound_at or "") if getattr(c, "bound_at", None) else "",
            }
            for c in rows
        ]
    )


@router.get("/trace/issues")
def list_issues(cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    q = select(TrMarkIssue).where(TrMarkIssue.deleted == 0)
    if cu.user.project_id:
        q = q.where(TrMarkIssue.project_id == cu.user.project_id)
    rows = db.scalars(q.order_by(TrMarkIssue.id.desc())).all()
    return ok(
        [
            {
                "id": i.id,
                "applyId": i.apply_id,
                "issueQty": i.issue_qty,
                "startCode": i.start_code,
                "endCode": i.end_code,
                "enterpriseId": i.enterprise_id,
            }
            for i in rows
        ]
    )


@router.get("/trace/stats")
def trace_stats(cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    aq = select(TrMarkApply).where(TrMarkApply.deleted == 0)
    cq = select(TrMarkCode).where(TrMarkCode.deleted == 0)
    if cu.user.project_id:
        aq = aq.where(TrMarkApply.project_id == cu.user.project_id)
        cq = cq.where(TrMarkCode.project_id == cu.user.project_id)
    applies = db.scalars(aq).all()
    codes = db.scalars(cq).all()
    return ok(
        {
            "applyTotal": len(applies),
            "pending": len([a for a in applies if a.status == "PENDING"]),
            "issued": len([a for a in applies if a.status == "ISSUED"]),
            "codeTotal": len(codes),
            "bound": len([c for c in codes if c.status == "BOUND"]),
        }
    )


@router.get("/public/trace/{code}")
def public_trace(code: str, db: Session = Depends(get_db)):
    c = db.scalar(select(TrMarkCode).where(TrMarkCode.code == code, TrMarkCode.deleted == 0))
    if not c:
        raise ApiError(40400, "追溯码不存在", 404)
    batch = db.get(BrBatch, c.batch_id) if c.batch_id else None
    ent = db.get(BizEnterprise, c.enterprise_id)
    acts = []
    if batch:
        acts = db.scalars(
            select(BrActivity).where(BrActivity.batch_id == batch.id, BrActivity.deleted == 0).order_by(BrActivity.id)
        ).all()
    harvests = []
    if batch:
        harvests = db.scalars(select(BrHarvest).where(BrHarvest.batch_id == batch.id)).all()
    return ok(
        {
            "code": c.code,
            "status": c.status,
            "enterprise": {"name": ent.name if ent else None, "intro": ent.intro if ent else None},
            "batch": None
            if not batch
            else {
                "batchNo": batch.batch_no,
                "species": batch.species,
                "stockDate": str(batch.stock_date or ""),
                "status": batch.status,
                "stockQty": float(batch.stock_qty or 0),
            },
            "timeline": [
                {
                    "type": a.activity_type,
                    "title": a.title,
                    "qty": float(a.qty or 0),
                    "unit": a.unit,
                    "at": a.occurred_at.isoformat() if a.occurred_at else None,
                }
                for a in acts
            ],
            "harvests": [{"weightKg": float(h.weight_kg), "at": h.harvested_at.isoformat() if h.harvested_at else None} for h in harvests],
        }
    )
