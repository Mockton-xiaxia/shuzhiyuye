"""一次性全库检查：ORM↔SQLite 表/列、API 映射、feature/update 字段、引用完整性、种子数据。"""
from __future__ import annotations

import json
import sqlite3
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from sqlalchemy import inspect as sa_inspect  # noqa: E402

from app.db import engine  # noqa: E402
from app.models import Base  # noqa: E402

OUT = ROOT / "crawl_output" / "12-数据库全量检查.md"

API_TABLE_MAP = {
    "/system/users": "sys_user",
    "/party/enterprises": "biz_enterprise",
    "/party/ponds": "biz_pond",
    "/party/staffs": "biz_staff",
    "/quality/policies": "qa_policy",
    "/quality/labs": "qa_lab",
    "/quality/inspections": "qa_inspection",
    "/quality/rectifications": "qa_rectification",
    "/quality/self-checks": "qa_self_check",
    "/trace/applies": "tr_mark_apply",
    "/trace/codes": "tr_mark_code",
    "/effluent/waters": "ef_water_body",
    "/effluent/plans": "ef_discharge_plan",
    "/effluent/patrols": "ef_patrol",
    "/effluent/dispatches": "ef_dispatch",
    "/effluent/rectifications": "ef_rectification",
    "/breeding/batches": "br_batch",
    "/breeding/activities": "br_activity",
    "/breeding/sales": "br_sale",
    "/inputs/suppliers": "in_supplier",
    "/inputs/items": "in_item",
    "/wms/warehouses": "wm_warehouse",
    "/wms/stocks": "wm_stock",
    "/wms/inbounds": "wm_inbound",
    "/wms/outbounds": "wm_outbound",
    "/wms/stocktakes": "wm_stocktake",
    "/ledger/customers": "lg_customer",
    "/ledger/contracts": "lg_contract",
    "/ledger/after-sales": "lg_after_sale",
    "/ledger/entries": "lg_ledger_entry",
    "/circulation/transports": "ci_transport",
    "/circulation/sales-orders": "ci_sales_order",
    "/iot/rules": "iot_rule",
    "/iot/cameras": "iot_camera",
    "/iot/alarms": "iot_alarm",
    "/disease/alerts": "di_alert",
    "/cms/articles": "cms_article",
    "/cms/categories": "cms_category",
    "/cms/videos": "cms_video",
    "/supply/listings": "su_listing",
    "/supply/markets": "su_market",
    "/supply/prices": "su_price",
    "/specialty/disease-tests": "sp_salamander_record",
    "/specialty/domestication/logs": "sp_domestication_log",
    "/specialty/domestication/plots": "sp_domestication_plot",
    "/uav/pilots": "uav_pilot",
    "/uav/missions": "uav_mission",
}

FEATURE_UPDATE_FIELDS: dict[str, dict[str, str]] = {
    "/quality/labs": {"name": "name", "contact": "contact", "phone": "phone", "lng": "lng", "lat": "lat"},
    "/quality/policies": {"name": "name", "fileUrl": "file_url", "publishDate": "publish_date"},
    "/supply/listings": {"title": "title", "supplierName": "supplier_name", "contact": "contact", "phone": "phone", "brand": "brand", "region": "region", "price": "price", "category": "category"},
    "/supply/markets": {"name": "name", "region": "region", "lng": "lng", "lat": "lat"},
    "/supply/prices": {"species": "species", "spec": "spec", "price": "price", "unit": "unit"},
    "/effluent/waters": {"name": "name", "code": "code", "level": "level"},
    "/cms/articles": {"title": "title", "content": "content", "category": "category"},
    "/cms/categories": {"name": "name", "sortNo": "sort_no"},
    "/cms/videos": {"title": "title", "category": "category", "url": "url", "published": "published"},
    "/inputs/items": {"name": "name", "category": "category", "unit": "unit", "withdrawalDays": "withdrawal_days"},
    "/inputs/suppliers": {"name": "name", "category": "category", "contact": "contact", "phone": "phone"},
    "/party/staffs": {"name": "name", "phone": "phone", "post": "post", "status": "status"},
    "/breeding/batches": {"batchNo": "batch_no", "species": "species", "stockQty": "stock_qty", "stockDate": "stock_date", "pondId": "pond_id"},
    "/breeding/activities": {"title": "title", "activityType": "activity_type", "qty": "qty", "unit": "unit"},
    "/breeding/sales": {"customerName": "customer_name", "species": "species", "weightKg": "weight_kg", "amount": "amount", "soldAt": "sold_at"},
    "/ledger/customers": {"name": "name", "phone": "phone", "address": "address"},
    "/ledger/contracts": {"title": "title", "amount": "amount"},
    "/ledger/after-sales": {"title": "title", "content": "content"},
    "/ledger/entries": {"title": "title", "entryType": "entry_type", "amount": "amount", "month": "occurred_at", "occurredAt": "occurred_at"},
    "/wms/warehouses": {"name": "name", "code": "code"},
    "/wms/stocks": {"qty": "qty"},
    "/wms/inbounds": {"qty": "qty", "source": "source", "status": "status"},
    "/wms/outbounds": {"qty": "qty", "status": "status"},
    "/wms/stocktakes": {"title": "title"},
    "/circulation/transports": {"plateNo": "plate_no", "fromAddr": "from_addr", "toAddr": "to_addr"},
    "/iot/rules": {"name": "name", "pointCode": "point_code", "operator": "operator", "threshold": "threshold", "enabled": "enabled"},
    "/iot/cameras": {"name": "name", "deviceSerial": "device_serial", "scene": "scene", "status": "status"},
    "/disease/alerts": {"title": "title", "level": "level", "content": "content"},
    "/effluent/patrols": {"title": "title", "result": "result"},
    "/specialty/disease-tests": {"title": "title", "content": "content", "status": "status"},
    "/quality/inspections": {"title": "title", "species": "species", "quarter": "quarter", "level": "level", "result": "result", "year": "year", "status": "status"},
    "/party/ponds": {"name": "name", "code": "code", "pondType": "pond_type", "species": "species", "township": "township", "areaMu": "area_mu"},
}

BATCH_DELETE_TABLES = {
    "/quality/inspections": "qa_inspection",
    "/quality/policies": "qa_policy",
    "/quality/labs": "qa_lab",
    "/quality/self-checks": "qa_self_check",
    "/party/staffs": "biz_staff",
    "/party/ponds": "biz_pond",
    "/inputs/suppliers": "in_supplier",
    "/inputs/items": "in_item",
    "/breeding/batches": "br_batch",
    "/breeding/activities": "br_activity",
    "/breeding/sales": "br_sale",
    "/ledger/customers": "lg_customer",
    "/ledger/contracts": "lg_contract",
    "/ledger/after-sales": "lg_after_sale",
    "/ledger/entries": "lg_ledger_entry",
    "/wms/warehouses": "wm_warehouse",
    "/wms/stocks": "wm_stock",
    "/wms/inbounds": "wm_inbound",
    "/wms/outbounds": "wm_outbound",
    "/wms/stocktakes": "wm_stocktake",
    "/circulation/transports": "ci_transport",
    "/iot/rules": "iot_rule",
    "/iot/cameras": "iot_camera",
    "/disease/alerts": "di_alert",
    "/effluent/patrols": "ef_patrol",
    "/specialty/disease-tests": "sp_salamander_record",
    "/supply/prices": "su_price",
    "/supply/listings": "su_listing",
    "/cms/articles": "cms_article",
}

# 软外键：子表列 -> 父表
REF_CHECKS = [
    ("biz_pond", "enterprise_id", "biz_enterprise", "id"),
    ("biz_staff", "enterprise_id", "biz_enterprise", "id"),
    ("br_batch", "enterprise_id", "biz_enterprise", "id"),
    ("br_batch", "pond_id", "biz_pond", "id"),
    ("br_activity", "batch_id", "br_batch", "id"),
    ("br_activity", "enterprise_id", "biz_enterprise", "id"),
    ("br_sale", "enterprise_id", "biz_enterprise", "id"),
    ("in_item", "enterprise_id", "biz_enterprise", "id"),
    ("in_supplier", "enterprise_id", "biz_enterprise", "id"),
    ("wm_warehouse", "enterprise_id", "biz_enterprise", "id"),
    ("wm_stock", "enterprise_id", "biz_enterprise", "id"),
    ("wm_stock", "warehouse_id", "wm_warehouse", "id"),
    ("wm_stock", "item_id", "in_item", "id"),
    ("lg_customer", "enterprise_id", "biz_enterprise", "id"),
    ("ci_transport", "enterprise_id", "biz_enterprise", "id"),
    ("ci_sales_order", "enterprise_id", "biz_enterprise", "id"),
    ("ef_discharge_plan", "enterprise_id", "biz_enterprise", "id"),
    ("ef_patrol", "enterprise_id", "biz_enterprise", "id"),
    ("ef_dispatch", "enterprise_id", "biz_enterprise", "id"),
    ("ef_rectification", "enterprise_id", "biz_enterprise", "id"),
    ("iot_rule", "enterprise_id", "biz_enterprise", "id"),
    ("iot_camera", "enterprise_id", "biz_enterprise", "id"),
    ("iot_alarm", "enterprise_id", "biz_enterprise", "id"),
    ("sys_user", "enterprise_id", "biz_enterprise", "id"),
    ("tr_mark_apply", "enterprise_id", "biz_enterprise", "id"),
    ("tr_mark_code", "enterprise_id", "biz_enterprise", "id"),
]

CRITICAL_EMPTY = {"sys_user", "biz_enterprise", "sys_role", "sys_menu"}


def find_db() -> Path:
    for p in (ROOT / "backend" / "fishery.db", ROOT / "fishery.db"):
        if p.exists():
            return p
    raise FileNotFoundError("fishery.db not found")


def orm_columns(table_name: str) -> set[str]:
    tbl = Base.metadata.tables.get(table_name)
    if tbl is None:
        return set()
    return {c.name for c in tbl.columns}


def db_columns(conn: sqlite3.Connection, table_name: str) -> set[str]:
    return {r[1] for r in conn.execute(f"PRAGMA table_info({table_name})").fetchall()}


def row_count(conn: sqlite3.Connection, table: str) -> tuple[int, int]:
    cols = db_columns(conn, table)
    total = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    if "deleted" in cols:
        active = conn.execute(f"SELECT COUNT(*) FROM {table} WHERE deleted=0").fetchone()[0]
    else:
        active = total
    return active, total


def main() -> None:
    Base.metadata.create_all(bind=engine)
    insp = sa_inspect(engine)
    orm_table_names = sorted(Base.metadata.tables.keys())
    db_path = find_db()
    conn = sqlite3.connect(str(db_path))

    db_table_names = sorted(
        r[0]
        for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        ).fetchall()
    )

    errors: list[str] = []
    warnings: list[str] = []
    lines: list[str] = [
        "# 12 — 数据库全量检查",
        "",
        f"> 执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} · DB `{db_path}`",
        "",
    ]

    # ── 1. 表级对齐 ──
    missing = sorted(set(orm_table_names) - set(db_table_names))
    extra = sorted(set(db_table_names) - set(orm_table_names))
    lines += [
        "## 1. 表结构对齐 (ORM ↔ SQLite)",
        "",
        f"- ORM 表数: **{len(orm_table_names)}**",
        f"- DB 表数: **{len(db_table_names)}**",
        f"- 缺表: **{len(missing)}** · 多余: **{len(extra)}**",
        "",
    ]
    if missing:
        errors.append(f"ORM 有但 DB 缺表: {missing}")
        lines.append("### 缺表\n" + "\n".join(f"- `{t}`" for t in missing) + "\n")
    if extra:
        warnings.append(f"DB 有但 ORM 无: {extra}")
        lines.append("### 多余表\n" + "\n".join(f"- `{t}`" for t in extra) + "\n")

    # ── 2. 全表列对齐 ──
    col_mismatch: list[str] = []
    for t in orm_table_names:
        if t not in db_table_names:
            continue
        oc, dc = orm_columns(t), db_columns(conn, t)
        only_orm = sorted(oc - dc)
        only_db = sorted(dc - oc)
        if only_orm or only_db:
            col_mismatch.append(t)
            if only_orm:
                errors.append(f"{t}: ORM 列不在 DB: {only_orm}")
            if only_db:
                warnings.append(f"{t}: DB 列不在 ORM: {only_db}")

    lines += [
        "## 2. 列级对齐 (70 表)",
        "",
        f"- 列不一致表数: **{len(col_mismatch)}**",
        "",
    ]
    if col_mismatch:
        lines.append("| 表 | ORM 缺列 | DB 多余列 |")
        lines.append("|---|---|---|")
        for t in col_mismatch:
            oc, dc = orm_columns(t), db_columns(conn, t)
            lines.append(f"| `{t}` | {', '.join(sorted(oc - dc)) or '-'} | {', '.join(sorted(dc - oc)) or '-'} |")
        lines.append("")

    # ── 3. 全表行数 ──
    lines += ["## 3. 全表数据量", "", "| 表 | 有效行 | 总行 | 备注 |", "|---|---:|---:|---|"]
    empty_business: list[str] = []
    for t in orm_table_names:
        if t not in db_table_names:
            lines.append(f"| `{t}` | - | - | 缺表 |")
            continue
        active, total = row_count(conn, t)
        note = ""
        if t in CRITICAL_EMPTY and active == 0:
            errors.append(f"关键表为空: {t}")
            note = "关键表空"
        elif active == 0:
            empty_business.append(t)
            note = "空"
        deleted = total - active
        if deleted:
            note = (note + " " if note else "") + f"deleted={deleted}"
        lines.append(f"| `{t}` | {active} | {total} | {note or 'OK'} |")
    lines.append("")

    # ── 4. API → 表 ──
    lines += ["## 4. API → 表映射", ""]
    api_bad = [api for api, tbl in API_TABLE_MAP.items() if tbl not in orm_table_names]
    if api_bad:
        errors.extend([f"API 无 ORM 表: {a}" for a in api_bad])
    lines.append(f"- 业务 API 映射: **{len(API_TABLE_MAP) - len(api_bad)}/{len(API_TABLE_MAP)}** OK")
    lines.append("")

    # ── 5. feature/update 字段 ──
    lines += ["## 5. feature/update 字段映射", "", "| API | 问题 |", "|---|---|"]
    field_issues = 0
    for api, fmap in sorted(FEATURE_UPDATE_FIELDS.items()):
        tbl = API_TABLE_MAP.get(api)
        if not tbl:
            # ponds etc may not be in map - infer from fmap usage
            tbl = {
                "/party/ponds": "biz_pond",
            }.get(api)
        if not tbl:
            continue
        cols = orm_columns(tbl)
        bad_cols = [f"{src}→{dst}" for src, dst in fmap.items() if dst not in cols]
        if bad_cols:
            field_issues += 1
            warnings.append(f"{api}: 映射列不存在 {bad_cols}")
            lines.append(f"| `{api}` | 无效列: {', '.join(bad_cols)} |")
    if field_issues == 0:
        lines.append("| *(全部)* | 无无效列映射 |")
    lines.append("")

    # ── 6. batch-delete ──
    lines += ["## 6. batch-delete 映射", ""]
    bd_bad = []
    for api, tbl in BATCH_DELETE_TABLES.items():
        if tbl not in orm_table_names:
            bd_bad.append(f"{api}→{tbl}")
        elif "deleted" not in orm_columns(tbl):
            bd_bad.append(f"{api}→{tbl}(无 deleted 列)")
    if bd_bad:
        warnings.extend(bd_bad)
        lines.append("问题:\n" + "\n".join(f"- {x}" for x in bd_bad) + "\n")
    else:
        lines.append(f"- **{len(BATCH_DELETE_TABLES)}** 条映射 OK\n")

    # ── 7. 引用完整性 ──
    lines += ["## 7. 引用完整性 (软外键)", "", "| 检查 | 孤儿数 |", "|---|---:|"]
    ref_errors = 0
    for child, ccol, parent, pcol in REF_CHECKS:
        if child not in db_table_names or parent not in db_table_names:
            continue
        cc = db_columns(conn, child)
        if ccol not in cc:
            continue
        del_clause = " AND c.deleted=0" if "deleted" in cc else ""
        sql = f"""
            SELECT COUNT(*) FROM {child} c
            LEFT JOIN {parent} p ON c.{ccol} = p.{pcol}
            WHERE c.{ccol} IS NOT NULL AND c.{ccol} != 0
            {del_clause}
            AND (p.{pcol} IS NULL OR p.deleted=1)
        """
        if "deleted" not in db_columns(conn, parent):
            sql = f"""
                SELECT COUNT(*) FROM {child} c
                LEFT JOIN {parent} p ON c.{ccol} = p.{pcol}
                WHERE c.{ccol} IS NOT NULL AND c.{ccol} != 0
                {del_clause}
                AND p.{pcol} IS NULL
            """
        orphans = conn.execute(sql).fetchone()[0]
        flag = "OK" if orphans == 0 else "FAIL"
        lines.append(f"| `{child}.{ccol}` → `{parent}.{pcol}` | {orphans} {flag} |")
        if orphans:
            ref_errors += 1
            errors.append(f"孤儿引用 {child}.{ccol}→{parent}: {orphans} 条")
    lines.append("")

    # ── 8. 种子/账号 ──
    lines += ["## 8. 种子数据 & 演示账号", ""]
    users = conn.execute(
        "SELECT username, user_type, enterprise_id, status FROM sys_user WHERE deleted=0"
    ).fetchall()
    ents = conn.execute("SELECT id, name FROM biz_enterprise WHERE deleted=0").fetchall()
    roles = conn.execute("SELECT code, name FROM sys_role WHERE deleted=0").fetchall()
    menus = conn.execute("SELECT COUNT(*) FROM sys_menu WHERE deleted=0").fetchone()[0]

    lines.append("| 用户 | 类型 | 主体ID | 状态 |")
    lines.append("|---|---|---:|---|")
    for u in users:
        lines.append(f"| `{u[0]}` | {u[1]} | {u[2] or '-'} | {'启用' if u[3] else '停用'} |")
    lines.append("")
    lines.append(f"- 主体: {len(ents)} · 角色: {len(roles)} · 菜单: {menus}")
    if not any(u[0] == "gov_admin" for u in users):
        errors.append("缺少演示账号 gov_admin")
    if not any(u[0] == "ent_admin" for u in users):
        errors.append("缺少演示账号 ent_admin")
    if len(ents) == 0:
        errors.append("无养殖主体种子数据")

    # ── 9. 汇总 ──
    lines += [
        "",
        "## 9. 汇总",
        "",
        f"- **ERROR**: {len(errors)}",
        f"- **WARN**: {len(warnings)}",
        f"- **空业务表**: {len(empty_business)}（非关键表允许空）",
        "",
    ]
    if errors:
        lines.append("### 错误\n")
        for e in errors:
            lines.append(f"- {e}")
        lines.append("")
    if warnings:
        lines.append("### 警告\n")
        for w in warnings:
            lines.append(f"- {w}")
        lines.append("")

    result = "PASS" if not errors else "FAIL"
    lines.append(f"**result: {result}**")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines), encoding="utf-8")
    conn.close()

    print(OUT)
    print(f"errors={len(errors)} warnings={len(warnings)} result={result}")
    if errors:
        for e in errors[:20]:
            print(f"  ERROR: {e}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
