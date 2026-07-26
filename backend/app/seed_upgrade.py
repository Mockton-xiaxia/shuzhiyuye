"""幂等补齐字典与演示数据（菜单改由 seed_menus.rebuild_menus_from_catalog 负责）。"""
from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import Base, engine
from app.models import (
    BizEnterprise,
    BizPond,
    BizStaff,
    CiTransport,
    CmsCategory,
    CmsVideo,
    DiAlert,
    DiDiagnosisLink,
    DiReport,
    EfDispatch,
    EfPatrol,
    EfRectification,
    EfWaterBody,
    InItem,
    InSupplier,
    IotCamera,
    IotCommandLog,
    IotDevice,
    LgAfterSale,
    LgContract,
    LgCustomer,
    LgLedgerEntry,
    QaLab,
    QaRectification,
    QaSelfCheck,
    SuListing,
    SuMarket,
    SuPrice,
    SysDictItem,
    SysDictType,
    SysProject,
    SysRegion,
    SysTodo,
    SysUser,
    UavMission,
    UavPilot,
    SpDomesticationPlot,
    SpDomesticationLog,
    TrMarkApply,
    WmInbound,
    WmOutbound,
    WmStock,
    WmStocktake,
    WmWarehouse,
)


# 旧演示数据中的真实地名/厂商名 → 中性演示名（已有库启动时幂等替换）
_LEGACY_DEMO_REPLACEMENTS = [
    ("汉中市南郑区绿色循环渔业试点项目", "绿色循环渔业试点项目"),
    ("汉中市南郑区渔业总体情况", "区县渔业总体情况"),
    ("汉中市南郑区绿色循环渔业试点", "绿色循环渔业试点"),
    ("南郑区绿色循环渔业", "绿色循环渔业"),
    ("南郑区水产检测中心", "区县水产检测中心"),
    ("南郑区水产市场", "区县水产市场"),
    ("南郑渔政执法", "区县渔政执法"),
    ("汉中水产批发市场", "本地水产批发市场"),
    ("汉中水产批发商", "本地水产批发商"),
    ("余秀芳养殖场", "示范养殖场"),
    ("南郑大鲵", "本地大鲵"),
    ("捷安物联", "智联物联"),
    ("汉中饲料厂", "本地饲料厂"),
    ("汉中渔药店", "本地渔药店"),
    ("南郑区县管理员", "区县管理员"),
    ("陕西省汉中市南郑区", "浙江省杭州市西湖区"),
    ("陕西省,汉中市,南郑区", "浙江省,杭州市,西湖区"),
    ("陕西省示范市示范县", "浙江省杭州市西湖区"),
    ("陕西省,示范市,示范县", "浙江省,杭州市,西湖区"),
    ("南郑区", "西湖区"),
    ("南郑", "示范"),
    ("汉山街道", "北山街道"),
    ("汉山社区", "示范社区"),
    ("汉江支流演示水域", "示范支流演示水域"),
    ("汉中市", "杭州市"),
    ("汉中批发", "本地批发"),
    ("余秀芳", "张示范"),
]


def _scrub_demo_text(value: str | None) -> str | None:
    if not value:
        return value
    out = value
    for old, new in _LEGACY_DEMO_REPLACEMENTS:
        out = out.replace(old, new)
    return out


def _rename_legacy_demo_accounts(db: Session) -> None:
    """旧演示账号用户名 → 中性账号（密码不变）。"""
    renames = {"nzqxj": "gov_admin", "yuxiufang": "ent_admin"}
    dirty = False
    for old, new in renames.items():
        u = db.scalar(select(SysUser).where(SysUser.username == old).limit(1))
        if u and not db.scalar(select(SysUser).where(SysUser.username == new).limit(1)):
            u.username = new
            dirty = True
    if dirty:
        db.commit()


def _normalize_legacy_demo_names(db: Session) -> None:
    """已有 SQLite 库中的旧演示文案，启动时统一替换为中性名称。"""
    dirty = False
    for p in db.scalars(select(SysProject)).all():
        for attr in ("name", "screen_title"):
            v = getattr(p, attr, None)
            nv = _scrub_demo_text(v)
            if nv != v:
                setattr(p, attr, nv)
                dirty = True
    for u in db.scalars(select(SysUser)).all():
        nv = _scrub_demo_text(u.real_name)
        if nv != u.real_name:
            u.real_name = nv
            dirty = True
    for r in db.scalars(select(SysRegion)).all():
        nv = _scrub_demo_text(r.name)
        if nv != r.name:
            r.name = nv
            dirty = True
    for ent in db.scalars(select(BizEnterprise)).all():
        for attr in ("name", "contact_name", "address", "intro", "extra_json"):
            v = getattr(ent, attr, None)
            nv = _scrub_demo_text(v)
            if nv != v:
                setattr(ent, attr, nv)
                dirty = True
    for row in db.scalars(select(QaLab)).all():
        nv = _scrub_demo_text(row.name)
        if nv != row.name:
            row.name = nv
            dirty = True
    for row in db.scalars(select(SuMarket)).all():
        for attr in ("name", "region"):
            v = getattr(row, attr, None)
            nv = _scrub_demo_text(v)
            if nv != v:
                setattr(row, attr, nv)
                dirty = True
    for row in db.scalars(select(SuListing)).all():
        nv = _scrub_demo_text(row.supplier_name)
        if nv != row.supplier_name:
            row.supplier_name = nv
            dirty = True
    for row in db.scalars(select(LgCustomer)).all():
        nv = _scrub_demo_text(row.name)
        if nv != row.name:
            row.name = nv
            dirty = True
    for row in db.scalars(select(EfWaterBody)).all():
        nv = _scrub_demo_text(row.name)
        if nv != row.name:
            row.name = nv
            dirty = True
    for row in db.scalars(select(TrMarkApply)).all():
        if row.remark and str(row.remark).startswith("{"):
            import json
            try:
                meta = json.loads(row.remark)
                changed_meta = False
                for k, v in list(meta.items()):
                    if isinstance(v, str):
                        nv = _scrub_demo_text(v)
                        if nv != v:
                            meta[k] = nv
                            changed_meta = True
                if changed_meta:
                    row.remark = json.dumps(meta, ensure_ascii=False)
                    dirty = True
            except Exception:
                pass
        elif row.remark:
            nv = _scrub_demo_text(str(row.remark))
            if nv != row.remark:
                row.remark = nv
                dirty = True
    for row in db.scalars(select(InSupplier)).all():
        nv = _scrub_demo_text(row.name)
        if nv != row.name:
            row.name = nv
            dirty = True
    for row in db.scalars(select(UavMission)).all():
        for attr in ("name", "location"):
            v = getattr(row, attr, None)
            nv = _scrub_demo_text(v)
            if nv != v:
                setattr(row, attr, nv)
                dirty = True
    if dirty:
        db.commit()


def upgrade_seed(db: Session) -> None:
    Base.metadata.create_all(bind=engine)
    # SQLite 轻量补列（已有库无 enabled 时）
    try:
        from sqlalchemy import text

        cols = [r[1] for r in db.execute(text("PRAGMA table_info(iot_camera)")).fetchall()]
        if "enabled" not in cols:
            db.execute(text("ALTER TABLE iot_camera ADD COLUMN enabled INTEGER DEFAULT 1"))
            db.commit()
    except Exception:
        db.rollback()

    try:
        from sqlalchemy import text

        ent_cols = [r[1] for r in db.execute(text("PRAGMA table_info(biz_enterprise)")).fetchall()]
        if "extra_json" not in ent_cols:
            db.execute(text("ALTER TABLE biz_enterprise ADD COLUMN extra_json TEXT"))
            db.commit()
    except Exception:
        db.rollback()

    try:
        from sqlalchemy import text

        listing_cols = [r[1] for r in db.execute(text("PRAGMA table_info(su_listing)")).fetchall()]
        if "brand" not in listing_cols:
            db.execute(text("ALTER TABLE su_listing ADD COLUMN brand VARCHAR(64)"))
        if "region" not in listing_cols:
            db.execute(text("ALTER TABLE su_listing ADD COLUMN region VARCHAR(64)"))
        if "price" not in listing_cols:
            db.execute(text("ALTER TABLE su_listing ADD COLUMN price NUMERIC(18,4)"))
        db.commit()
        defaults = {
            "FEED": ("本地品牌", "西湖区", 12.5),
            "SEED": ("优质苗种", "西湖区", 38.0),
            "MEDICINE": ("合格渔药", "西湖区", 25.0),
            "EQUIP": ("智联物联", "西湖区", 860.0),
        }
        for row in db.scalars(select(SuListing)).all():
            d = defaults.get(row.category, ("通用品牌", "西湖区", 10.0))
            if not row.brand:
                row.brand = d[0]
            if not row.region:
                row.region = d[1]
            if row.price is None:
                row.price = d[2]
        db.commit()
    except Exception:
        db.rollback()

    _normalize_legacy_demo_names(db)
    _rename_legacy_demo_accounts(db)
    _seed_region_tree(db)
    _migrate_pond_map_coords(db)
    _upgrade_demo_enterprise(db)
    _seed_uav_demo(db)
    _seed_domestication_demo(db)

    if not db.scalar(select(SysDictType).where(SysDictType.code == "pond_type")):
        db.add(SysDictType(code="pond_type", name="塘口类型"))
        for i, (lab, val) in enumerate([("池塘", "POND"), ("工厂化", "FACTORY"), ("稻渔", "RICE")], 1):
            db.add(SysDictItem(type_code="pond_type", label=lab, value=val, sort_no=i))
    if not db.scalar(select(SysDictType).where(SysDictType.code == "species")):
        db.add(SysDictType(code="species", name="养殖品种"))
        for i, (lab, val) in enumerate([("大鲵", "DN"), ("草鱼", "CY"), ("鲢", "LY"), ("鲤", "LI"), ("鲫", "JI")], 1):
            db.add(SysDictItem(type_code="species", label=lab, value=val, sort_no=i))

    if not db.scalar(select(QaLab).limit(1)):
        db.add(QaLab(project_id=1, name="区县水产检测中心", contact="张工", phone="0571-1234567", lng=120.145, lat=30.248))
    if not db.scalar(select(BizStaff).limit(1)):
        db.add(BizStaff(enterprise_id=1, name="养殖员小王", phone="13900001111", post="养殖员"))
    if not db.scalar(select(DiDiagnosisLink).limit(1)):
        db.add(DiDiagnosisLink(project_id=1, name="远程辅助诊断网", url="http://60.165.239.173:9000/ffcportal", portal="ENT"))
        db.add(DiAlert(project_id=1, title="春季常见病害提示", level="INFO", content="关注大鲵寄生虫防控"))
        db.add(DiReport(project_id=1, enterprise_id=1, title="演示病情测报", symptom="偶见浮头", status="SUBMITTED"))
    if not db.scalar(select(SuMarket).limit(1)):
        mkt = SuMarket(project_id=1, name="区县水产市场", region="西湖区", lng=120.155, lat=30.250)
        db.add(mkt)
        db.flush()
        db.add(SuPrice(project_id=1, market_id=mkt.id, species="大鲵", spec="商品鱼", price=180, price_date=date.today()))
        db.add(SuListing(project_id=1, category="FEED", title="膨化饲料供应", supplier_name="本地饲料厂", contact="李经理", phone="13800002222", brand="本地品牌", region="西湖区", price=12.5))
        db.add(SuListing(project_id=1, category="SEED", title="大鲵苗种供应", supplier_name="本地苗场", contact="赵场长", phone="13800003333", brand="优质苗种", region="西湖区", price=38.0))
        db.add(SuListing(project_id=1, category="MEDICINE", title="渔药供应点", supplier_name="本地渔药店", contact="周店长", phone="13800004444", brand="合格渔药", region="西湖区", price=25.0))
        db.add(SuListing(project_id=1, category="EQUIP", title="增氧设备供应", supplier_name="智联物联", contact="钱工", phone="13800005555", brand="智联物联", region="西湖区", price=860.0))
    else:
        for cat, title, supplier in [
            ("MEDICINE", "渔药供应点", "本地渔药店"),
            ("EQUIP", "增氧设备供应", "智联物联"),
        ]:
            if not db.scalar(select(SuListing).where(SuListing.category == cat).limit(1)):
                db.add(SuListing(project_id=1, category=cat, title=title, supplier_name=supplier, contact="联系人", phone="13800000000"))
    if not db.scalar(select(EfDispatch).limit(1)):
        db.add(
            EfDispatch(
                project_id=1,
                enterprise_id=1,
                title="7月尾水排放调度提醒",
                content="请按计划排放并做好监测",
                status="PENDING",
                remark='{"officerName":"区县渔政执法","labName":"区县水产检测中心","result":"需处置","unqualified":"COD偏高"}',
            )
        )
    # 清理乱码调度种子
    for bad in db.scalars(select(EfDispatch)).all():
        if bad.title and ("?" in bad.title or not bad.title.strip()):
            bad.deleted = 1

    # 保证至少一条待审核标识申请（演示区县通过/驳回）
    if not db.scalar(select(TrMarkApply).where(TrMarkApply.status == "PENDING", TrMarkApply.deleted == 0).limit(1)):
        pending = TrMarkApply(
            project_id=1,
            enterprise_id=1,
            batch_id=1,
            apply_qty=20,
            status="PENDING",
            remark='{"species":"大鲵","brand":"本地大鲵"}',
        )
        db.add(pending)
        db.flush()
        db.add(
            SysTodo(
                project_id=1,
                enterprise_id=1,
                title="标识申请待审核",
                biz_type="TRACE_APPLY",
                biz_id=pending.id,
                status="PENDING",
                portal="GOV",
                link_path="/gov/trace/applies",
            )
        )

    # 质量整改保持可演示：若无 PENDING 则补一条待接收
    if not db.scalar(select(QaRectification).where(QaRectification.status == "PENDING", QaRectification.deleted == 0).limit(1)):
        r = db.scalar(select(QaRectification).where(QaRectification.deleted == 0).limit(1))
        if r:
            db.add(
                QaRectification(
                    project_id=1,
                    enterprise_id=1,
                    inspection_id=r.inspection_id,
                    title="补种-待接收质量整改",
                    status="PENDING",
                    content="演示：请企业接收并回复整改说明",
                )
            )
    if not db.scalar(select(CmsCategory).limit(1)):
        db.add(CmsCategory(project_id=1, name="科普知识", sort_no=1))
        db.add(CmsCategory(project_id=1, name="技术规范", sort_no=2))
        db.add(CmsVideo(project_id=1, title="大鲵大丰收", category="水产资讯", url="", published=1))
    if not db.scalar(select(QaSelfCheck).limit(1)):
        db.add(QaSelfCheck(project_id=1, enterprise_id=1, title="月度自检", result="QUALIFIED"))

    # --- GIS 演示塘口（西湖区坐标 + GeoJSON）---
    existing_codes = {p.code for p in db.scalars(select(BizPond).where(BizPond.deleted == 0)).all()}
    demos = [
        (
            "TK-002",
            "2号养殖塘",
            "AQUACULTURE",
            "PENDING",
            12.5,
            120.151,
            30.244,
            '{"type":"Polygon","coordinates":[[[120.150,30.243],[120.152,30.243],[120.152,30.245],[120.150,30.245],[120.150,30.243]]]}',
        ),
        (
            "TK-003",
            "尾水处理区A",
            "EFFLUENT",
            "APPROVED",
            3.2,
            120.148,
            30.241,
            '{"type":"Polygon","coordinates":[[[120.147,30.240],[120.149,30.240],[120.149,30.242],[120.147,30.242],[120.147,30.240]]]}',
        ),
        (
            "TK-OUT-1",
            "1号出水口",
            "OUTLET",
            "APPROVED",
            0,
            120.148,
            30.2415,
            '{"type":"Point","coordinates":[120.148,30.2415]}',
        ),
        (
            "TK-004",
            "3号养殖塘",
            "AQUACULTURE",
            "PENDING",
            8.4,
            120.153,
            30.246,
            '{"type":"Polygon","coordinates":[[[120.152,30.245],[120.154,30.245],[120.154,30.247],[120.152,30.247],[120.152,30.245]]]}',
        ),
    ]
    for code, name, layer, status, area, lng, lat, gj in demos:
        if code in existing_codes:
            continue
        db.add(
            BizPond(
                project_id=1,
                enterprise_id=1,
                code=code,
                name=name,
                pond_type="池塘" if layer != "OUTLET" else "出水口",
                area_mu=area,
                species="大鲵" if layer == "AQUACULTURE" else None,
                township="北山街道",
                lng=lng,
                lat=lat,
                geom_geojson=gj,
                layer_type=layer,
                audit_status=status,
            )
        )

    # --- 填空列表演示数据（验收 rows=0 项）---
    if not db.scalar(select(EfPatrol).limit(1)):
        db.add(EfPatrol(project_id=1, enterprise_id=1, title="塘口巡检-东区", result="正常", status="DONE"))
        db.add(EfPatrol(project_id=1, enterprise_id=1, title="尾水设施巡检", result="需关注滤网", status="DONE"))
    if not db.scalar(select(EfRectification).limit(1)):
        db.add(
            EfRectification(
                project_id=1,
                enterprise_id=1,
                title="尾水排放口标识不完善",
                content="请补齐排放口标识牌并拍照回传",
                status="PENDING",
            )
        )

    feed = db.scalar(select(InItem).where(InItem.category == "FEED").limit(1))
    med = db.scalar(select(InItem).where(InItem.category == "MEDICINE").limit(1))
    prod = db.scalar(select(InItem).where(InItem.category == "PRODUCT").limit(1))
    wh = db.scalar(select(WmWarehouse).limit(1))
    if not prod and wh:
        prod = InItem(
            enterprise_id=1,
            project_id=1,
            name="商品大鲵",
            category="PRODUCT",
            unit="kg",
            withdrawal_days=0,
        )
        db.add(prod)
        db.flush()
    if wh and feed and not db.scalar(select(WmInbound).limit(1)):
        db.add(WmInbound(enterprise_id=1, warehouse_id=wh.id, item_id=feed.id, qty=500, status="POSTED", source="PURCHASE"))
        if med:
            db.add(WmInbound(enterprise_id=1, warehouse_id=wh.id, item_id=med.id, qty=20, status="POSTED", source="PURCHASE"))
        if prod:
            db.add(WmInbound(enterprise_id=1, warehouse_id=wh.id, item_id=prod.id, qty=80, status="POSTED", source="CATCH"))
        db.add(WmOutbound(enterprise_id=1, warehouse_id=wh.id, item_id=feed.id, qty=50, status="POSTED", batch_id=1))
        if med:
            db.add(WmOutbound(enterprise_id=1, warehouse_id=wh.id, item_id=med.id, qty=2, status="POSTED", batch_id=1))
        if prod:
            db.add(WmOutbound(enterprise_id=1, warehouse_id=wh.id, item_id=prod.id, qty=30, status="POSTED"))

    # 库存按品类补齐
    if wh:
        for it in (feed, med, prod):
            if not it:
                continue
            exists = db.scalar(
                select(WmStock).where(WmStock.warehouse_id == wh.id, WmStock.item_id == it.id).limit(1)
            )
            if not exists:
                qty = 1000 if it.category == "FEED" else (50 if it.category == "MEDICINE" else 120)
                db.add(WmStock(warehouse_id=wh.id, enterprise_id=1, item_id=it.id, qty=qty))

    if wh and not db.scalar(select(WmStocktake).limit(1)):
        db.add(WmStocktake(enterprise_id=1, warehouse_id=wh.id, title="2026-07 月度盘存", status="DRAFT"))

    # 资源池摄像头（未划分，供区县演示划分）
    if not db.scalar(select(IotCamera).where(IotCamera.enterprise_id == 0, IotCamera.deleted == 0).limit(1)):
        db.add(
            IotCamera(
                project_id=1,
                enterprise_id=0,
                name="待分配-东区监控",
                provider="EZVIZ",
                device_serial="POOL0001",
                channel_no=1,
                scene="POND",
                status="ONLINE",
                enabled=1,
            )
        )

    # 仓库场景摄像头（FeatureMonitor bindStorage / WAREHOUSE）
    if not db.scalar(select(IotCamera).where(IotCamera.scene == "WAREHOUSE", IotCamera.deleted == 0).limit(1)):
        db.add(
            IotCamera(
                project_id=1,
                enterprise_id=1,
                name="冷库仓门监控",
                provider="EZVIZ",
                device_serial="WH0001",
                channel_no=1,
                scene="WAREHOUSE",
                status="ONLINE",
                enabled=1,
            )
        )

    cust = db.scalar(select(LgCustomer).limit(1))
    cust_id = cust.id if cust else None
    if not db.scalar(select(LgContract).limit(1)):
        db.add(LgContract(enterprise_id=1, customer_id=cust_id, title="2026水产品购销合同", amount=50000, status="ACTIVE"))
    if not db.scalar(select(LgLedgerEntry).limit(1)):
        db.add(
            LgLedgerEntry(
                enterprise_id=1,
                customer_id=cust_id,
                entry_type="INCOME",
                amount=12000,
                title="商品鱼销售收入",
                occurred_at=date(2026, 6, 15),
            )
        )
        db.add(
            LgLedgerEntry(
                enterprise_id=1,
                entry_type="EXPENSE",
                amount=3500,
                title="饲料采购支出",
                occurred_at=date(2026, 6, 8),
            )
        )
    if not db.scalar(select(LgAfterSale).limit(1)):
        db.add(
            LgAfterSale(
                enterprise_id=1,
                customer_id=cust_id,
                title="配送时效反馈",
                content="客户反馈上周配送晚一天，已沟通",
                status="OPEN",
            )
        )

    if not db.scalar(select(CiTransport).limit(1)):
        db.add(
            CiTransport(
                enterprise_id=1,
                order_id=None,
                plate_no="陕F·D1234",
                from_addr="示范县示范养殖场",
                to_addr="本地水产批发市场",
                status="DONE",
            )
        )

    device = db.scalar(select(IotDevice).limit(1))
    if device and not db.scalar(select(IotCommandLog).limit(1)):
        db.add(
            IotCommandLog(
                enterprise_id=device.enterprise_id,
                device_id=device.id,
                command="AERATOR_ON",
                result="OK",
                detail="演示：开启增氧",
            )
        )

    db.commit()


def _remap_geojson_coords(gj_str: str, delta_lng: float, delta_lat: float) -> str:
    import json

    try:
        obj = json.loads(gj_str)
    except Exception:
        return gj_str

    def walk(coords):
        if isinstance(coords[0], (int, float)):
            return [round(coords[0] + delta_lng, 6), round(coords[1] + delta_lat, 6)]
        return [walk(c) for c in coords]

    if "coordinates" in obj:
        obj["coordinates"] = walk(obj["coordinates"])
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"))


def _migrate_pond_map_coords(db: Session) -> None:
    """将旧南郑坐标（lng<110）平移至杭州市西湖区演示中心。"""
    from app.data.demo_map_config import DEMO_LAT, DEMO_LNG, OLD_MAP_CENTER

    delta_lng = DEMO_LNG - OLD_MAP_CENTER[0]
    delta_lat = DEMO_LAT - OLD_MAP_CENTER[1]
    dirty = False

    def needs_remap(lng) -> bool:
        try:
            return lng is not None and float(lng) < 110
        except (TypeError, ValueError):
            return False

    def shift(lng, lat):
        return round(float(lng) + delta_lng, 6), round(float(lat or 0) + delta_lat, 6)

    for ent in db.scalars(select(BizEnterprise).where(BizEnterprise.deleted == 0)).all():
        if needs_remap(ent.lng):
            ent.lng, ent.lat = shift(ent.lng, ent.lat)
            dirty = True

    for pond in db.scalars(select(BizPond).where(BizPond.deleted == 0)).all():
        if pond.township in ("示范镇", "汉山街道", "南郑"):
            pond.township = "北山街道"
            dirty = True
        if not needs_remap(pond.lng):
            continue
        pond.lng, pond.lat = shift(pond.lng, pond.lat)
        if pond.geom_geojson:
            pond.geom_geojson = _remap_geojson_coords(pond.geom_geojson, delta_lng, delta_lat)
        dirty = True

    for row in db.scalars(select(QaLab)).all():
        if needs_remap(row.lng):
            row.lng, row.lat = shift(row.lng, row.lat)
            dirty = True

    for row in db.scalars(select(SuMarket)).all():
        if needs_remap(row.lng):
            row.lng, row.lat = shift(row.lng, row.lat)
            dirty = True

    if dirty:
        db.commit()


def _seed_region_tree(db: Session) -> None:
    """导入全国省 / 市 / 区县划，并校准演示主体所属区划。"""
    from app.services.region_import import import_national_regions

    import_national_regions(db)
    _migrate_demo_region_refs(db)


def _migrate_demo_region_refs(db: Session) -> None:
    """演示主体默认挂到浙江省 · 杭州市 · 西湖区（全国区划树内）。"""
    import json

    county = db.scalar(select(SysRegion).where(SysRegion.code == "330106").limit(1))
    city = db.scalar(select(SysRegion).where(SysRegion.code == "330100").limit(1))
    prov = db.scalar(select(SysRegion).where(SysRegion.code == "330000").limit(1))
    if not county:
        return
    label = "浙江省,杭州市,西湖区"
    path = ["330000", "330100", "330106"]
    for ent in db.scalars(select(BizEnterprise).where(BizEnterprise.deleted == 0)).all():
        ent.address = _scrub_demo_text(ent.address) or ent.address
        if ent.extra_json:
            try:
                extra = json.loads(ent.extra_json)
            except Exception:
                extra = {}
        else:
            extra = {}
        extra["regionPath"] = path
        extra["regionPathLabel"] = label
        ent.extra_json = json.dumps(extra, ensure_ascii=False)
        if county.id:
            ent.region_id = county.id
    for p in db.scalars(select(SysProject)).all():
        if county.id:
            p.region_id = county.id
    for u in db.scalars(select(SysUser).where(SysUser.user_type == "COUNTY")).all():
        if county.id:
            u.region_id = county.id
    for old in db.scalars(select(SysRegion).where(SysRegion.code.like("610703%"))).all():
        old.deleted = 1
    db.commit()


def _upgrade_demo_enterprise(db: Session) -> None:
    import json

    ent = db.scalar(select(BizEnterprise).where(BizEnterprise.code == "YXF001").limit(1))
    if not ent:
        return
    ent.name = _scrub_demo_text(ent.name) or ent.name
    ent.contact_name = _scrub_demo_text(ent.contact_name) or ent.contact_name
    ent.address = _scrub_demo_text(ent.address) or ent.address
    ent.intro = _scrub_demo_text(ent.intro) or ent.intro
    ent.subject_type = ent.subject_type or "INDIVIDUAL"
    default_extra = {
        "regionPath": ["330000", "330100", "330106"],
        "regionPathLabel": "浙江省,杭州市,西湖区",
        "speciesList": ["大鲵", "草鱼", "鲢", "鲤", "鲫"],
        "annualOutputTon": 12.5,
        "breedingMode": "POND",
        "showOnScreen": True,
        "breedingItems": [
            {"species": "大鲵", "ratio": 30, "outSpec": "500g", "yieldPerMu": 80, "outMonth": "全年"},
            {"species": "草鱼", "ratio": 25, "outSpec": "2000g", "yieldPerMu": 100, "outMonth": "9-10月"},
            {"species": "鲢", "ratio": 20, "outSpec": "1500g", "yieldPerMu": 120, "outMonth": "全年"},
            {"species": "鲤", "ratio": 15, "outSpec": "2000g", "yieldPerMu": 150, "outMonth": "全年"},
            {"species": "鲫", "ratio": 10, "outSpec": "300g", "yieldPerMu": 20, "outMonth": "全年"},
        ],
        "fisheryQualification": "水产养殖证",
        "promoImages": [],
        "promoVideos": [],
        "selfCheckFiles": [],
    }
    if not ent.extra_json:
        ent.extra_json = json.dumps(default_extra, ensure_ascii=False)
    else:
        try:
            extra = json.loads(ent.extra_json)
        except Exception:
            extra = {}
        label = extra.get("regionPathLabel") or ""
        path = extra.get("regionPath") or []
        if "陕西" in label or "南郑" in label or "汉山" in label or "610" in "".join(path):
            extra["regionPath"] = default_extra["regionPath"]
            extra["regionPathLabel"] = default_extra["regionPathLabel"]
            ent.extra_json = json.dumps(extra, ensure_ascii=False)
        county = db.scalar(select(SysRegion).where(SysRegion.code == "330106").limit(1))
        if county:
            ent.region_id = county.id
    db.commit()


def _seed_uav_demo(db: Session) -> None:
    if db.scalar(select(UavPilot).limit(1)):
        return
    p1 = UavPilot(
        project_id=1,
        code="FS20260001",
        name="张航",
        level="AOPA-多旋翼",
        register_date=date(2024, 3, 15),
        flight_hours=128.5,
        violation_count=0,
        attachments="[]",
    )
    p2 = UavPilot(
        project_id=1,
        code="FS20260002",
        name="李飞",
        level="UTC-植保",
        register_date=date(2025, 1, 8),
        flight_hours=56.0,
        violation_count=1,
        attachments="[]",
    )
    db.add_all([p1, p2])
    db.flush()
    db.add(
        UavMission(
            project_id=1,
            code="RW20260001",
            name="示范县示范镇养殖区巡查",
            task_type="日常巡查",
            location="示范县示范镇示范养殖场周边",
            leader="王监管",
            pilot_id=p1.id,
            plan_hours=2.0,
            actual_hours=1.8,
            status="COMPLETED",
            accept_result="QUALIFIED",
            remark="未发现异常",
            images="[]",
            videos="[]",
        )
    )
    db.commit()


def _seed_domestication_demo(db: Session) -> None:
    if db.scalar(select(SpDomesticationPlot).limit(1)):
        return
    db.add_all(
        [
            SpDomesticationPlot(
                project_id=1,
                plot_type="PADDY",
                code="DK20260001",
                area_mu=2.5,
                crop_species="优质稻",
                plant_date=date(2026, 3, 10),
                status="GROWING",
                soil_desc="壤土，有机质丰富",
                irrigation="滴灌",
                cost=12000,
                yield_kg=300,
                income=20000,
                profit=8000,
            ),
            SpDomesticationPlot(
                project_id=1,
                plot_type="PADDY",
                code="DK20260002",
                area_mu=5.0,
                crop_species="籼稻",
                plant_date=date(2026, 3, 15),
                status="GROWING",
                cost=18000,
                yield_kg=500,
                income=33000,
                profit=15000,
            ),
            SpDomesticationPlot(
                project_id=1,
                plot_type="RICE_FISH",
                code="YD20260001",
                area_mu=3.2,
                crop_species="糯稻",
                fish_species="鲤、鲫",
                plant_date=date(2026, 4, 1),
                status="GROWING",
                stocking_kg=150,
                cost=22000,
                rice_yield_kg=280,
                fish_yield_kg=120,
                income=42000,
                profit=20000,
            ),
        ]
    )
    db.add_all(
        [
            SpDomesticationLog(
                project_id=1,
                enterprise_id=1,
                code="XH20260001",
                log_date=date(2026, 5, 1),
                pond_code="1号塘",
                bait_type="鲜活饵料",
                feed_kg=12,
                effect="良好",
            ),
            SpDomesticationLog(
                project_id=1,
                enterprise_id=1,
                code="XH20260002",
                log_date=date(2026, 5, 15),
                pond_code="1号塘",
                bait_type="配合饲料",
                feed_kg=8,
                effect="一般",
            ),
        ]
    )
    db.commit()
