from __future__ import annotations

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
from app.models import SuListing, SuMarket, SuPrice

router = APIRouter(prefix="/supply", tags=["supply"])


@router.get("/listings")
def listings(category: Optional[str] = None, cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    q = select(SuListing).where(SuListing.deleted == 0, SuListing.published == 1)
    if category:
        q = q.where(SuListing.category == category)
    rows = db.scalars(q.order_by(SuListing.id.desc())).all()
    return ok(
        [
            {
                "id": x.id,
                "category": x.category,
                "title": x.title,
                "supplierName": x.supplier_name,
                "contact": x.contact,
                "phone": x.phone,
                "brand": x.brand or x.title,
                "region": x.region or "示范县",
                "price": float(x.price) if x.price is not None else None,
            }
            for x in rows
        ]
    )


class ListingIn(BaseModel):
    category: str = "SEED"
    title: str
    supplierName: Optional[str] = None
    contact: Optional[str] = None
    phone: OptionalLooseStr = None
    brand: Optional[str] = None
    region: Optional[str] = None
    price: Optional[float] = None


@router.post("/listings")
def create_listing(body: ListingIn, cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    if cu.portal not in ("GOV", "BOTH"):
        raise ApiError(40300, "仅区县维护渔需推介", 403)
    x = SuListing(
        project_id=cu.user.project_id,
        category=body.category,
        title=body.title,
        supplier_name=body.supplierName,
        contact=body.contact,
        phone=body.phone,
        brand=body.brand,
        region=body.region,
        price=body.price,
    )
    db.add(x)
    db.commit()
    db.refresh(x)
    return ok({"id": x.id})


@router.get("/markets")
def markets(cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.scalars(select(SuMarket).where(SuMarket.deleted == 0)).all()
    return ok([{"id": m.id, "name": m.name, "region": m.region, "lng": m.lng, "lat": m.lat} for m in rows])


class MarketIn(BaseModel):
    name: str
    region: Optional[str] = None
    lng: Optional[float] = None
    lat: Optional[float] = None


@router.post("/markets")
def create_market(body: MarketIn, cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    if cu.portal not in ("GOV", "BOTH"):
        raise ApiError(40300, "仅区县维护", 403)
    m = SuMarket(project_id=cu.user.project_id, name=body.name, region=body.region, lng=body.lng, lat=body.lat)
    db.add(m)
    db.commit()
    db.refresh(m)
    return ok({"id": m.id})


@router.get("/prices")
def prices(cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.scalars(select(SuPrice).where(SuPrice.deleted == 0).order_by(SuPrice.id.desc()).limit(200)).all()
    return ok(
        [
            {
                "id": p.id,
                "marketId": p.market_id,
                "species": p.species,
                "spec": p.spec,
                "price": float(p.price),
                "unit": p.unit,
                "priceDate": str(p.price_date or ""),
            }
            for p in rows
        ]
    )


class PriceIn(BaseModel):
    marketId: Optional[int] = None
    species: str
    spec: Optional[str] = None
    price: float
    unit: str = "元/kg"
    priceDate: Optional[date] = None


@router.post("/prices")
def create_price(body: PriceIn, cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    if cu.portal not in ("GOV", "BOTH"):
        raise ApiError(40300, "仅区县维护", 403)
    p = SuPrice(
        project_id=cu.user.project_id,
        market_id=body.marketId,
        species=body.species,
        spec=body.spec,
        price=body.price,
        unit=body.unit,
        price_date=body.priceDate or date.today(),
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    return ok({"id": p.id})
