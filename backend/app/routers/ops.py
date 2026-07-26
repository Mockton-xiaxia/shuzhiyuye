from __future__ import annotations

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.common.coerce import OptionalLooseStr
from app.common.response import ApiError, ok
from app.db import get_db
from app.deps import CurrentUser, get_current_user
from app.models import (
    InItem,
    InSupplier,
    LgAfterSale,
    LgContract,
    LgCustomer,
    LgLedgerEntry,
    WmInbound,
    WmOutbound,
    WmStock,
    WmStocktake,
    WmTxn,
    WmWarehouse,
)

router = APIRouter(tags=["ops"])


class SupplierIn(BaseModel):
    name: str
    category: Optional[str] = None
    contact: Optional[str] = None
    phone: OptionalLooseStr = None


@router.get("/inputs/suppliers")
def suppliers(
    category: Optional[str] = None,
    cu: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = select(InSupplier).where(InSupplier.deleted == 0)
    if cu.user.enterprise_id:
        q = q.where(InSupplier.enterprise_id == cu.user.enterprise_id)
    if category:
        q = q.where(InSupplier.category == category)
    rows = db.scalars(q).all()
    return ok([{"id": s.id, "name": s.name, "category": s.category, "phone": s.phone, "contact": s.contact} for s in rows])


@router.post("/inputs/suppliers")
def create_supplier(body: SupplierIn, cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    s = InSupplier(
        project_id=cu.user.project_id,
        enterprise_id=cu.user.enterprise_id or 0,
        name=body.name,
        category=body.category,
        contact=body.contact,
        phone=body.phone,
    )
    db.add(s)
    db.commit()
    db.refresh(s)
    return ok({"id": s.id})


@router.get("/inputs/items")
def items(cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    q = select(InItem).where(InItem.deleted == 0)
    if cu.user.enterprise_id:
        q = q.where(InItem.enterprise_id == cu.user.enterprise_id)
    rows = db.scalars(q).all()
    return ok(
        [
            {
                "id": i.id,
                "name": i.name,
                "category": i.category,
                "unit": i.unit,
                "withdrawalDays": i.withdrawal_days,
                "supplierId": i.supplier_id,
            }
            for i in rows
        ]
    )


class ItemIn(BaseModel):
    name: str
    category: str
    unit: str = "kg"
    withdrawalDays: int = 0
    supplierId: Optional[int] = None


@router.post("/inputs/items")
def create_item(body: ItemIn, cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    i = InItem(
        project_id=cu.user.project_id,
        enterprise_id=cu.user.enterprise_id or 0,
        supplier_id=body.supplierId,
        name=body.name,
        category=body.category,
        unit=body.unit,
        withdrawal_days=body.withdrawalDays,
    )
    db.add(i)
    db.commit()
    db.refresh(i)
    return ok({"id": i.id})


class WarehouseIn(BaseModel):
    name: str
    code: Optional[str] = None


@router.get("/wms/warehouses")
def warehouses(cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    q = select(WmWarehouse).where(WmWarehouse.deleted == 0)
    if cu.user.enterprise_id:
        q = q.where(WmWarehouse.enterprise_id == cu.user.enterprise_id)
    rows = db.scalars(q).all()
    return ok([{"id": w.id, "name": w.name, "code": w.code} for w in rows])


@router.post("/wms/warehouses")
def create_warehouse(body: WarehouseIn, cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    w = WmWarehouse(
        project_id=cu.user.project_id or 0,
        enterprise_id=cu.user.enterprise_id or 0,
        name=body.name,
        code=body.code,
    )
    db.add(w)
    db.commit()
    db.refresh(w)
    return ok({"id": w.id})


def _item_map(db: Session) -> dict[int, InItem]:
    return {i.id: i for i in db.scalars(select(InItem).where(InItem.deleted == 0)).all()}


@router.get("/wms/stocks")
def stocks(
    category: Optional[str] = Query(None),
    cu: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = select(WmStock).where(WmStock.deleted == 0)
    if cu.user.enterprise_id:
        q = q.where(WmStock.enterprise_id == cu.user.enterprise_id)
    rows = db.scalars(q).all()
    items = _item_map(db)
    out = []
    for s in rows:
        it = items.get(s.item_id)
        if category and (not it or it.category != category):
            continue
        out.append(
            {
                "id": s.id,
                "warehouseId": s.warehouse_id,
                "itemId": s.item_id,
                "itemName": it.name if it else f"#{s.item_id}",
                "category": it.category if it else "",
                "qty": float(s.qty),
                "source": "自购",
                "expireDate": "2027-12-31",
            }
        )
    return ok(out)


class StockIn(BaseModel):
    warehouseId: int
    itemId: int
    qty: float


@router.post("/wms/stocks/in")
def stock_in(body: StockIn, cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    stock = db.scalar(
        select(WmStock).where(
            WmStock.warehouse_id == body.warehouseId,
            WmStock.item_id == body.itemId,
            WmStock.enterprise_id == (cu.user.enterprise_id or 0),
        )
    )
    if not stock:
        stock = WmStock(
            warehouse_id=body.warehouseId,
            enterprise_id=cu.user.enterprise_id or 0,
            item_id=body.itemId,
            qty=0,
        )
        db.add(stock)
        db.flush()
    stock.qty = float(stock.qty) + float(body.qty)
    db.add(
        WmTxn(
            warehouse_id=body.warehouseId,
            enterprise_id=cu.user.enterprise_id or 0,
            item_id=body.itemId,
            txn_type="IN",
            qty=body.qty,
        )
    )
    db.add(
        WmInbound(
            enterprise_id=cu.user.enterprise_id or 0,
            warehouse_id=body.warehouseId,
            item_id=body.itemId,
            qty=body.qty,
            status="POSTED",
            source="PURCHASE",
        )
    )
    db.commit()
    return ok({"qty": float(stock.qty)})


class CustomerIn(BaseModel):
    name: str
    phone: OptionalLooseStr = None
    address: Optional[str] = None


@router.get("/ledger/customers")
def customers(cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    q = select(LgCustomer).where(LgCustomer.deleted == 0)
    if cu.user.enterprise_id:
        q = q.where(LgCustomer.enterprise_id == cu.user.enterprise_id)
    rows = db.scalars(q).all()
    return ok([{"id": c.id, "name": c.name, "phone": c.phone, "address": c.address} for c in rows])


@router.post("/ledger/customers")
def create_customer(body: CustomerIn, cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    c = LgCustomer(
        enterprise_id=cu.user.enterprise_id or 0,
        name=body.name,
        phone=body.phone,
        address=body.address,
    )
    db.add(c)
    db.commit()
    db.refresh(c)
    return ok({"id": c.id})


class LedgerIn(BaseModel):
    title: str
    entryType: str
    amount: float
    batchId: Optional[int] = None
    customerId: Optional[int] = None
    month: Optional[str] = None
    occurredAt: Optional[date] = None


def _parse_ledger_date(body: LedgerIn) -> date:
    if body.occurredAt:
        return body.occurredAt
    if body.month and len(body.month) >= 7:
        try:
            return date.fromisoformat(f"{body.month[:7]}-01")
        except ValueError:
            pass
    return date.today()


@router.get("/ledger/entries")
def entries(cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    q = select(LgLedgerEntry).where(LgLedgerEntry.deleted == 0)
    if cu.user.enterprise_id:
        q = q.where(LgLedgerEntry.enterprise_id == cu.user.enterprise_id)
    rows = db.scalars(q.order_by(LgLedgerEntry.id.desc())).all()
    return ok(
        [
            {
                "id": e.id,
                "title": e.title,
                "entryType": e.entry_type,
                "amount": float(e.amount),
                "batchId": e.batch_id,
                "customerId": e.customer_id,
                "month": str(e.occurred_at or "")[:7] if e.occurred_at else "",
                "occurredAt": str(e.occurred_at or ""),
            }
            for e in rows
        ]
    )


@router.post("/ledger/entries")
def create_entry(body: LedgerIn, cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    e = LgLedgerEntry(
        enterprise_id=cu.user.enterprise_id or 0,
        batch_id=body.batchId,
        customer_id=body.customerId,
        entry_type=body.entryType,
        amount=body.amount,
        title=body.title,
        occurred_at=_parse_ledger_date(body),
    )
    db.add(e)
    db.commit()
    db.refresh(e)
    return ok({"id": e.id})


@router.get("/ledger/contracts")
def contracts(cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    q = select(LgContract).where(LgContract.deleted == 0)
    if cu.user.enterprise_id:
        q = q.where(LgContract.enterprise_id == cu.user.enterprise_id)
    rows = db.scalars(q).all()
    return ok(
        [
            {
                "id": c.id,
                "title": c.title,
                "customerId": c.customer_id,
                "amount": float(c.amount),
                "status": c.status,
            }
            for c in rows
        ]
    )


class ContractIn(BaseModel):
    title: str
    customerId: Optional[int] = None
    amount: float = 0


@router.post("/ledger/contracts")
def create_contract(body: ContractIn, cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    c = LgContract(
        enterprise_id=cu.user.enterprise_id or 0,
        customer_id=body.customerId,
        title=body.title,
        amount=body.amount,
    )
    db.add(c)
    db.commit()
    db.refresh(c)
    return ok({"id": c.id})


@router.get("/ledger/after-sales")
def after_sales(cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    q = select(LgAfterSale).where(LgAfterSale.deleted == 0)
    if cu.user.enterprise_id:
        q = q.where(LgAfterSale.enterprise_id == cu.user.enterprise_id)
    rows = db.scalars(q).all()
    return ok(
        [
            {
                "id": a.id,
                "title": a.title,
                "content": a.content,
                "status": a.status,
                "customerId": a.customer_id,
            }
            for a in rows
        ]
    )


class AfterSaleIn(BaseModel):
    title: str
    content: Optional[str] = None
    customerId: Optional[int] = None


@router.post("/ledger/after-sales")
def create_after_sale(body: AfterSaleIn, cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    a = LgAfterSale(
        enterprise_id=cu.user.enterprise_id or 0,
        customer_id=body.customerId,
        title=body.title,
        content=body.content,
    )
    db.add(a)
    db.commit()
    db.refresh(a)
    return ok({"id": a.id})


@router.post("/ledger/after-sales/{aid}/handle")
def handle_after_sale(aid: int, cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    a = db.get(LgAfterSale, aid)
    if not a:
        raise ApiError(40400, "记录不存在", 404)
    a.status = "DONE"
    db.commit()
    return ok(True)


@router.get("/wms/inbounds")
def inbounds(
    category: Optional[str] = Query(None),
    cu: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = select(WmInbound).where(WmInbound.deleted == 0)
    if cu.user.enterprise_id:
        q = q.where(WmInbound.enterprise_id == cu.user.enterprise_id)
    rows = db.scalars(q.order_by(WmInbound.id.desc())).all()
    items = _item_map(db)
    out = []
    for x in rows:
        it = items.get(x.item_id)
        if category and (not it or it.category != category):
            continue
        out.append(
            {
                "id": x.id,
                "warehouseId": x.warehouse_id,
                "itemId": x.item_id,
                "itemName": it.name if it else f"#{x.item_id}",
                "category": it.category if it else "",
                "qty": float(x.qty),
                "status": x.status,
                "source": x.source,
                "createdAt": x.created_at.isoformat() if x.created_at else "",
            }
        )
    return ok(out)


@router.get("/wms/outbounds")
def outbounds(
    category: Optional[str] = Query(None),
    cu: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = select(WmOutbound).where(WmOutbound.deleted == 0)
    if cu.user.enterprise_id:
        q = q.where(WmOutbound.enterprise_id == cu.user.enterprise_id)
    rows = db.scalars(q.order_by(WmOutbound.id.desc())).all()
    items = _item_map(db)
    out = []
    for x in rows:
        it = items.get(x.item_id)
        if category and (not it or it.category != category):
            continue
        out.append(
            {
                "id": x.id,
                "warehouseId": x.warehouse_id,
                "itemId": x.item_id,
                "itemName": it.name if it else f"#{x.item_id}",
                "category": it.category if it else "",
                "batchId": x.batch_id,
                "qty": float(x.qty),
                "status": x.status,
                "createdAt": x.created_at.isoformat() if x.created_at else "",
            }
        )
    return ok(out)


class InboundIn(BaseModel):
    warehouseId: Optional[int] = None
    itemId: Optional[int] = None
    itemName: Optional[str] = None
    qty: float = 1
    source: str = "PURCHASE"
    category: Optional[str] = None


@router.post("/wms/inbounds")
def create_inbound(body: InboundIn, cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    eid = cu.user.enterprise_id or 0
    wh = db.get(WmWarehouse, body.warehouseId) if body.warehouseId else db.scalar(
        select(WmWarehouse).where(WmWarehouse.enterprise_id == eid).limit(1)
    )
    if not wh:
        raise ApiError(40400, "仓库不存在", 404)
    item = db.get(InItem, body.itemId) if body.itemId else None
    if not item and body.itemName:
        item = InItem(
            enterprise_id=eid,
            project_id=cu.user.project_id,
            name=body.itemName,
            category=body.category or "FEED",
            unit="kg",
        )
        db.add(item)
        db.flush()
    if not item:
        item = db.scalar(select(InItem).where(InItem.enterprise_id == eid).limit(1))
    if not item:
        raise ApiError(40400, "物资不存在", 404)
    x = WmInbound(
        enterprise_id=eid,
        warehouse_id=wh.id,
        item_id=item.id,
        qty=body.qty,
        status="POSTED",
        source=body.source,
    )
    db.add(x)
    stock = db.scalar(
        select(WmStock).where(
            WmStock.warehouse_id == wh.id,
            WmStock.item_id == item.id,
            WmStock.enterprise_id == eid,
        )
    )
    if not stock:
        stock = WmStock(warehouse_id=wh.id, enterprise_id=eid, item_id=item.id, qty=0)
        db.add(stock)
        db.flush()
    stock.qty = float(stock.qty) + float(body.qty)
    db.commit()
    db.refresh(x)
    return ok({"id": x.id})


class OutboundIn(BaseModel):
    warehouseId: Optional[int] = None
    itemId: Optional[int] = None
    itemName: Optional[str] = None
    qty: float = 1
    batchId: Optional[int] = None
    category: Optional[str] = None


@router.post("/wms/outbounds")
def create_outbound(body: OutboundIn, cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    eid = cu.user.enterprise_id or 0
    wh = db.get(WmWarehouse, body.warehouseId) if body.warehouseId else db.scalar(
        select(WmWarehouse).where(WmWarehouse.enterprise_id == eid).limit(1)
    )
    if not wh:
        raise ApiError(40400, "仓库不存在", 404)
    item = db.get(InItem, body.itemId) if body.itemId else None
    if not item and body.itemName:
        item = db.scalar(select(InItem).where(InItem.enterprise_id == eid, InItem.name == body.itemName).limit(1))
    if not item:
        q = select(InItem).where(InItem.enterprise_id == eid)
        if body.category:
            q = q.where(InItem.category == body.category)
        item = db.scalar(q.limit(1))
    if not item:
        raise ApiError(40400, "物资不存在", 404)
    x = WmOutbound(
        enterprise_id=eid,
        warehouse_id=wh.id,
        item_id=item.id,
        batch_id=body.batchId,
        qty=body.qty,
        status="POSTED",
    )
    db.add(x)
    stock = db.scalar(
        select(WmStock).where(
            WmStock.warehouse_id == wh.id,
            WmStock.item_id == item.id,
            WmStock.enterprise_id == eid,
        )
    )
    if stock:
        stock.qty = max(0.0, float(stock.qty) - float(body.qty))
    db.commit()
    db.refresh(x)
    return ok({"id": x.id})


class StocktakeIn(BaseModel):
    warehouseId: int
    title: str


@router.get("/wms/stocktakes")
def stocktakes(cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    q = select(WmStocktake).where(WmStocktake.deleted == 0)
    if cu.user.enterprise_id:
        q = q.where(WmStocktake.enterprise_id == cu.user.enterprise_id)
    rows = db.scalars(q.order_by(WmStocktake.id.desc())).all()
    return ok(
        [
            {
                "id": x.id,
                "warehouseId": x.warehouse_id,
                "title": x.title,
                "status": x.status,
                "remark": x.remark_text,
            }
            for x in rows
        ]
    )


@router.post("/wms/stocktakes")
def create_stocktake(body: StocktakeIn, cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    x = WmStocktake(
        enterprise_id=cu.user.enterprise_id or 0,
        warehouse_id=body.warehouseId,
        title=body.title,
        status="DRAFT",
    )
    db.add(x)
    db.commit()
    db.refresh(x)
    return ok({"id": x.id})


@router.post("/wms/stocktakes/{sid}/post")
def post_stocktake(sid: int, cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    x = db.get(WmStocktake, sid)
    if not x or x.status != "DRAFT":
        raise ApiError(40900, "状态冲突")
    x.status = "POSTED"
    db.commit()
    return ok(True)
