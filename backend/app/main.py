from __future__ import annotations

from contextlib import asynccontextmanager

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.common.response import ApiError, new_trace_id
from app.config import get_settings
from app.db import Base, SessionLocal, engine
from app.routers import (
    analytics,
    breeding,
    circulation,
    disease,
    effluent,
    fill,
    iot,
    ops,
    party,
    platform,
    quality,
    supply,
    system,
    trace,
    telemetry,  # 新增：IoT时序数据
    effluent_gis,  # 新增：尾水GIS
    uav,
    domestication,
)
from app.seed import seed_if_empty
from app.seed_menus import rebuild_menus_from_catalog
from app.seed_upgrade import upgrade_seed

settings = get_settings()


def _warn_insecure_defaults() -> None:
    import logging
    import os

    log = logging.getLogger("uvicorn.error")
    if settings.jwt_secret in ("fishery-dev-secret-change-me", "", "changeme"):
        log.warning("JWT_SECRET 仍为默认值，生产环境请在 .env 中设置强随机密钥")
    if os.getenv("ENV", "").lower() in ("prod", "production") and settings.database_url.startswith("sqlite"):
        log.warning("生产环境建议使用 PostgreSQL/MySQL，当前仍为 SQLite")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    _warn_insecure_defaults()
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_if_empty(db)
        upgrade_seed(db)
        rebuild_menus_from_catalog(db)
    finally:
        db.close()
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(ApiError)
async def api_error_handler(_: Request, exc: ApiError):
    return JSONResponse(
        status_code=exc.status_code,
        content={"code": exc.code, "message": exc.message, "data": None, "traceId": new_trace_id()},
    )


@app.exception_handler(Exception)
async def unhandled(_: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"code": 50000, "message": str(exc), "data": None, "traceId": new_trace_id()},
    )


prefix = settings.api_prefix
app.include_router(platform.router, prefix=prefix)
app.include_router(system.router, prefix=prefix)
app.include_router(party.router, prefix=prefix)
app.include_router(quality.router, prefix=prefix)
app.include_router(trace.router, prefix=prefix)
app.include_router(effluent.router, prefix=prefix)
app.include_router(breeding.router, prefix=prefix)
app.include_router(iot.router, prefix=prefix)
app.include_router(ops.router, prefix=prefix)
app.include_router(disease.router, prefix=prefix)
app.include_router(supply.router, prefix=prefix)
app.include_router(circulation.router, prefix=prefix)
app.include_router(analytics.router, prefix=prefix)
app.include_router(fill.router, prefix=prefix)

# 新增路由
app.include_router(telemetry.router, prefix=prefix)
app.include_router(effluent_gis.router, prefix=prefix)
app.include_router(uav.router, prefix=prefix)
app.include_router(domestication.router, prefix=prefix)

_uploads = Path(__file__).resolve().parent.parent / "uploads"
_uploads.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(_uploads)), name="uploads")


@app.get("/health")
def health():
    return {"status": "up", "app": settings.app_name}
