from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from sqlalchemy import (
    Integer,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    deleted: Mapped[int] = mapped_column(Integer, default=0)
    remark: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)


class SysRegion(Base, TimestampMixin):
    __tablename__ = "sys_region"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    parent_id: Mapped[int] = mapped_column(Integer, default=0)
    code: Mapped[str] = mapped_column(String(32), unique=True)
    name: Mapped[str] = mapped_column(String(64))
    level: Mapped[int] = mapped_column(Integer, default=3)
    sort_no: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[int] = mapped_column(Integer, default=1)


class SysProject(Base, TimestampMixin):
    __tablename__ = "sys_project"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    region_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("sys_region.id"))
    code: Mapped[str] = mapped_column(String(64), unique=True)
    name: Mapped[str] = mapped_column(String(128))
    logo_url: Mapped[Optional[str]] = mapped_column(String(512))
    screen_title: Mapped[Optional[str]] = mapped_column(String(128))
    status: Mapped[int] = mapped_column(Integer, default=1)


class SysUser(Base, TimestampMixin):
    __tablename__ = "sys_user"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(64), unique=True)
    password_hash: Mapped[str] = mapped_column(String(128))
    real_name: Mapped[Optional[str]] = mapped_column(String(64))
    mobile: Mapped[Optional[str]] = mapped_column(String(20))
    user_type: Mapped[str] = mapped_column(String(32))  # PLATFORM/COUNTY/ENTERPRISE
    region_id: Mapped[Optional[int]] = mapped_column(Integer)
    enterprise_id: Mapped[Optional[int]] = mapped_column(Integer)
    project_id: Mapped[Optional[int]] = mapped_column(Integer)
    data_scope: Mapped[str] = mapped_column(String(32), default="ENTERPRISE")
    status: Mapped[int] = mapped_column(Integer, default=1)


class SysRole(Base, TimestampMixin):
    __tablename__ = "sys_role"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(64), unique=True)
    name: Mapped[str] = mapped_column(String(64))
    portal: Mapped[str] = mapped_column(String(16))  # GOV/ENT/BOTH
    status: Mapped[int] = mapped_column(Integer, default=1)


class SysUserRole(Base):
    __tablename__ = "sys_user_role"
    __table_args__ = (UniqueConstraint("user_id", "role_id"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("sys_user.id"))
    role_id: Mapped[int] = mapped_column(Integer, ForeignKey("sys_role.id"))


class SysMenu(Base, TimestampMixin):
    __tablename__ = "sys_menu"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    parent_id: Mapped[int] = mapped_column(Integer, default=0)
    name: Mapped[str] = mapped_column(String(64))
    type: Mapped[int] = mapped_column(Integer, default=2)  # 1 dir 2 menu 3 btn
    path: Mapped[Optional[str]] = mapped_column(String(128))
    component: Mapped[Optional[str]] = mapped_column(String(128))
    permission: Mapped[Optional[str]] = mapped_column(String(128))
    icon: Mapped[Optional[str]] = mapped_column(String(64))
    portal: Mapped[str] = mapped_column(String(16), default="BOTH")
    sort_no: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[int] = mapped_column(Integer, default=1)


class SysRoleMenu(Base):
    __tablename__ = "sys_role_menu"
    __table_args__ = (UniqueConstraint("role_id", "menu_id"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    role_id: Mapped[int] = mapped_column(Integer, ForeignKey("sys_role.id"))
    menu_id: Mapped[int] = mapped_column(Integer, ForeignKey("sys_menu.id"))


class SysTodo(Base, TimestampMixin):
    __tablename__ = "sys_todo"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[Optional[int]] = mapped_column(Integer)
    enterprise_id: Mapped[Optional[int]] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(String(200))
    biz_type: Mapped[str] = mapped_column(String(64))
    biz_id: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(32), default="PENDING")  # PENDING/DONE/CANCELLED
    portal: Mapped[str] = mapped_column(String(16), default="GOV")
    assignee_role: Mapped[Optional[str]] = mapped_column(String(64))
    link_path: Mapped[Optional[str]] = mapped_column(String(256))


class SysMessage(Base, TimestampMixin):
    __tablename__ = "sys_message"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(String(200))
    content: Mapped[Optional[str]] = mapped_column(Text)
    read_flag: Mapped[int] = mapped_column(Integer, default=0)


class BizEnterprise(Base, TimestampMixin):
    __tablename__ = "biz_enterprise"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(Integer)
    region_id: Mapped[Optional[int]] = mapped_column(Integer)
    name: Mapped[str] = mapped_column(String(128))
    code: Mapped[Optional[str]] = mapped_column(String(64))
    subject_type: Mapped[Optional[str]] = mapped_column(String(64))
    contact_name: Mapped[Optional[str]] = mapped_column(String(64))
    contact_phone: Mapped[Optional[str]] = mapped_column(String(20))
    address: Mapped[Optional[str]] = mapped_column(String(256))
    lng: Mapped[Optional[float]] = mapped_column(Float)
    lat: Mapped[Optional[float]] = mapped_column(Float)
    area_mu: Mapped[Optional[float]] = mapped_column(Numeric(18, 2))
    species: Mapped[Optional[str]] = mapped_column(String(256))
    status: Mapped[str] = mapped_column(String(32), default="APPROVED")
    intro: Mapped[Optional[str]] = mapped_column(Text)
    extra_json: Mapped[Optional[str]] = mapped_column(Text)  # 养殖信息表、宣传媒体、大屏打点等


class BizPond(Base, TimestampMixin):
    __tablename__ = "biz_pond"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(Integer)
    enterprise_id: Mapped[int] = mapped_column(Integer)
    code: Mapped[Optional[str]] = mapped_column(String(64))
    name: Mapped[str] = mapped_column(String(128))
    pond_type: Mapped[Optional[str]] = mapped_column(String(64))
    nature: Mapped[Optional[str]] = mapped_column(String(64))
    area_mu: Mapped[Optional[float]] = mapped_column(Numeric(18, 2))
    species: Mapped[Optional[str]] = mapped_column(String(128))
    address: Mapped[Optional[str]] = mapped_column(String(256))
    township: Mapped[Optional[str]] = mapped_column(String(64))
    lng: Mapped[Optional[float]] = mapped_column(Float)
    lat: Mapped[Optional[float]] = mapped_column(Float)
    geom_geojson: Mapped[Optional[str]] = mapped_column(Text)
    layer_type: Mapped[str] = mapped_column(String(32), default="AQUACULTURE")  # AQUACULTURE/EFFLUENT/OUTLET
    audit_status: Mapped[str] = mapped_column(String(32), default="DRAFT")
    audit_opinion: Mapped[Optional[str]] = mapped_column(String(500))


class QaPolicy(Base, TimestampMixin):
    __tablename__ = "qa_policy"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[Optional[int]] = mapped_column(Integer)
    name: Mapped[str] = mapped_column(String(200))
    file_url: Mapped[Optional[str]] = mapped_column(String(512))
    publish_date: Mapped[Optional[date]] = mapped_column(Date)


class QaLab(Base, TimestampMixin):
    __tablename__ = "qa_lab"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[Optional[int]] = mapped_column(Integer)
    name: Mapped[str] = mapped_column(String(128))
    contact: Mapped[Optional[str]] = mapped_column(String(64))
    phone: Mapped[Optional[str]] = mapped_column(String(20))
    lng: Mapped[Optional[float]] = mapped_column(Float)
    lat: Mapped[Optional[float]] = mapped_column(Float)


class QaInspection(Base, TimestampMixin):
    __tablename__ = "qa_inspection"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(Integer)
    enterprise_id: Mapped[int] = mapped_column(Integer)
    pond_id: Mapped[Optional[int]] = mapped_column(Integer)
    batch_id: Mapped[Optional[int]] = mapped_column(Integer)
    lab_id: Mapped[Optional[int]] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(String(200))
    year: Mapped[Optional[int]] = mapped_column(Integer)
    quarter: Mapped[Optional[str]] = mapped_column(String(16))
    level: Mapped[Optional[str]] = mapped_column(String(32))
    species: Mapped[Optional[str]] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(32), default="DRAFT")
    result: Mapped[str] = mapped_column(String(32), default="PENDING")
    inspected_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))


class QaRectification(Base, TimestampMixin):
    __tablename__ = "qa_rectification"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(Integer)
    enterprise_id: Mapped[int] = mapped_column(Integer)
    inspection_id: Mapped[Optional[int]] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(String(200))
    status: Mapped[str] = mapped_column(String(32), default="PENDING")
    content: Mapped[Optional[str]] = mapped_column(Text)
    reply: Mapped[Optional[str]] = mapped_column(Text)
    review_opinion: Mapped[Optional[str]] = mapped_column(String(500))


class TrMarkApply(Base, TimestampMixin):
    __tablename__ = "tr_mark_apply"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(Integer)
    enterprise_id: Mapped[int] = mapped_column(Integer)
    batch_id: Mapped[Optional[int]] = mapped_column(Integer)
    apply_qty: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String(32), default="DRAFT")
    audit_opinion: Mapped[Optional[str]] = mapped_column(String(500))


class TrMarkCode(Base, TimestampMixin):
    __tablename__ = "tr_mark_code"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(Integer)
    enterprise_id: Mapped[int] = mapped_column(Integer)
    apply_id: Mapped[int] = mapped_column(Integer)
    batch_id: Mapped[Optional[int]] = mapped_column(Integer)
    code: Mapped[str] = mapped_column(String(64), unique=True)
    status: Mapped[str] = mapped_column(String(32), default="UNUSED")


class EfWaterBody(Base, TimestampMixin):
    __tablename__ = "ef_water_body"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(Integer)
    name: Mapped[str] = mapped_column(String(128))
    code: Mapped[Optional[str]] = mapped_column(String(64))
    level: Mapped[Optional[str]] = mapped_column(String(32))


class EfFacility(Base, TimestampMixin):
    __tablename__ = "ef_facility"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(Integer)
    enterprise_id: Mapped[Optional[int]] = mapped_column(Integer)
    name: Mapped[str] = mapped_column(String(128))
    facility_type: Mapped[str] = mapped_column(String(64), default="SETTLING")
    pond_id: Mapped[Optional[int]] = mapped_column(Integer)


class EfDischargePlan(Base, TimestampMixin):
    __tablename__ = "ef_discharge_plan"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(Integer)
    enterprise_id: Mapped[int] = mapped_column(Integer)
    water_body_id: Mapped[Optional[int]] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(String(200))
    plan_month: Mapped[Optional[str]] = mapped_column(String(7))
    volume: Mapped[Optional[float]] = mapped_column(Numeric(18, 2))
    status: Mapped[str] = mapped_column(String(32), default="DRAFT")


class EfPatrol(Base, TimestampMixin):
    __tablename__ = "ef_patrol"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(Integer)
    enterprise_id: Mapped[int] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(String(200))
    result: Mapped[Optional[str]] = mapped_column(String(64))
    photos: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), default="DONE")


class BrBatch(Base, TimestampMixin):
    __tablename__ = "br_batch"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(Integer)
    enterprise_id: Mapped[int] = mapped_column(Integer)
    pond_id: Mapped[int] = mapped_column(Integer)
    batch_no: Mapped[str] = mapped_column(String(64))
    species: Mapped[str] = mapped_column(String(64))
    stock_qty: Mapped[Optional[float]] = mapped_column(Numeric(18, 2))
    stock_date: Mapped[Optional[date]] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(32), default="BREEDING")
    feed_total_kg: Mapped[float] = mapped_column(Numeric(18, 4), default=0)
    harvest_kg: Mapped[float] = mapped_column(Numeric(18, 4), default=0)
    mortality_qty: Mapped[float] = mapped_column(Numeric(18, 2), default=0)


class BrActivity(Base, TimestampMixin):
    __tablename__ = "br_activity"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(Integer)
    enterprise_id: Mapped[int] = mapped_column(Integer)
    batch_id: Mapped[int] = mapped_column(Integer)
    pond_id: Mapped[Optional[int]] = mapped_column(Integer)
    activity_type: Mapped[str] = mapped_column(String(32))  # FEED/MEDICINE/WATER/OTHER
    title: Mapped[str] = mapped_column(String(200))
    qty: Mapped[Optional[float]] = mapped_column(Numeric(18, 4))
    unit: Mapped[Optional[str]] = mapped_column(String(16))
    input_item_id: Mapped[Optional[int]] = mapped_column(Integer)
    withdrawal_days: Mapped[int] = mapped_column(Integer, default=0)
    withdrawal_until: Mapped[Optional[date]] = mapped_column(Date)
    occurred_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))


class BrHarvest(Base, TimestampMixin):
    __tablename__ = "br_harvest"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(Integer)
    enterprise_id: Mapped[int] = mapped_column(Integer)
    batch_id: Mapped[int] = mapped_column(Integer)
    weight_kg: Mapped[float] = mapped_column(Numeric(18, 4))
    harvested_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))


class InSupplier(Base, TimestampMixin):
    __tablename__ = "in_supplier"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[Optional[int]] = mapped_column(Integer)
    enterprise_id: Mapped[int] = mapped_column(Integer)
    name: Mapped[str] = mapped_column(String(128))
    contact: Mapped[Optional[str]] = mapped_column(String(64))
    phone: Mapped[Optional[str]] = mapped_column(String(20))
    category: Mapped[Optional[str]] = mapped_column(String(64))


class InItem(Base, TimestampMixin):
    __tablename__ = "in_item"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[Optional[int]] = mapped_column(Integer)
    enterprise_id: Mapped[int] = mapped_column(Integer)
    supplier_id: Mapped[Optional[int]] = mapped_column(Integer)
    name: Mapped[str] = mapped_column(String(128))
    category: Mapped[str] = mapped_column(String(32))  # FEED/MEDICINE/SEED/EQUIP
    unit: Mapped[str] = mapped_column(String(16), default="kg")
    withdrawal_days: Mapped[int] = mapped_column(Integer, default=0)


class WmWarehouse(Base, TimestampMixin):
    __tablename__ = "wm_warehouse"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(Integer)
    enterprise_id: Mapped[int] = mapped_column(Integer)
    name: Mapped[str] = mapped_column(String(128))
    code: Mapped[Optional[str]] = mapped_column(String(64))


class WmStock(Base, TimestampMixin):
    __tablename__ = "wm_stock"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    warehouse_id: Mapped[int] = mapped_column(Integer)
    enterprise_id: Mapped[int] = mapped_column(Integer)
    item_id: Mapped[int] = mapped_column(Integer)
    qty: Mapped[float] = mapped_column(Numeric(18, 4), default=0)


class WmTxn(Base, TimestampMixin):
    __tablename__ = "wm_txn"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    warehouse_id: Mapped[int] = mapped_column(Integer)
    enterprise_id: Mapped[int] = mapped_column(Integer)
    item_id: Mapped[int] = mapped_column(Integer)
    batch_id: Mapped[Optional[int]] = mapped_column(Integer)
    txn_type: Mapped[str] = mapped_column(String(16))  # IN/OUT
    qty: Mapped[float] = mapped_column(Numeric(18, 4))


class LgCustomer(Base, TimestampMixin):
    __tablename__ = "lg_customer"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    enterprise_id: Mapped[int] = mapped_column(Integer)
    name: Mapped[str] = mapped_column(String(128))
    phone: Mapped[Optional[str]] = mapped_column(String(20))
    address: Mapped[Optional[str]] = mapped_column(String(256))


class LgLedgerEntry(Base, TimestampMixin):
    __tablename__ = "lg_ledger_entry"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    enterprise_id: Mapped[int] = mapped_column(Integer)
    batch_id: Mapped[Optional[int]] = mapped_column(Integer)
    customer_id: Mapped[Optional[int]] = mapped_column(Integer)
    entry_type: Mapped[str] = mapped_column(String(16))  # INCOME/EXPENSE
    amount: Mapped[float] = mapped_column(Numeric(18, 4))
    title: Mapped[str] = mapped_column(String(200))
    occurred_at: Mapped[Optional[date]] = mapped_column(Date)


class IotDevice(Base, TimestampMixin):
    __tablename__ = "iot_device"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(Integer)
    enterprise_id: Mapped[int] = mapped_column(Integer)
    pond_id: Mapped[Optional[int]] = mapped_column(Integer)
    name: Mapped[str] = mapped_column(String(128))
    device_no: Mapped[str] = mapped_column(String(64))
    device_type: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(32), default="ONLINE")


class IotCamera(Base, TimestampMixin):
    __tablename__ = "iot_camera"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(Integer)
    enterprise_id: Mapped[int] = mapped_column(Integer, default=0)  # 0=未分配资源池，区县可划分给企业
    pond_id: Mapped[Optional[int]] = mapped_column(Integer)
    warehouse_id: Mapped[Optional[int]] = mapped_column(Integer)
    name: Mapped[str] = mapped_column(String(128))
    provider: Mapped[str] = mapped_column(String(32), default="EZVIZ")
    device_serial: Mapped[str] = mapped_column(String(64))
    channel_no: Mapped[int] = mapped_column(Integer, default=1)
    scene: Mapped[str] = mapped_column(String(32), default="POND")
    ptz_capable: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String(32), default="ONLINE")
    enabled: Mapped[int] = mapped_column(Integer, default=1)


class IotEzvizConfig(Base, TimestampMixin):
    """项目级萤石开放平台凭证（区县配置，企业共用取流）。"""
    __tablename__ = "iot_ezviz_config"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(Integer, unique=True)
    app_key: Mapped[Optional[str]] = mapped_column(String(128))
    app_secret: Mapped[Optional[str]] = mapped_column(String(128))
    access_token: Mapped[Optional[str]] = mapped_column(String(512))
    token_expire_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(32), default="UNSET")  # UNSET/OK/ERROR
    last_check_msg: Mapped[Optional[str]] = mapped_column(String(500))


class IotRule(Base, TimestampMixin):
    __tablename__ = "iot_rule"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    enterprise_id: Mapped[int] = mapped_column(Integer)
    device_id: Mapped[Optional[int]] = mapped_column(Integer)
    name: Mapped[str] = mapped_column(String(128))
    point_code: Mapped[str] = mapped_column(String(64))
    operator: Mapped[str] = mapped_column(String(8), default="LT")
    threshold: Mapped[float] = mapped_column(Float)
    enabled: Mapped[int] = mapped_column(Integer, default=1)


class IotAlarm(Base, TimestampMixin):
    __tablename__ = "iot_alarm"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(Integer)
    enterprise_id: Mapped[int] = mapped_column(Integer)
    device_id: Mapped[Optional[int]] = mapped_column(Integer)
    camera_id: Mapped[Optional[int]] = mapped_column(Integer)
    alarm_type: Mapped[str] = mapped_column(String(64))
    level: Mapped[str] = mapped_column(String(16), default="WARN")
    title: Mapped[str] = mapped_column(String(128))
    content: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), default="OPEN")
    occurred_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))


class TsTelemetry(Base):
    __tablename__ = "ts_telemetry"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    time: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    device_id: Mapped[int] = mapped_column(Integer, index=True)
    point_code: Mapped[str] = mapped_column(String(64))
    point_value: Mapped[float] = mapped_column(Float)
    quality: Mapped[int] = mapped_column(Integer, default=1)


class CmsArticle(Base, TimestampMixin):
    __tablename__ = "cms_article"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[Optional[int]] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(String(200))
    category: Mapped[str] = mapped_column(String(64), default="璧勮")
    content: Mapped[Optional[str]] = mapped_column(Text)
    source: Mapped[Optional[str]] = mapped_column(String(64))
    recommend: Mapped[int] = mapped_column(Integer, default=0)
    published: Mapped[int] = mapped_column(Integer, default=1)
    ent_visible: Mapped[int] = mapped_column(Integer, default=1)
    views: Mapped[int] = mapped_column(Integer, default=0)


class SpecialtySalamander(Base, TimestampMixin):
    __tablename__ = "sp_salamander_record"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(Integer)
    enterprise_id: Mapped[int] = mapped_column(Integer)
    record_type: Mapped[str] = mapped_column(String(32))  # DISEASE/BREED/PROCESS
    title: Mapped[str] = mapped_column(String(200))
    content: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), default="NORMAL")


class UavPilot(Base, TimestampMixin):
    __tablename__ = "uav_pilot"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(Integer, default=0)
    code: Mapped[str] = mapped_column(String(32), unique=True)
    name: Mapped[str] = mapped_column(String(64))
    level: Mapped[Optional[str]] = mapped_column(String(64))
    register_date: Mapped[Optional[date]] = mapped_column(Date)
    flight_hours: Mapped[Optional[float]] = mapped_column(Numeric(10, 2))
    violation_count: Mapped[int] = mapped_column(Integer, default=0)
    attachments: Mapped[Optional[str]] = mapped_column(Text)  # JSON url list


class UavMission(Base, TimestampMixin):
    __tablename__ = "uav_mission"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(Integer, default=0)
    code: Mapped[str] = mapped_column(String(32), unique=True)
    name: Mapped[str] = mapped_column(String(128))
    task_type: Mapped[Optional[str]] = mapped_column(String(64))
    location: Mapped[Optional[str]] = mapped_column(String(256))
    leader: Mapped[Optional[str]] = mapped_column(String(64))
    pilot_id: Mapped[Optional[int]] = mapped_column(Integer)
    start_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    end_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    plan_hours: Mapped[Optional[float]] = mapped_column(Numeric(10, 2))
    actual_hours: Mapped[Optional[float]] = mapped_column(Numeric(10, 2))
    status: Mapped[str] = mapped_column(String(32), default="NOT_STARTED")
    accept_result: Mapped[str] = mapped_column(String(32), default="QUALIFIED")
    images: Mapped[Optional[str]] = mapped_column(Text)
    videos: Mapped[Optional[str]] = mapped_column(Text)


class SpDomesticationPlot(Base, TimestampMixin):
    """育种驯化 - 稻田/渔稻地块"""
    __tablename__ = "sp_domestication_plot"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(Integer, default=0)
    enterprise_id: Mapped[Optional[int]] = mapped_column(Integer)
    plot_type: Mapped[str] = mapped_column(String(16))  # PADDY | RICE_FISH
    code: Mapped[str] = mapped_column(String(32), unique=True)
    area_mu: Mapped[Optional[float]] = mapped_column(Numeric(10, 2))
    crop_species: Mapped[Optional[str]] = mapped_column(String(64))
    fish_species: Mapped[Optional[str]] = mapped_column(String(64))
    plant_date: Mapped[Optional[date]] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(32), default="GROWING")
    soil_desc: Mapped[Optional[str]] = mapped_column(String(256))
    irrigation: Mapped[Optional[str]] = mapped_column(String(256))
    cost: Mapped[Optional[float]] = mapped_column(Numeric(12, 2))
    yield_kg: Mapped[Optional[float]] = mapped_column(Numeric(12, 2))
    rice_yield_kg: Mapped[Optional[float]] = mapped_column(Numeric(12, 2))
    fish_yield_kg: Mapped[Optional[float]] = mapped_column(Numeric(12, 2))
    income: Mapped[Optional[float]] = mapped_column(Numeric(12, 2))
    profit: Mapped[Optional[float]] = mapped_column(Numeric(12, 2))
    stocking_kg: Mapped[Optional[float]] = mapped_column(Numeric(12, 2))


class SpDomesticationLog(Base, TimestampMixin):
    """企业端 - 驯化投喂记录"""
    __tablename__ = "sp_domestication_log"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(Integer, default=0)
    enterprise_id: Mapped[Optional[int]] = mapped_column(Integer)
    code: Mapped[str] = mapped_column(String(32), unique=True)
    log_date: Mapped[Optional[date]] = mapped_column(Date)
    pond_code: Mapped[Optional[str]] = mapped_column(String(64))
    bait_type: Mapped[Optional[str]] = mapped_column(String(64))
    feed_kg: Mapped[Optional[float]] = mapped_column(Numeric(10, 2))
    effect: Mapped[Optional[str]] = mapped_column(String(64))


# ---- 对照 01 设计补齐的缺口实体 ----

class SysDictType(Base, TimestampMixin):
    __tablename__ = "sys_dict_type"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(64), unique=True)
    name: Mapped[str] = mapped_column(String(64))
    status: Mapped[int] = mapped_column(Integer, default=1)


class SysDictItem(Base, TimestampMixin):
    __tablename__ = "sys_dict_item"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    type_code: Mapped[str] = mapped_column(String(64), index=True)
    label: Mapped[str] = mapped_column(String(64))
    value: Mapped[str] = mapped_column(String(64))
    sort_no: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[int] = mapped_column(Integer, default=1)


class SysAuditLog(Base, TimestampMixin):
    __tablename__ = "sys_audit_log"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[Optional[int]] = mapped_column(Integer)
    username: Mapped[Optional[str]] = mapped_column(String(64))
    action: Mapped[str] = mapped_column(String(64))
    resource: Mapped[Optional[str]] = mapped_column(String(128))
    detail: Mapped[Optional[str]] = mapped_column(Text)
    ip: Mapped[Optional[str]] = mapped_column(String(64))


class BizStaff(Base, TimestampMixin):
    __tablename__ = "biz_staff"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    enterprise_id: Mapped[int] = mapped_column(Integer, index=True)
    name: Mapped[str] = mapped_column(String(64))
    phone: Mapped[Optional[str]] = mapped_column(String(20))
    post: Mapped[Optional[str]] = mapped_column(String(64))
    status: Mapped[int] = mapped_column(Integer, default=1)


class BizInfoSubmit(Base, TimestampMixin):
    __tablename__ = "biz_info_submit"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(Integer)
    enterprise_id: Mapped[int] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(String(200))
    content: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), default="DRAFT")
    audit_opinion: Mapped[Optional[str]] = mapped_column(String(500))


class QaSelfCheck(Base, TimestampMixin):
    __tablename__ = "qa_self_check"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(Integer)
    enterprise_id: Mapped[int] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(String(200))
    result: Mapped[str] = mapped_column(String(32), default="QUALIFIED")
    checked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))


class TrMarkIssue(Base, TimestampMixin):
    __tablename__ = "tr_mark_issue"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(Integer)
    enterprise_id: Mapped[int] = mapped_column(Integer)
    apply_id: Mapped[int] = mapped_column(Integer)
    issue_qty: Mapped[int] = mapped_column(Integer, default=0)
    start_code: Mapped[Optional[str]] = mapped_column(String(64))
    end_code: Mapped[Optional[str]] = mapped_column(String(64))
    issued_by: Mapped[Optional[int]] = mapped_column(Integer)


class EfDispatch(Base, TimestampMixin):
    __tablename__ = "ef_dispatch"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(Integer)
    enterprise_id: Mapped[int] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(String(200))
    content: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), default="PENDING")
    feedback: Mapped[Optional[str]] = mapped_column(Text)


class EfRectification(Base, TimestampMixin):
    __tablename__ = "ef_rectification"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(Integer)
    enterprise_id: Mapped[int] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(String(200))
    content: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), default="PENDING")
    reply: Mapped[Optional[str]] = mapped_column(Text)


class BrSale(Base, TimestampMixin):
    __tablename__ = "br_sale"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(Integer)
    enterprise_id: Mapped[int] = mapped_column(Integer)
    batch_id: Mapped[Optional[int]] = mapped_column(Integer)
    customer_name: Mapped[Optional[str]] = mapped_column(String(128))
    species: Mapped[Optional[str]] = mapped_column(String(64))
    weight_kg: Mapped[float] = mapped_column(Numeric(18, 4), default=0)
    amount: Mapped[float] = mapped_column(Numeric(18, 4), default=0)
    sold_at: Mapped[Optional[date]] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(32), default="DONE")


class DiReport(Base, TimestampMixin):
    __tablename__ = "di_report"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(Integer)
    enterprise_id: Mapped[int] = mapped_column(Integer)
    pond_id: Mapped[Optional[int]] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(String(200))
    symptom: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), default="SUBMITTED")


class DiAlert(Base, TimestampMixin):
    __tablename__ = "di_alert"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(String(200))
    level: Mapped[str] = mapped_column(String(16), default="WARN")
    content: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), default="OPEN")


class DiDiagnosisLink(Base, TimestampMixin):
    __tablename__ = "di_diagnosis_link"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[Optional[int]] = mapped_column(Integer)
    name: Mapped[str] = mapped_column(String(128))
    url: Mapped[str] = mapped_column(String(512))
    portal: Mapped[str] = mapped_column(String(16), default="ENT")


class SuListing(Base, TimestampMixin):
    __tablename__ = "su_listing"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[Optional[int]] = mapped_column(Integer)
    category: Mapped[str] = mapped_column(String(32))  # SEED/FEED/MEDICINE/EQUIP
    title: Mapped[str] = mapped_column(String(200))
    supplier_name: Mapped[Optional[str]] = mapped_column(String(128))
    contact: Mapped[Optional[str]] = mapped_column(String(64))
    phone: Mapped[Optional[str]] = mapped_column(String(20))
    brand: Mapped[Optional[str]] = mapped_column(String(64))
    region: Mapped[Optional[str]] = mapped_column(String(64))
    price: Mapped[Optional[float]] = mapped_column(Numeric(18, 4))
    published: Mapped[int] = mapped_column(Integer, default=1)


class SuMarket(Base, TimestampMixin):
    __tablename__ = "su_market"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[Optional[int]] = mapped_column(Integer)
    name: Mapped[str] = mapped_column(String(128))
    region: Mapped[Optional[str]] = mapped_column(String(64))
    lng: Mapped[Optional[float]] = mapped_column(Float)
    lat: Mapped[Optional[float]] = mapped_column(Float)


class SuPrice(Base, TimestampMixin):
    __tablename__ = "su_price"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[Optional[int]] = mapped_column(Integer)
    market_id: Mapped[Optional[int]] = mapped_column(Integer)
    species: Mapped[str] = mapped_column(String(64))
    spec: Mapped[Optional[str]] = mapped_column(String(64))
    price: Mapped[float] = mapped_column(Numeric(18, 4))
    unit: Mapped[str] = mapped_column(String(16), default="元/kg")
    price_date: Mapped[Optional[date]] = mapped_column(Date)


class IotStrategy(Base, TimestampMixin):
    __tablename__ = "iot_strategy"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    enterprise_id: Mapped[int] = mapped_column(Integer)
    device_id: Mapped[Optional[int]] = mapped_column(Integer)
    name: Mapped[str] = mapped_column(String(128))
    strategy_type: Mapped[str] = mapped_column(String(32), default="THRESHOLD")
    params_json: Mapped[Optional[str]] = mapped_column(Text)
    enabled: Mapped[int] = mapped_column(Integer, default=1)


class IotCommandLog(Base, TimestampMixin):
    __tablename__ = "iot_command_log"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    enterprise_id: Mapped[int] = mapped_column(Integer)
    device_id: Mapped[int] = mapped_column(Integer)
    command: Mapped[str] = mapped_column(String(64))
    result: Mapped[str] = mapped_column(String(32), default="OK")
    detail: Mapped[Optional[str]] = mapped_column(Text)


class WmInbound(Base, TimestampMixin):
    __tablename__ = "wm_inbound"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    enterprise_id: Mapped[int] = mapped_column(Integer)
    warehouse_id: Mapped[int] = mapped_column(Integer)
    item_id: Mapped[int] = mapped_column(Integer)
    qty: Mapped[float] = mapped_column(Numeric(18, 4))
    status: Mapped[str] = mapped_column(String(32), default="POSTED")
    source: Mapped[str] = mapped_column(String(32), default="PURCHASE")


class WmOutbound(Base, TimestampMixin):
    __tablename__ = "wm_outbound"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    enterprise_id: Mapped[int] = mapped_column(Integer)
    warehouse_id: Mapped[int] = mapped_column(Integer)
    item_id: Mapped[int] = mapped_column(Integer)
    batch_id: Mapped[Optional[int]] = mapped_column(Integer)
    qty: Mapped[float] = mapped_column(Numeric(18, 4))
    status: Mapped[str] = mapped_column(String(32), default="POSTED")


class WmStocktake(Base, TimestampMixin):
    __tablename__ = "wm_stocktake"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    enterprise_id: Mapped[int] = mapped_column(Integer)
    warehouse_id: Mapped[int] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(String(200))
    status: Mapped[str] = mapped_column(String(32), default="DRAFT")
    remark_text: Mapped[Optional[str]] = mapped_column(String(500))


class LgContract(Base, TimestampMixin):
    __tablename__ = "lg_contract"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    enterprise_id: Mapped[int] = mapped_column(Integer)
    customer_id: Mapped[Optional[int]] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(String(200))
    amount: Mapped[float] = mapped_column(Numeric(18, 4), default=0)
    status: Mapped[str] = mapped_column(String(32), default="ACTIVE")


class LgAfterSale(Base, TimestampMixin):
    __tablename__ = "lg_after_sale"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    enterprise_id: Mapped[int] = mapped_column(Integer)
    customer_id: Mapped[Optional[int]] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(String(200))
    content: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), default="OPEN")


class CiSalesOrder(Base, TimestampMixin):
    __tablename__ = "ci_sales_order"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(Integer)
    enterprise_id: Mapped[int] = mapped_column(Integer)
    order_no: Mapped[str] = mapped_column(String(64))
    buyer: Mapped[Optional[str]] = mapped_column(String(128))
    amount: Mapped[float] = mapped_column(Numeric(18, 4), default=0)
    status: Mapped[str] = mapped_column(String(32), default="CREATED")


class CiTransport(Base, TimestampMixin):
    __tablename__ = "ci_transport"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    enterprise_id: Mapped[int] = mapped_column(Integer)
    order_id: Mapped[Optional[int]] = mapped_column(Integer)
    plate_no: Mapped[Optional[str]] = mapped_column(String(32))
    from_addr: Mapped[Optional[str]] = mapped_column(String(256))
    to_addr: Mapped[Optional[str]] = mapped_column(String(256))
    status: Mapped[str] = mapped_column(String(32), default="PENDING")


class CmsCategory(Base, TimestampMixin):
    __tablename__ = "cms_category"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[Optional[int]] = mapped_column(Integer)
    name: Mapped[str] = mapped_column(String(64))
    sort_no: Mapped[int] = mapped_column(Integer, default=0)


class CmsVideo(Base, TimestampMixin):
    __tablename__ = "cms_video"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[Optional[int]] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(String(200))
    category: Mapped[Optional[str]] = mapped_column(String(64))
    url: Mapped[Optional[str]] = mapped_column(String(512))
    published: Mapped[int] = mapped_column(Integer, default=1)
    views: Mapped[int] = mapped_column(Integer, default=0)

