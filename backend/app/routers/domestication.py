from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.common.response import ApiError, ok
from app.db import get_db
from app.deps import CurrentUser, get_current_user
from app.models import SpDomesticationLog, SpDomesticationPlot

router = APIRouter(prefix="/specialty/domestication", tags=["domestication"])


def _next_code(db: Session, prefix: str, model) -> str:
    year = datetime.now().year
    pat = f"{prefix}{year}%"
    n = db.scalar(select(func.count()).select_from(model).where(model.code.like(pat))) or 0
    return f"{prefix}{year}{n + 1:04d}"


def _status_label(s: str) -> str:
    return {"GROWING": "生长中", "HARVESTED": "已收获", "FALLOW": "休耕"}.get(s, s)


def _plot_dict(p: SpDomesticationPlot) -> dict:
    income = float(p.income or 0)
    cost = float(p.cost or 0)
    profit = float(p.profit if p.profit is not None else income - cost)
    return {
        "id": p.id,
        "plotType": p.plot_type,
        "code": p.code,
        "name": p.code,
        "areaMu": float(p.area_mu or 0),
        "cropSpecies": p.crop_species,
        "fishSpecies": p.fish_species,
        "species": p.crop_species,
        "plantDate": p.plant_date.isoformat() if p.plant_date else None,
        "status": p.status,
        "statusLabel": _status_label(p.status),
        "soilDesc": p.soil_desc,
        "irrigation": p.irrigation,
        "cost": cost,
        "yieldKg": float(p.yield_kg or 0),
        "riceYieldKg": float(p.rice_yield_kg or 0),
        "fishYieldKg": float(p.fish_yield_kg or 0),
        "income": income,
        "profit": profit,
        "stockingKg": float(p.stocking_kg or 0),
    }


class PlotIn(BaseModel):
    plotType: str = "PADDY"
    areaMu: Optional[float] = None
    cropSpecies: Optional[str] = None
    fishSpecies: Optional[str] = None
    plantDate: Optional[date] = None
    status: Optional[str] = "GROWING"
    soilDesc: Optional[str] = None
    irrigation: Optional[str] = None
    cost: Optional[float] = None
    yieldKg: Optional[float] = None
    riceYieldKg: Optional[float] = None
    fishYieldKg: Optional[float] = None
    income: Optional[float] = None
    profit: Optional[float] = None
    stockingKg: Optional[float] = None


class LogIn(BaseModel):
    logDate: Optional[date] = None
    pondCode: Optional[str] = None
    baitType: Optional[str] = None
    feedKg: Optional[float] = None
    effect: Optional[str] = None


def _log_dict(l: SpDomesticationLog) -> dict:
    return {
        "id": l.id,
        "code": l.code,
        "logDate": l.log_date.isoformat() if l.log_date else None,
        "date": l.log_date.isoformat() if l.log_date else None,
        "pondCode": l.pond_code,
        "pondName": l.pond_code,
        "baitType": l.bait_type,
        "feedType": l.bait_type,
        "feedKg": float(l.feed_kg or 0),
        "feedQty": float(l.feed_kg or 0),
        "effect": l.effect,
    }


def _apply_plot(p: SpDomesticationPlot, body: PlotIn) -> None:
    p.area_mu = body.areaMu
    p.crop_species = body.cropSpecies
    p.fish_species = body.fishSpecies
    p.plant_date = body.plantDate
    p.status = body.status or "GROWING"
    p.soil_desc = body.soilDesc
    p.irrigation = body.irrigation
    p.cost = body.cost
    p.yield_kg = body.yieldKg
    p.rice_yield_kg = body.riceYieldKg
    p.fish_yield_kg = body.fishYieldKg
    p.income = body.income
    p.stocking_kg = body.stockingKg
    income = float(body.income or 0)
    cost = float(body.cost or 0)
    p.profit = body.profit if body.profit is not None else (income - cost if income or cost else None)


@router.get("/stats")
def domestication_stats(cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    pid = cu.user.project_id or 0
    q = select(SpDomesticationPlot).where(SpDomesticationPlot.deleted == 0, SpDomesticationPlot.project_id == pid)
    plots = db.scalars(q).all()
    today_feed = db.scalar(
        select(func.coalesce(func.sum(SpDomesticationLog.feed_kg), 0)).where(
            SpDomesticationLog.deleted == 0,
            SpDomesticationLog.project_id == pid,
            SpDomesticationLog.log_date == date.today(),
        )
    ) or 0
    good = sum(1 for l in db.scalars(select(SpDomesticationLog).where(SpDomesticationLog.deleted == 0)).all() if (l.effect or "") in ("良好", "好", "优秀"))
    total_logs = db.scalar(select(func.count()).select_from(SpDomesticationLog).where(SpDomesticationLog.deleted == 0)) or 0
    return ok(
        {
            "stockCount": len(plots) * 120,
            "adultCount": len(plots) * 80,
            "juvenileCount": len(plots) * 40,
            "todayFeedKg": float(today_feed),
            "yesterdayFeedKg": float(today_feed) * 0.9,
            "successRate": round(good / total_logs * 100, 1) if total_logs else 0,
            "pendingCount": sum(1 for p in plots if p.status == "GROWING"),
        }
    )


@router.get("/plots")
def list_plots(
    plotType: Optional[str] = Query(None, alias="plotType"),
    keyword: Optional[str] = None,
    cu: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = select(SpDomesticationPlot).where(SpDomesticationPlot.deleted == 0)
    if cu.user.project_id:
        q = q.where(SpDomesticationPlot.project_id == cu.user.project_id)
    if plotType:
        q = q.where(SpDomesticationPlot.plot_type == plotType)
    if keyword:
        q = q.where(SpDomesticationPlot.code.contains(keyword) | SpDomesticationPlot.crop_species.contains(keyword))
    rows = db.scalars(q.order_by(SpDomesticationPlot.id.desc())).all()
    return ok({"list": [_plot_dict(p) for p in rows], "total": len(rows)})


@router.post("/plots")
def create_plot(body: PlotIn, cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    prefix = "DK" if body.plotType == "PADDY" else "YD"
    p = SpDomesticationPlot(
        project_id=cu.user.project_id or 0,
        enterprise_id=cu.user.enterprise_id,
        plot_type=body.plotType,
        code=_next_code(db, prefix, SpDomesticationPlot),
    )
    _apply_plot(p, body)
    db.add(p)
    db.commit()
    db.refresh(p)
    return ok(_plot_dict(p))


@router.put("/plots/{pid}")
def update_plot(pid: int, body: PlotIn, cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    p = db.get(SpDomesticationPlot, pid)
    if not p or p.deleted:
        raise ApiError(40400, "地块不存在", 404)
    _apply_plot(p, body)
    db.commit()
    return ok(_plot_dict(p))


@router.delete("/plots/{pid}")
def delete_plot(pid: int, cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    p = db.get(SpDomesticationPlot, pid)
    if not p or p.deleted:
        raise ApiError(40400, "地块不存在", 404)
    p.deleted = 1
    db.commit()
    return ok(True)


@router.get("/economics")
def domestication_economics(cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    q = select(SpDomesticationPlot).where(SpDomesticationPlot.deleted == 0)
    if cu.user.project_id:
        q = q.where(SpDomesticationPlot.project_id == cu.user.project_id)
    plots = db.scalars(q).all()

    def agg(ptype: str) -> dict:
        items = [p for p in plots if p.plot_type == ptype]
        area = sum(float(p.area_mu or 0) for p in items)
        cost = sum(float(p.cost or 0) for p in items)
        income = sum(float(p.income or 0) for p in items)
        profit = sum(float(p.profit or 0) if p.profit is not None else float(p.income or 0) - float(p.cost or 0) for p in items)
        yield_kg = sum(float(p.yield_kg or 0) + float(p.rice_yield_kg or 0) + float(p.fish_yield_kg or 0) for p in items)
        return {
            "areaMu": round(area, 2),
            "yieldKg": round(yield_kg, 2),
            "cost": round(cost, 2),
            "income": round(income, 2),
            "profit": round(profit, 2),
            "costPerMu": round(cost / area, 2) if area else 0,
            "incomePerMu": round(income / area, 2) if area else 0,
        }

    paddy = agg("PADDY")
    rice_fish = agg("RICE_FISH")
    return ok(
        {
            "paddy": paddy,
            "riceFish": rice_fish,
            "chart": {
                "categories": ["纯稻", "渔稻共生"],
                "cost": [paddy["cost"], rice_fish["cost"]],
                "income": [paddy["income"], rice_fish["income"]],
                "profit": [paddy["profit"], rice_fish["profit"]],
            },
        }
    )


@router.get("/logs")
def list_logs(
    keyword: Optional[str] = None,
    cu: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = select(SpDomesticationLog).where(SpDomesticationLog.deleted == 0)
    if cu.user.project_id:
        q = q.where(SpDomesticationLog.project_id == cu.user.project_id)
    if cu.user.user_type == "ENTERPRISE" and cu.user.enterprise_id:
        q = q.where(SpDomesticationLog.enterprise_id == cu.user.enterprise_id)
    if keyword:
        q = q.where(SpDomesticationLog.code.contains(keyword) | SpDomesticationLog.pond_code.contains(keyword))
    rows = db.scalars(q.order_by(SpDomesticationLog.id.desc())).all()
    return ok({"list": [_log_dict(l) for l in rows], "total": len(rows)})


@router.post("/logs")
def create_log(body: LogIn, cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    l = SpDomesticationLog(
        project_id=cu.user.project_id or 0,
        enterprise_id=cu.user.enterprise_id,
        code=_next_code(db, "XH", SpDomesticationLog),
        log_date=body.logDate,
        pond_code=body.pondCode,
        bait_type=body.baitType,
        feed_kg=body.feedKg,
        effect=body.effect,
    )
    db.add(l)
    db.commit()
    db.refresh(l)
    return ok(_log_dict(l))


@router.put("/logs/{lid}")
def update_log(lid: int, body: LogIn, cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    l = db.get(SpDomesticationLog, lid)
    if not l or l.deleted:
        raise ApiError(40400, "记录不存在", 404)
    l.log_date = body.logDate
    l.pond_code = body.pondCode
    l.bait_type = body.baitType
    l.feed_kg = body.feedKg
    l.effect = body.effect
    db.commit()
    return ok(_log_dict(l))


@router.delete("/logs/{lid}")
def delete_log(lid: int, cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    l = db.get(SpDomesticationLog, lid)
    if not l or l.deleted:
        raise ApiError(40400, "记录不存在", 404)
    l.deleted = 1
    db.commit()
    return ok(True)
