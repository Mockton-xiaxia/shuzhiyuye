from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.common.response import ApiError, ok
from app.db import get_db
from app.deps import CurrentUser, get_current_user
from app.models import BrActivity, BrBatch, BrHarvest, BrSale, InItem, WmStock, WmTxn
from app.services.withdrawal import assert_withdrawal_ok

router = APIRouter(prefix="/breeding", tags=["breeding"])


class BatchIn(BaseModel):
    pondId: int
    batchNo: str
    species: str
    stockQty: Optional[float] = None
    stockDate: Optional[date] = None


class ActivityIn(BaseModel):
    batchId: int
    activityType: str
    title: str
    qty: Optional[float] = None
    unit: Optional[str] = None
    inputItemId: Optional[int] = None
    warehouseId: Optional[int] = None


class HarvestIn(BaseModel):
    batchId: int
    weightKg: float


@router.get("/batches")
def batches(cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    q = select(BrBatch).where(BrBatch.deleted == 0)
    if cu.user.user_type == "ENTERPRISE":
        q = q.where(BrBatch.enterprise_id == cu.user.enterprise_id)
    rows = db.scalars(q.order_by(BrBatch.id.desc())).all()
    return ok(
        [
            {
                "id": b.id,
                "batchNo": b.batch_no,
                "species": b.species,
                "pondId": b.pond_id,
                "pondName": f"塘口{b.pond_id or '-'}",
                "stockQty": float(b.stock_qty or 0),
                "stockSpec": "苗种",
                "stockDate": str(b.stock_date or ""),
                "endDate": "",
                "days": 90,
                "outSpec": "-",
                "yieldKg": float(b.harvest_kg or 0),
                "status": b.status,
                "feedTotalKg": float(b.feed_total_kg or 0),
                "harvestKg": float(b.harvest_kg or 0),
                "fcr": round(float(b.feed_total_kg or 0) / float(b.harvest_kg), 3) if b.harvest_kg else None,
            }
            for b in rows
        ]
    )


@router.post("/batches")
def create_batch(body: BatchIn, cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    b = BrBatch(
        project_id=cu.user.project_id or 0,
        enterprise_id=cu.user.enterprise_id or 0,
        pond_id=body.pondId,
        batch_no=body.batchNo,
        species=body.species,
        stock_qty=body.stockQty,
        stock_date=body.stockDate or date.today(),
        status="BREEDING",
    )
    db.add(b)
    db.commit()
    db.refresh(b)
    return ok({"id": b.id})


@router.put("/batches/{bid}")
def update_batch(bid: int, body: BatchIn, cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    b = db.get(BrBatch, bid)
    if not b or b.deleted:
        raise ApiError(40400, "批次不存在", 404)
    if cu.user.enterprise_id and b.enterprise_id != cu.user.enterprise_id:
        raise ApiError(40300, "无权限", 403)
    b.pond_id = body.pondId
    b.batch_no = body.batchNo
    b.species = body.species
    b.stock_qty = body.stockQty
    if body.stockDate:
        b.stock_date = body.stockDate
    db.commit()
    return ok({"id": b.id})


@router.get("/batches/{bid}/timeline")
def timeline(bid: int, cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    batch = db.get(BrBatch, bid)
    if not batch:
        raise ApiError(40400, "批次不存在", 404)
    acts = db.scalars(select(BrActivity).where(BrActivity.batch_id == bid).order_by(BrActivity.id)).all()
    harvests = db.scalars(select(BrHarvest).where(BrHarvest.batch_id == bid)).all()
    return ok(
        {
            "batch": {
                "id": batch.id,
                "batchNo": batch.batch_no,
                "species": batch.species,
                "status": batch.status,
                "feedTotalKg": float(batch.feed_total_kg or 0),
                "harvestKg": float(batch.harvest_kg or 0),
                "fcr": round(float(batch.feed_total_kg or 0) / float(batch.harvest_kg), 3) if batch.harvest_kg else None,
            },
            "activities": [
                {
                    "id": a.id,
                    "type": a.activity_type,
                    "title": a.title,
                    "qty": float(a.qty or 0),
                    "unit": a.unit,
                    "withdrawalUntil": str(a.withdrawal_until or ""),
                    "at": a.occurred_at.isoformat() if a.occurred_at else None,
                }
                for a in acts
            ],
            "harvests": [{"id": h.id, "weightKg": float(h.weight_kg), "at": h.harvested_at.isoformat() if h.harvested_at else None} for h in harvests],
        }
    )


@router.get("/activities")
def activities(batchId: Optional[int] = None, cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    q = select(BrActivity).where(BrActivity.deleted == 0)
    if cu.user.enterprise_id:
        q = q.where(BrActivity.enterprise_id == cu.user.enterprise_id)
    if batchId:
        q = q.where(BrActivity.batch_id == batchId)
    rows = db.scalars(q.order_by(BrActivity.id.desc()).limit(200)).all()
    return ok(
        [
            {
                "id": a.id,
                "batchId": a.batch_id,
                "activityType": a.activity_type,
                "title": a.title,
                "qty": float(a.qty or 0),
                "unit": a.unit,
                "withdrawalUntil": str(a.withdrawal_until or ""),
            }
            for a in rows
        ]
    )


@router.post("/activities")
def create_activity(body: ActivityIn, cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    batch = db.get(BrBatch, body.batchId)
    if not batch:
        raise ApiError(40400, "批次不存在", 404)
    withdrawal_days = 0
    withdrawal_until = None
    if body.inputItemId:
        item = db.get(InItem, body.inputItemId)
        if item:
            withdrawal_days = item.withdrawal_days or 0
            if withdrawal_days and body.activityType == "MEDICINE":
                withdrawal_until = date.today() + timedelta(days=withdrawal_days)
        if body.warehouseId and body.qty:
            stock = db.scalar(
                select(WmStock).where(
                    WmStock.warehouse_id == body.warehouseId,
                    WmStock.item_id == body.inputItemId,
                    WmStock.enterprise_id == batch.enterprise_id,
                )
            )
            if not stock or float(stock.qty) < float(body.qty):
                raise ApiError(40900, "库存不足")
            stock.qty = float(stock.qty) - float(body.qty)
            db.add(
                WmTxn(
                    warehouse_id=body.warehouseId,
                    enterprise_id=batch.enterprise_id,
                    item_id=body.inputItemId,
                    batch_id=batch.id,
                    txn_type="OUT",
                    qty=body.qty,
                )
            )
    a = BrActivity(
        project_id=batch.project_id,
        enterprise_id=batch.enterprise_id,
        batch_id=batch.id,
        pond_id=batch.pond_id,
        activity_type=body.activityType,
        title=body.title,
        qty=body.qty,
        unit=body.unit,
        input_item_id=body.inputItemId,
        withdrawal_days=withdrawal_days,
        withdrawal_until=withdrawal_until,
        occurred_at=datetime.now(timezone.utc),
    )
    db.add(a)
    if body.activityType == "FEED" and body.qty:
        batch.feed_total_kg = float(batch.feed_total_kg or 0) + float(body.qty)
    db.commit()
    db.refresh(a)
    return ok({"id": a.id, "withdrawalUntil": str(withdrawal_until or "")})


class ActivityUpdateIn(BaseModel):
    title: Optional[str] = None
    activityType: Optional[str] = None
    qty: Optional[float] = None
    unit: Optional[str] = None


@router.put("/activities/{aid}")
def update_activity(aid: int, body: ActivityUpdateIn, cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    a = db.get(BrActivity, aid)
    if not a or a.deleted:
        raise ApiError(40400, "农事记录不存在", 404)
    if cu.user.enterprise_id and a.enterprise_id != cu.user.enterprise_id:
        raise ApiError(40300, "无权限", 403)
    if body.title is not None:
        a.title = body.title
    if body.activityType is not None:
        a.activity_type = body.activityType
    if body.qty is not None:
        a.qty = body.qty
    if body.unit is not None:
        a.unit = body.unit
    db.commit()
    return ok({"id": a.id})


@router.post("/harvests")
def harvest(body: HarvestIn, cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    batch = db.get(BrBatch, body.batchId)
    if not batch:
        raise ApiError(40400, "批次不存在", 404)
    assert_withdrawal_ok(db, body.batchId)
    h = BrHarvest(
        project_id=batch.project_id,
        enterprise_id=batch.enterprise_id,
        batch_id=batch.id,
        weight_kg=body.weightKg,
        harvested_at=datetime.now(timezone.utc),
    )
    db.add(h)
    batch.harvest_kg = float(batch.harvest_kg or 0) + float(body.weightKg)
    batch.status = "HARVESTED"
    db.commit()
    db.refresh(h)
    return ok({"id": h.id, "fcr": round(float(batch.feed_total_kg or 0) / float(batch.harvest_kg), 3) if batch.harvest_kg else None})


class SaleIn(BaseModel):
    batchId: Optional[int] = None
    customerName: Optional[str] = None
    species: Optional[str] = None
    weightKg: float = 0
    amount: float = 0
    soldAt: Optional[date] = None


@router.get("/sales")
def sales(cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    q = select(BrSale).where(BrSale.deleted == 0)
    if cu.user.enterprise_id:
        q = q.where(BrSale.enterprise_id == cu.user.enterprise_id)
    rows = db.scalars(q.order_by(BrSale.id.desc())).all()
    return ok(
        [
            {
                "id": s.id,
                "batchId": s.batch_id,
                "orderNo": f"SO{s.id:06d}",
                "customerName": s.customer_name,
                "species": s.species,
                "orderType": "销售",
                "weightKg": float(s.weight_kg),
                "amount": float(s.amount),
                "soldAt": str(s.sold_at or ""),
                "status": s.status,
            }
            for s in rows
        ]
    )


@router.post("/sales")
def create_sale(body: SaleIn, cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    s = BrSale(
        project_id=cu.user.project_id or 0,
        enterprise_id=cu.user.enterprise_id or 0,
        batch_id=body.batchId,
        customer_name=body.customerName,
        species=body.species,
        weight_kg=body.weightKg,
        amount=body.amount,
        sold_at=body.soldAt or date.today(),
    )
    db.add(s)
    db.commit()
    db.refresh(s)
    return ok({"id": s.id})


@router.put("/sales/{sid}")
def update_sale(sid: int, body: SaleIn, cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    s = db.get(BrSale, sid)
    if not s or s.deleted:
        raise ApiError(40400, "销售记录不存在", 404)
    if cu.user.enterprise_id and s.enterprise_id != cu.user.enterprise_id:
        raise ApiError(40300, "无权限", 403)
    if body.customerName is not None:
        s.customer_name = body.customerName
    if body.species is not None:
        s.species = body.species
    s.weight_kg = body.weightKg
    s.amount = body.amount
    if body.soldAt:
        s.sold_at = body.soldAt
    if body.batchId is not None:
        s.batch_id = body.batchId
    db.commit()
    return ok({"id": s.id})
