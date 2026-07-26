# -*- coding: utf-8 -*-
"""补齐现网对照所需的列表接口（演示数据 + 尽量挂接现库）。"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.common.response import ok
from app.db import get_db
from app.deps import CurrentUser, get_current_user
from app.models import LgCustomer, SpecialtySalamander, TrMarkCode

router = APIRouter(tags=["feature-fill"])


def _now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


@router.get("/quality/stats-records")
def quality_stats_records(cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    return ok(
        [
            {
                "id": 1,
                "year": 2026,
                "quarter": "Q1",
                "regionName": "示范县",
                "level": "区级",
                "enterpriseCount": 1,
                "sampleCount": 3,
                "passCount": 2,
                "failCount": 1,
            }
        ]
    )


@router.get("/trace/label-stats")
def trace_label_stats(cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.scalars(select(TrMarkCode).where(TrMarkCode.deleted == 0).limit(50)).all()
    if not rows:
        return ok(
            [
                {
                    "id": 1,
                    "labelCode": "NZTRACE20260001",
                    "enterpriseName": "示范养殖场",
                    "species": "大鲵",
                    "customer": "本地批发",
                    "dest": "示范市",
                    "saleDate": "2026-06-01",
                    "genDate": "2026-05-20",
                    "status": "BOUND",
                }
            ]
        )
    return ok(
        [
            {
                "id": c.id,
                "labelCode": c.code,
                "enterpriseName": str(c.enterprise_id),
                "species": "-",
                "customer": "-",
                "dest": "-",
                "saleDate": "",
                "genDate": str(c.created_at or "")[:10],
                "status": c.status,
            }
            for c in rows
        ]
    )


@router.get("/effluent/policies")
def effluent_policies(cu: CurrentUser = Depends(get_current_user)):
    return ok([{"id": 1, "name": "示范县尾水排放管理办法", "scope": "示范县全域", "publishDate": "2026-01-01"}])


@router.post("/effluent/policies")
def create_effluent_policy(body: dict, cu: CurrentUser = Depends(get_current_user)):
    return ok({"id": 2, **body})


@router.put("/effluent/policies/{pid}")
def update_effluent_policy(pid: int, body: dict, cu: CurrentUser = Depends(get_current_user)):
    return ok({"id": pid, **body})


@router.get("/specialty/disease-tests")
def disease_tests(cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.scalars(select(SpecialtySalamander).limit(20)).all()
    if rows:
        return ok(
            [
                {
                    "id": r.id,
                    "applyNo": f"DT{r.id:04d}",
                    "applyDate": str(r.created_at or "")[:10],
                    "applicant": "张示范",
                    "sampleSource": r.title or "1号塘",
                    "purpose": r.content or "常规检测",
                    "status": r.status or "DONE",
                }
                for r in rows
            ]
        )
    return ok(
        [
            {
                "id": 1,
                "applyNo": "DT0001",
                "applyDate": "2026-06-01",
                "applicant": "张示范",
                "sampleSource": "1号塘",
                "purpose": "常规检测",
                "status": "DONE",
            }
        ]
    )


@router.post("/specialty/disease-tests")
def create_disease_test(body: dict, cu: CurrentUser = Depends(get_current_user)):
    return ok({"id": 99, **body, "status": "PENDING"})


@router.get("/specialty/domestication-plots")
def domestication_plots_legacy(cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    from app.models import SpDomesticationPlot
    from app.routers.domestication import _plot_dict

    q = select(SpDomesticationPlot).where(SpDomesticationPlot.deleted == 0, SpDomesticationPlot.plot_type == "PADDY")
    if cu.user.project_id:
        q = q.where(SpDomesticationPlot.project_id == cu.user.project_id)
    rows = db.scalars(q.order_by(SpDomesticationPlot.id.desc())).all()
    return ok([_plot_dict(p) for p in rows])


@router.post("/specialty/domestication-plots")
def create_plot_legacy(body: dict, cu: CurrentUser = Depends(get_current_user)):
    return ok({"id": 3, **body})


@router.get("/specialty/domestication-logs")
def domestication_logs_legacy(cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    from app.models import SpDomesticationLog
    from app.routers.domestication import _log_dict

    q = select(SpDomesticationLog).where(SpDomesticationLog.deleted == 0)
    if cu.user.enterprise_id:
        q = q.where(SpDomesticationLog.enterprise_id == cu.user.enterprise_id)
    rows = db.scalars(q.order_by(SpDomesticationLog.id.desc())).all()
    return ok([_log_dict(l) for l in rows])


@router.post("/specialty/domestication-logs")
def create_dom_log(body: dict, cu: CurrentUser = Depends(get_current_user)):
    return ok({"id": 3, **body})


@router.get("/specialty/processing")
def processing(cu: CurrentUser = Depends(get_current_user)):
    return ok(
        [
            {
                "id": 1,
                "materialNo": "M2026001",
                "purchaseDate": "2026-06-01",
                "pondName": "1号塘",
                "weightKg": 120,
                "quarantineStatus": "合格",
            }
        ]
    )


@router.post("/specialty/processing")
def create_processing(body: dict, cu: CurrentUser = Depends(get_current_user)):
    return ok({"id": 2, **body})


@router.get("/specialty/transports")
def specialty_transports(cu: CurrentUser = Depends(get_current_user)):
    return ok(
        [
            {
                "id": 1,
                "transportNo": "TP2026001",
                "fromAddr": "示范镇",
                "toAddr": "示范市",
                "tempC": 8,
                "durationH": 2.5,
                "sampleStatus": "合格",
            }
        ]
    )


@router.post("/specialty/transports")
def create_specialty_transport(body: dict, cu: CurrentUser = Depends(get_current_user)):
    return ok({"id": 2, **body})


@router.get("/iot/water-lab")
def water_lab(cu: CurrentUser = Depends(get_current_user)):
    return ok(
        [
            {
                "id": 1,
                "permanganate": 3.2,
                "nitrite": 0.02,
                "ammonia": 0.15,
                "alkalinity": 80,
                "salinity": 0.1,
                "ss": 12,
                "flagellate": 0,
                "diatom": 1,
                "cyanobacteria": 0,
                "protozoa": 0,
                "sampledAt": _now(),
            }
        ]
    )


@router.get("/iot/weather")
def iot_weather(cu: CurrentUser = Depends(get_current_user)):
    return ok(
        [
            {
                "id": 1,
                "sampledAt": _now(),
                "tempC": 31,
                "windDir": "西南",
                "windLevel": "4-5",
                "humidity": 54,
                "condition": "晴",
            }
        ]
    )


@router.get("/ledger/fees")
def ledger_fees(cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    customers = db.scalars(select(LgCustomer).where(LgCustomer.deleted == 0)).all()
    if not customers:
        return ok(
            [{"id": 1, "customerName": "本地水产批发商", "contractCount": 1, "totalAmount": 10000, "paid": 3000, "feeStatus": "部分付款"}]
        )
    return ok(
        [
            {
                "id": c.id,
                "customerName": c.name,
                "contractCount": 1,
                "totalAmount": 10000,
                "paid": 3000,
                "feeStatus": "部分付款",
            }
            for c in customers
        ]
    )


@router.get("/ledger/purchase-history")
def purchase_history(cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    customers = db.scalars(select(LgCustomer).where(LgCustomer.deleted == 0)).all()
    return ok(
        [
            {
                "id": c.id,
                "customerName": c.name,
                "orderCount": 2,
                "totalAmount": 5600,
                "lastOrderAt": "2026-06-10",
            }
            for c in customers
        ]
        or [{"id": 1, "customerName": "本地水产批发商", "orderCount": 2, "totalAmount": 5600, "lastOrderAt": "2026-06-10"}]
    )


@router.get("/ledger/analysis")
def ledger_analysis(cu: CurrentUser = Depends(get_current_user)):
    return ok(
        {
            "list": [
                {"id": 1, "month": "2026-05", "income": 20000, "cost": 12000, "profit": 8000},
                {"id": 2, "month": "2026-06", "income": 25000, "cost": 14000, "profit": 11000},
                {"id": 3, "month": "2026-07", "income": 28000, "cost": 15500, "profit": 12500},
            ],
            "months": ["2026-05", "2026-06", "2026-07"],
            "income": [20000, 25000, 28000],
            "cost": [12000, 14000, 15500],
            "profit": [8000, 11000, 12500],
            "costShare": [
                {"name": "饲料", "value": 8500},
                {"name": "人工", "value": 4200},
                {"name": "苗种", "value": 1500},
                {"name": "渔药", "value": 700},
                {"name": "其他", "value": 2600},
            ],
        }
    )


@router.get("/ledger/portrait")
def ledger_portrait(cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    customers = db.scalars(select(LgCustomer).where(LgCustomer.deleted == 0)).all()
    if not customers:
        customers = []
    items = []
    for i, c in enumerate(customers or [None]):
        name = c.name if c else "本地水产批发商"
        cid = c.id if c else 1
        items.append(
            {
                "id": cid,
                "customerName": name,
                "phone": (c.phone if c else "13900000000"),
                "address": (c.address if c else "示范市"),
                "level": "A级" if i == 0 else "B级",
                "totalOrders": 5 + i,
                "totalAmount": 56000 - i * 8000,
                "paidAmount": 42000 - i * 5000,
                "unpaidAmount": 14000 - i * 3000,
                "lastOrderAt": "2026-07-10",
                "tags": ["稳定客户", "大宗采购"] if i == 0 else ["新客户"],
                "timeline": [
                    {"date": "2026-07-10", "event": "销售出库", "amount": 8600},
                    {"date": "2026-06-18", "event": "合同续签", "amount": 50000},
                    {"date": "2026-05-02", "event": "售后处理完成", "amount": 0},
                ],
            }
        )
    return ok(items)


class BatchDeleteIn(BaseModel):
    api: str
    ids: list[int]


@router.post("/feature/batch-delete")
def feature_batch_delete(body: BatchDeleteIn, cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    """通用软删除：按 API 路径映射到模型。"""
    from app.models import (
        BizPond,
        BizStaff,
        BrActivity,
        BrBatch,
        BrSale,
        CiTransport,
        CmsArticle,
        DiAlert,
        EfPatrol,
        InItem,
        InSupplier,
        IotCamera,
        IotRule,
        LgAfterSale,
        LgContract,
        LgCustomer,
        LgLedgerEntry,
        QaInspection,
        QaLab,
        QaPolicy,
        SpecialtySalamander,
        SuListing,
        SuPrice,
        WmInbound,
        WmOutbound,
        WmStock,
        WmStocktake,
        WmWarehouse,
    )

    path = (body.api or "").split("?")[0].rstrip("/")
    mapping = {
        "/quality/inspections": QaInspection,
        "/quality/policies": QaPolicy,
        "/quality/labs": QaLab,
        "/quality/self-checks": None,
        "/party/staffs": BizStaff,
        "/party/ponds": BizPond,
        "/inputs/suppliers": InSupplier,
        "/inputs/items": InItem,
        "/breeding/batches": BrBatch,
        "/breeding/activities": BrActivity,
        "/breeding/sales": BrSale,
        "/ledger/customers": LgCustomer,
        "/ledger/contracts": LgContract,
        "/ledger/after-sales": LgAfterSale,
        "/ledger/entries": LgLedgerEntry,
        "/wms/warehouses": WmWarehouse,
        "/wms/stocks": WmStock,
        "/wms/inbounds": WmInbound,
        "/wms/outbounds": WmOutbound,
        "/wms/stocktakes": WmStocktake,
        "/circulation/transports": CiTransport,
        "/iot/rules": IotRule,
        "/iot/cameras": IotCamera,
        "/disease/alerts": DiAlert,
        "/effluent/patrols": EfPatrol,
        "/specialty/disease-tests": SpecialtySalamander,
        "/supply/prices": SuPrice,
        "/supply/listings": SuListing,
        "/cms/articles": CmsArticle,
    }
    model = mapping.get(path)
    n = 0
    if model is None and path.endswith("/self-checks"):
        from app.models import QaSelfCheck

        model = QaSelfCheck
    if model is None:
        return ok({"count": 0, "message": "该资源演示删除（前端已移除选中行）", "soft": True})
    for i in body.ids or []:
        row = db.get(model, int(i))
        if row and hasattr(row, "deleted"):
            row.deleted = 1
            n += 1
    db.commit()
    return ok({"count": n})


class FeatureUpdateIn(BaseModel):
    api: str
    id: int
    data: dict


_DISPLAY_ONLY_KEYS = {
    "roleName", "orgName", "projectName", "source", "createdAt", "updatedAt",
    "regionName", "enterpriseName", "labType", "subjectType", "inspectedAt",
    "fileName", "scope", "zone", "customerName", "supplierName", "orderNo",
    "transportNo", "applyNo", "applyDate", "applicant", "genDate", "saleDate",
}


def _coerce_value(key: str, val):
    if val is None or val == "":
        return val
    if key in {"mobile", "phone", "contactPhone", "idCard", "plateNo", "username", "deviceSerial"}:
        return str(val)
    if isinstance(val, str) and val.isdigit() and key.endswith("Id"):
        return int(val)
    return val


@router.put("/feature/update")
def feature_update(body: FeatureUpdateIn, cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    """通用编辑：CrudPage 对无专用 PUT 的资源走此接口。"""
    from app.models import (
        BizPond,
        BizStaff,
        BrActivity,
        BrBatch,
        BrSale,
        CiTransport,
        CmsArticle,
        CmsCategory,
        CmsVideo,
        DiAlert,
        EfPatrol,
        EfWaterBody,
        InItem,
        InSupplier,
        IotCamera,
        IotRule,
        LgAfterSale,
        LgContract,
        LgCustomer,
        LgLedgerEntry,
        QaInspection,
        QaLab,
        QaPolicy,
        SpecialtySalamander,
        SuListing,
        SuMarket,
        SuPrice,
        WmInbound,
        WmOutbound,
        WmStock,
        WmStocktake,
        WmWarehouse,
    )

    path = (body.api or "").split("?")[0].rstrip("/")
    rules: dict[str, tuple] = {
        "/quality/labs": (QaLab, {"name": "name", "contact": "contact", "phone": "phone", "lng": "lng", "lat": "lat"}),
        "/quality/policies": (QaPolicy, {"name": "name", "fileUrl": "file_url", "publishDate": "publish_date"}),
        "/supply/listings": (
            SuListing,
            {"title": "title", "supplierName": "supplier_name", "contact": "contact", "phone": "phone", "brand": "brand", "region": "region", "price": "price", "category": "category"},
        ),
        "/supply/markets": (SuMarket, {"name": "name", "region": "region", "lng": "lng", "lat": "lat"}),
        "/supply/prices": (SuPrice, {"species": "species", "spec": "spec", "price": "price", "unit": "unit"}),
        "/effluent/waters": (EfWaterBody, {"name": "name", "code": "code", "level": "level", "zone": "name"}),
        "/cms/articles": (CmsArticle, {"title": "title", "content": "content", "category": "category"}),
        "/cms/categories": (CmsCategory, {"name": "name", "sortNo": "sort_no"}),
        "/cms/videos": (CmsVideo, {"title": "title", "category": "category", "url": "url", "published": "published"}),
        "/inputs/items": (InItem, {"name": "name", "category": "category", "unit": "unit", "withdrawalDays": "withdrawal_days"}),
        "/inputs/suppliers": (InSupplier, {"name": "name", "category": "category", "contact": "contact", "phone": "phone"}),
        "/party/staffs": (BizStaff, {"name": "name", "phone": "phone", "post": "post", "status": "status"}),
        "/breeding/batches": (BrBatch, {"batchNo": "batch_no", "species": "species", "stockQty": "stock_qty", "stockDate": "stock_date", "pondId": "pond_id"}),
        "/breeding/activities": (BrActivity, {"title": "title", "activityType": "activity_type", "qty": "qty", "unit": "unit"}),
        "/breeding/sales": (BrSale, {"customerName": "customer_name", "species": "species", "weightKg": "weight_kg", "amount": "amount", "soldAt": "sold_at"}),
        "/ledger/customers": (LgCustomer, {"name": "name", "phone": "phone", "address": "address"}),
        "/ledger/contracts": (LgContract, {"title": "title", "amount": "amount"}),
        "/ledger/after-sales": (LgAfterSale, {"title": "title", "content": "content"}),
        "/ledger/entries": (LgLedgerEntry, {"title": "title", "entryType": "entry_type", "amount": "amount", "month": "occurred_at", "occurredAt": "occurred_at"}),
        "/wms/warehouses": (WmWarehouse, {"name": "name", "code": "code"}),
        "/wms/stocks": (WmStock, {"qty": "qty"}),
        "/wms/inbounds": (WmInbound, {"qty": "qty", "source": "source", "status": "status"}),
        "/wms/outbounds": (WmOutbound, {"qty": "qty", "status": "status"}),
        "/wms/stocktakes": (WmStocktake, {"title": "title"}),
        "/circulation/transports": (CiTransport, {"plateNo": "plate_no", "fromAddr": "from_addr", "toAddr": "to_addr"}),
        "/iot/rules": (IotRule, {"name": "name", "pointCode": "point_code", "operator": "operator", "threshold": "threshold", "enabled": "enabled"}),
        "/iot/cameras": (IotCamera, {"name": "name", "deviceSerial": "device_serial", "scene": "scene", "status": "status"}),
        "/disease/alerts": (DiAlert, {"title": "title", "level": "level", "content": "content"}),
        "/effluent/patrols": (EfPatrol, {"title": "title", "result": "result"}),
        "/specialty/disease-tests": (SpecialtySalamander, {"title": "title", "content": "content", "status": "status"}),
        "/quality/inspections": (
            QaInspection,
            {"title": "title", "species": "species", "quarter": "quarter", "level": "level", "result": "result", "year": "year", "status": "status"},
        ),
        "/party/ponds": (BizPond, {"name": "name", "code": "code", "pondType": "pond_type", "species": "species", "township": "township", "areaMu": "area_mu"}),
    }
    rule = rules.get(path)
    if not rule:
        return ok({"id": body.id, "message": "演示环境已接收（该资源无持久化字段映射）", "soft": True})
    model, field_map = rule
    row = db.get(model, int(body.id))
    if not row or getattr(row, "deleted", 0):
        return ok({"id": body.id, "message": "记录不存在或已删除", "soft": True})
    data = body.data or {}
    for src, dst in field_map.items():
        if src not in data or data[src] in (None, ""):
            continue
        if not hasattr(row, dst):
            continue
        val = _coerce_value(src if src in {"mobile", "phone", "contactPhone", "idCard", "plateNo"} else dst, data[src])
        if dst == "publish_date" and isinstance(val, str):
            from datetime import date as date_cls
            val = date_cls.fromisoformat(val[:10])
        if dst in ("stock_date", "sold_at", "occurred_at") and isinstance(val, str) and val:
            from datetime import date as date_cls
            if dst == "occurred_at" and len(val) == 7 and val[4] == "-":
                val = date_cls.fromisoformat(f"{val}-01")
            else:
                val = date_cls.fromisoformat(val[:10])
        setattr(row, dst, val)
    db.commit()
    return ok({"id": body.id})


@router.get("/ledger/budgets")
def ledger_budgets(cu: CurrentUser = Depends(get_current_user)):
    """手工记账/预算管理：月度成本预算（演示）。"""
    return ok(
        [
            {
                "id": 1,
                "month": "2026-06",
                "seed": 2000,
                "feed": 8000,
                "medicine": 600,
                "rent": 1500,
                "power": 900,
                "water": 300,
                "labor": 4000,
                "other": 500,
                "total": 17800,
            },
            {
                "id": 2,
                "month": "2026-07",
                "seed": 1500,
                "feed": 8500,
                "medicine": 700,
                "rent": 1500,
                "power": 1100,
                "water": 350,
                "labor": 4200,
                "other": 600,
                "total": 18450,
            },
        ]
    )


class BudgetIn(BaseModel):
    month: str = "2026-07"
    seed: float = 0
    feed: float = 0
    medicine: float = 0
    rent: float = 0
    power: float = 0
    water: float = 0
    labor: float = 0
    other: float = 0


@router.post("/ledger/budgets")
def create_budget(body: BudgetIn, cu: CurrentUser = Depends(get_current_user)):
    total = body.seed + body.feed + body.medicine + body.rent + body.power + body.water + body.labor + body.other
    return ok({"id": 99, **body.model_dump(), "total": total})


@router.get("/wms/warehouse-equip")
def warehouse_equip(cu: CurrentUser = Depends(get_current_user)):
    return ok([{"id": 1, "name": "冷库温控", "warehouseName": "饲料仓", "status": "ONLINE"}])


@router.get("/feature/demo")
def feature_demo(cu: CurrentUser = Depends(get_current_user)):
    return ok([{"id": 1, "name": "演示数据", "status": "OK"}])
