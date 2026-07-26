from __future__ import annotations

import json
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends
from app.common.coerce import OptionalLooseStr
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.common.response import ApiError, ok
from app.db import get_db
from app.deps import CurrentUser, get_current_user
from app.models import CiSalesOrder, CiTransport

router = APIRouter(prefix="/circulation", tags=["circulation"])


def _order_meta(o: CiSalesOrder) -> dict:
    if o.remark and str(o.remark).startswith("{"):
        try:
            return json.loads(o.remark)
        except Exception:
            return {}
    return {}


def _order_row(o: CiSalesOrder) -> dict:
    meta = _order_meta(o)
    qty = float(meta.get("qty") or 0)
    price = float(meta.get("unitPrice") or 0)
    amount = float(o.amount or 0) or round(qty * price, 2)
    return {
        "id": o.id,
        "orderNo": o.order_no,
        "buyer": o.buyer or meta.get("buyer") or "-",
        "productName": meta.get("productName") or "商品大鲵",
        "qty": qty,
        "unitPrice": price,
        "amount": amount,
        "orderDate": meta.get("orderDate") or str(o.created_at or "")[:10],
        "deliverDate": meta.get("deliverDate") or "",
        "status": o.status,
        "traceHint": meta.get("traceHint") or "",
    }


@router.get("/sales-orders")
def sales_orders(cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    q = select(CiSalesOrder).where(CiSalesOrder.deleted == 0)
    if cu.user.enterprise_id:
        q = q.where(CiSalesOrder.enterprise_id == cu.user.enterprise_id)
    rows = db.scalars(q.order_by(CiSalesOrder.id.desc())).all()
    return ok([_order_row(o) for o in rows])


class OrderIn(BaseModel):
    orderNo: Optional[str] = None
    buyer: Optional[str] = None
    amount: float = 0
    productName: Optional[str] = "商品大鲵"
    qty: float = 0
    unitPrice: float = 0
    orderDate: Optional[str] = None
    deliverDate: Optional[str] = None


@router.post("/sales-orders")
def create_order(body: OrderIn, cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    qty = body.qty
    price = body.unitPrice
    amount = body.amount or round(qty * price, 2)
    order_no = body.orderNo or f"SO{date.today().strftime('%Y%m%d')}{int(date.today().toordinal()) % 1000:03d}"
    meta = {
        "productName": body.productName,
        "qty": qty,
        "unitPrice": price,
        "orderDate": body.orderDate or str(date.today()),
        "deliverDate": body.deliverDate or "",
        "buyer": body.buyer,
    }
    o = CiSalesOrder(
        project_id=cu.user.project_id or 0,
        enterprise_id=cu.user.enterprise_id or 0,
        order_no=order_no,
        buyer=body.buyer,
        amount=amount,
        status="DRAFT",
        remark=json.dumps(meta, ensure_ascii=False),
    )
    db.add(o)
    db.commit()
    db.refresh(o)
    return ok({"id": o.id})


@router.post("/sales-orders/{oid}/confirm")
def confirm_order(oid: int, cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    o = db.get(CiSalesOrder, oid)
    if not o or o.status not in ("DRAFT", "CREATED"):
        raise ApiError(40900, "状态冲突")
    o.status = "CONFIRMED"
    db.commit()
    return ok(True)


@router.post("/sales-orders/{oid}/fulfill")
def fulfill_order(oid: int, cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    o = db.get(CiSalesOrder, oid)
    if not o or o.status != "CONFIRMED":
        raise ApiError(40900, "需先确认订单")
    o.status = "DONE"
    meta = _order_meta(o)
    meta["traceHint"] = f"订单 {o.order_no} 已履约交付"
    o.remark = json.dumps(meta, ensure_ascii=False)
    # 履约时自动挂一条运输记录（对齐现网销售→流通）
    if not db.scalar(select(CiTransport).where(CiTransport.order_id == o.id).limit(1)):
        db.add(
            CiTransport(
                enterprise_id=o.enterprise_id,
                order_id=o.id,
                plate_no="陕F·待派",
                from_addr="养殖场",
                to_addr=o.buyer or "客户收货点",
                status="PENDING",
            )
        )
    db.commit()
    return ok(True)


@router.post("/sales-orders/{oid}/cancel")
def cancel_order(oid: int, cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    o = db.get(CiSalesOrder, oid)
    if not o or o.status not in ("DRAFT", "CREATED", "CONFIRMED"):
        raise ApiError(40900, "状态冲突")
    o.status = "CANCELLED"
    db.commit()
    return ok(True)


@router.get("/transports")
def transports(cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    q = select(CiTransport).where(CiTransport.deleted == 0)
    if cu.user.enterprise_id:
        q = q.where(CiTransport.enterprise_id == cu.user.enterprise_id)
    rows = db.scalars(q.order_by(CiTransport.id.desc())).all()
    orders = {o.id: o for o in db.scalars(select(CiSalesOrder)).all()}
    return ok(
        [
            {
                "id": t.id,
                "orderId": t.order_id,
                "orderNo": orders[t.order_id].order_no if t.order_id in orders else (f"SO-{t.order_id}" if t.order_id else "-"),
                "plateNo": t.plate_no,
                "fromAddr": t.from_addr,
                "toAddr": t.to_addr,
                "species": "大鲵",
                "customerName": (orders[t.order_id].buyer if t.order_id in orders else None) or "本地水产批发商",
                "transportNo": t.plate_no or f"TR-{t.id}",
                "status": t.status,
            }
            for t in rows
        ]
    )


class TransportIn(BaseModel):
    orderId: Optional[int] = None
    plateNo: OptionalLooseStr = None
    fromAddr: Optional[str] = None
    toAddr: Optional[str] = None


@router.post("/transports")
def create_transport(body: TransportIn, cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    t = CiTransport(
        enterprise_id=cu.user.enterprise_id or 0,
        order_id=body.orderId,
        plate_no=body.plateNo,
        from_addr=body.fromAddr,
        to_addr=body.toAddr,
        status="PENDING",
    )
    db.add(t)
    db.commit()
    db.refresh(t)
    return ok({"id": t.id})


@router.put("/transports/{tid}")
def update_transport(tid: int, body: TransportIn, cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    t = db.get(CiTransport, tid)
    if not t or t.deleted:
        raise ApiError(40400, "运输记录不存在", 404)
    if cu.user.enterprise_id and t.enterprise_id != cu.user.enterprise_id:
        raise ApiError(40300, "无权限", 403)
    if t.status not in ("PENDING", "DRAFT"):
        raise ApiError(40900, "仅待发车状态可编辑")
    if body.plateNo is not None:
        t.plate_no = body.plateNo
    if body.fromAddr is not None:
        t.from_addr = body.fromAddr
    if body.toAddr is not None:
        t.to_addr = body.toAddr
    if body.orderId is not None:
        t.order_id = body.orderId
    db.commit()
    return ok({"id": t.id})


@router.post("/transports/{tid}/depart")
def depart_transport(tid: int, cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    t = db.get(CiTransport, tid)
    if not t or t.status != "PENDING":
        raise ApiError(40900, "状态冲突")
    t.status = "TRANSIT"
    db.commit()
    return ok(True)


@router.post("/transports/{tid}/arrive")
def arrive_transport(tid: int, cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    t = db.get(CiTransport, tid)
    if not t or t.status not in ("PENDING", "TRANSIT"):
        raise ApiError(40900, "状态冲突")
    t.status = "DONE"
    db.commit()
    return ok(True)
