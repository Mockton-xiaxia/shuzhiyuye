from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    BizEnterprise,
    BizPond,
    BrActivity,
    BrBatch,
    CmsArticle,
    EfDischargePlan,
    EfWaterBody,
    InItem,
    InSupplier,
    IotAlarm,
    IotCamera,
    IotDevice,
    IotRule,
    LgCustomer,
    QaInspection,
    QaPolicy,
    QaRectification,
    SpecialtySalamander,
    SysMenu,
    SysProject,
    SysRegion,
    SysRole,
    SysRoleMenu,
    SysTodo,
    SysUser,
    SysUserRole,
    TrMarkApply,
    TrMarkCode,
    WmStock,
    WmWarehouse,
)
from app.security import hash_password


def _menu(db: Session, **kwargs) -> SysMenu:
    m = SysMenu(**kwargs)
    db.add(m)
    db.flush()
    return m


def seed_if_empty(db: Session) -> None:
    if db.scalar(select(SysUser).limit(1)):
        return

    region = SysRegion(code="330106", name="西湖区", level=3, parent_id=0)
    db.add(region)
    db.flush()

    project = SysProject(
        region_id=region.id,
        code="nz-green-cycle",
        name="绿色循环渔业试点项目",
        screen_title="区县渔业总体情况",
    )
    db.add(project)
    db.flush()

    ent = BizEnterprise(
        project_id=project.id,
        region_id=region.id,
        name="示范养殖场",
        code="YXF001",
        contact_name="张示范",
        contact_phone="13891651431",
        address="浙江省杭州市西湖区",
        lng=120.149506,
        lat=30.242726,
        area_mu=65,
        species="大鲵,草鱼,鲢,鲤,鲫",
        subject_type="INDIVIDUAL",
        status="APPROVED",
        intro="绿色循环渔业试点示范主体，主养大鲵及常规鱼类，配套尾水处理与质量追溯。",
    )
    db.add(ent)
    db.flush()

    role_gov = SysRole(code="COUNTY_ADMIN", name="区县管理员", portal="GOV")
    role_ent = SysRole(code="ENT_ADMIN", name="企业管理员", portal="ENT")
    db.add_all([role_gov, role_ent])
    db.flush()

    u_gov = SysUser(
        username="gov_admin",
        password_hash=hash_password("123456"),
        real_name="区县管理员",
        user_type="COUNTY",
        region_id=region.id,
        project_id=project.id,
        data_scope="ALL_COUNTY",
    )
    u_ent = SysUser(
        username="ent_admin",
        password_hash=hash_password("123456"),
        real_name="张示范",
        mobile="13891651431",
        user_type="ENTERPRISE",
        enterprise_id=ent.id,
        project_id=project.id,
        data_scope="ENTERPRISE",
    )
    db.add_all([u_gov, u_ent])
    db.flush()
    db.add_all(
        [
            SysUserRole(user_id=u_gov.id, role_id=role_gov.id),
            SysUserRole(user_id=u_ent.id, role_id=role_ent.id),
        ]
    )

    # menus
    menus: list[SysMenu] = []

    def add(parent_id: int, name: str, path: str, portal: str, perm: str, sort_no: int, component: str = ""):
        m = _menu(
            db,
            parent_id=parent_id,
            name=name,
            type=2,
            path=path,
            component=component or path,
            permission=perm,
            portal=portal,
            sort_no=sort_no,
            icon="Menu",
        )
        menus.append(m)
        return m

    work_gov = _menu(db, parent_id=0, name="工作台", type=1, path="/gov/workbench", portal="GOV", sort_no=1, icon="HomeFilled")
    add(work_gov.id, "我的待办", "/gov/workbench/todos", "GOV", "todo:list", 1)
    add(work_gov.id, "一张图", "/gov/map", "GOV", "map:view", 2)
    add(work_gov.id, "领导驾驶舱", "/gov/cockpit", "GOV", "analytics:cockpit", 3)

    q = _menu(db, parent_id=0, name="质量安全", type=1, path="/gov/quality", portal="GOV", sort_no=2, icon="Medal")
    add(q.id, "政策管理", "/gov/quality/policies", "GOV", "quality:policy:list", 1)
    add(q.id, "质量抽检", "/gov/quality/inspections", "GOV", "quality:inspection:list", 2)
    add(q.id, "质量整改", "/gov/quality/rectifications", "GOV", "quality:rectification:list", 3)

    t = _menu(db, parent_id=0, name="追溯标识", type=1, path="/gov/trace", portal="GOV", sort_no=3, icon="Ticket")
    add(t.id, "标识审核", "/gov/trace/applies", "GOV", "trace:apply:audit", 1)
    add(t.id, "标识分发", "/gov/trace/codes", "GOV", "trace:code:list", 2)

    e = _menu(db, parent_id=0, name="尾水监管", type=1, path="/gov/effluent", portal="GOV", sort_no=4, icon="Pouring")
    add(e.id, "排放水域", "/gov/effluent/waters", "GOV", "effluent:water:list", 1)
    add(e.id, "排放计划", "/gov/effluent/plans", "GOV", "effluent:plan:list", 2)

    p = _menu(db, parent_id=0, name="主体资源", type=1, path="/gov/party", portal="GOV", sort_no=5, icon="OfficeBuilding")
    add(p.id, "养殖主体", "/gov/party/enterprises", "GOV", "party:enterprise:list", 1)
    add(p.id, "塘口审核", "/gov/party/ponds", "GOV", "party:pond:audit", 2)

    c = _menu(db, parent_id=0, name="产业资讯", type=1, path="/gov/cms", portal="GOV", sort_no=6, icon="Document")
    add(c.id, "文章资讯", "/gov/cms/articles", "GOV", "cms:article:list", 1)

    sp = _menu(db, parent_id=0, name="大鲵专项", type=1, path="/gov/specialty", portal="GOV", sort_no=7, icon="Fish")
    add(sp.id, "病害检测", "/gov/specialty/salamander", "GOV", "specialty:salamander:list", 1)

    # enterprise
    ew = _menu(db, parent_id=0, name="工作台", type=1, path="/ent/workbench", portal="ENT", sort_no=1, icon="HomeFilled")
    add(ew.id, "我的待办", "/ent/workbench/todos", "ENT", "todo:list", 1)
    add(ew.id, "企业大屏", "/ent/screen", "ENT", "analytics:ent-screen", 2)

    base = _menu(db, parent_id=0, name="我的基地", type=1, path="/ent/base", portal="ENT", sort_no=2, icon="Place")
    add(base.id, "主体信息", "/ent/base/enterprise", "ENT", "party:enterprise:self", 1)
    add(base.id, "塘口测绘", "/ent/base/ponds", "ENT", "party:pond:edit", 2)

    breed = _menu(db, parent_id=0, name="养殖生产", type=1, path="/ent/breeding", portal="ENT", sort_no=3, icon="Cherry")
    add(breed.id, "养殖批次", "/ent/breeding/batches", "ENT", "breeding:batch:list", 1)
    add(breed.id, "农事记录", "/ent/breeding/activities", "ENT", "breeding:activity:list", 2)

    iot = _menu(db, parent_id=0, name="物联中心", type=1, path="/ent/iot", portal="ENT", sort_no=4, icon="Cpu")
    add(iot.id, "水质设备", "/ent/iot/devices", "ENT", "iot:device:list", 1)
    add(iot.id, "视频监控", "/ent/iot/cameras", "ENT", "iot:camera:list", 2)
    add(iot.id, "设备预警", "/ent/iot/alarms", "ENT", "iot:alarm:list", 3)

    wms = _menu(db, parent_id=0, name="仓储经营", type=1, path="/ent/ops", portal="ENT", sort_no=5, icon="Box")
    add(wms.id, "仓库库存", "/ent/ops/warehouse", "ENT", "wms:stock:list", 1)
    add(wms.id, "投入品", "/ent/ops/inputs", "ENT", "input:item:list", 2)
    add(wms.id, "客户账本", "/ent/ops/ledger", "ENT", "ledger:list", 3)

    qt = _menu(db, parent_id=0, name="质量追溯", type=1, path="/ent/quality", portal="ENT", sort_no=6, icon="Stamp")
    add(qt.id, "标识申请", "/ent/quality/trace-apply", "ENT", "trace:apply:create", 1)
    add(qt.id, "质量整改", "/ent/quality/rectifications", "ENT", "quality:rectification:ent", 2)
    add(qt.id, "资讯行情", "/ent/cms/articles", "ENT", "cms:article:read", 3)

    db.flush()
    for m in db.scalars(select(SysMenu)).all():
        if m.portal in ("GOV", "BOTH"):
            db.add(SysRoleMenu(role_id=role_gov.id, menu_id=m.id))
        if m.portal in ("ENT", "BOTH"):
            db.add(SysRoleMenu(role_id=role_ent.id, menu_id=m.id))

    pond = BizPond(
        project_id=project.id,
        enterprise_id=ent.id,
        code="TK-001",
        name="1号养殖塘",
        pond_type="池塘",
        area_mu=28.88,
        species="大鲵",
        township="北山街道",
        lng=120.151,
        lat=30.244,
        geom_geojson='{"type":"Polygon","coordinates":[[[120.150,30.243],[120.152,30.243],[120.152,30.245],[120.150,30.245],[120.150,30.243]]]}',
        layer_type="AQUACULTURE",
        audit_status="APPROVED",
    )
    db.add(pond)
    db.flush()

    db.add(
        SysTodo(
            project_id=project.id,
            enterprise_id=ent.id,
            title="待审核塘口：1号养殖塘",
            biz_type="POND_AUDIT",
            biz_id=pond.id,
            status="PENDING",
            portal="GOV",
            assignee_role="COUNTY_ADMIN",
            link_path="/gov/party/ponds",
        )
    )

    batch = BrBatch(
        project_id=project.id,
        enterprise_id=ent.id,
        pond_id=pond.id,
        batch_no="B2026-001",
        species="大鲵",
        stock_qty=500,
        stock_date=date(2026, 3, 1),
        status="BREEDING",
        feed_total_kg=120,
    )
    db.add(batch)
    db.flush()
    db.add(
        BrActivity(
            project_id=project.id,
            enterprise_id=ent.id,
            batch_id=batch.id,
            pond_id=pond.id,
            activity_type="FEED",
            title="投喂配合饲料",
            qty=20,
            unit="kg",
            occurred_at=datetime.now(timezone.utc),
        )
    )

    db.add(QaPolicy(project_id=project.id, name="示范县水产品质量安全监管办法", publish_date=date(2026, 1, 1)))
    insp = QaInspection(
        project_id=project.id,
        enterprise_id=ent.id,
        pond_id=pond.id,
        batch_id=batch.id,
        title="一季度抽检",
        status="SUBMITTED",
        result="UNQUALIFIED",
        inspected_at=datetime.now(timezone.utc),
    )
    db.add(insp)
    db.flush()
    rect = QaRectification(
        project_id=project.id,
        enterprise_id=ent.id,
        inspection_id=insp.id,
        title="一季度抽检不合格整改",
        status="PENDING",
        content="请限期整改用药记录与水质管理",
    )
    db.add(rect)
    db.flush()
    db.add(
        SysTodo(
            project_id=project.id,
            enterprise_id=ent.id,
            title="待处理整改：一季度抽检不合格",
            biz_type="QA_RECTIFICATION",
            biz_id=rect.id,
            status="PENDING",
            portal="ENT",
            link_path="/ent/quality/rectifications",
        )
    )

    apply = TrMarkApply(
        project_id=project.id,
        enterprise_id=ent.id,
        batch_id=batch.id,
        apply_qty=10,
        status="PENDING",
    )
    db.add(apply)
    db.flush()
    db.add(
        SysTodo(
            project_id=project.id,
            enterprise_id=ent.id,
            title="标识申请待审核",
            biz_type="TRACE_APPLY",
            biz_id=apply.id,
            status="PENDING",
            portal="GOV",
            link_path="/gov/trace/applies",
        )
    )

    water = EfWaterBody(project_id=project.id, name="示范支流演示水域", code="HJ-01", level="Ⅲ")
    db.add(water)
    db.flush()
    db.add(
        EfDischargePlan(
            project_id=project.id,
            enterprise_id=ent.id,
            water_body_id=water.id,
            title="2026-07 排放计划",
            plan_month="2026-07",
            volume=100,
            status="SUBMITTED",
        )
    )

    supplier = InSupplier(enterprise_id=ent.id, project_id=project.id, name="本地饲料厂", category="FEED")
    db.add(supplier)
    db.flush()
    item = InItem(
        enterprise_id=ent.id,
        project_id=project.id,
        supplier_id=supplier.id,
        name="膨化饲料",
        category="FEED",
        unit="kg",
        withdrawal_days=0,
    )
    med = InItem(
        enterprise_id=ent.id,
        project_id=project.id,
        supplier_id=supplier.id,
        name="渔药A",
        category="MEDICINE",
        unit="瓶",
        withdrawal_days=7,
    )
    db.add_all([item, med])
    db.flush()
    wh = WmWarehouse(project_id=project.id, enterprise_id=ent.id, name="饲料仓", code="WH-01")
    db.add(wh)
    db.flush()
    db.add(WmStock(warehouse_id=wh.id, enterprise_id=ent.id, item_id=item.id, qty=1000))
    db.add(LgCustomer(enterprise_id=ent.id, name="本地水产批发商", phone="13900000000"))

    device = IotDevice(
        project_id=project.id,
        enterprise_id=ent.id,
        pond_id=pond.id,
        name="室外水质监测1",
        device_no="nanzheng-kms-10773",
        device_type="WATER",
        status="ONLINE",
    )
    db.add(device)
    db.flush()
    cam = IotCamera(
        project_id=project.id,
        enterprise_id=ent.id,
        pond_id=pond.id,
        name="唐湾庄",
        provider="EZVIZ",
        device_serial="GN2548932",
        channel_no=1,
        scene="POND",
    )
    db.add(cam)
    db.flush()
    db.add(
        IotRule(
            enterprise_id=ent.id,
            device_id=device.id,
            name="溶氧过低",
            point_code="DO",
            operator="LT",
            threshold=5.0,
        )
    )
    db.add(
        IotAlarm(
            project_id=project.id,
            enterprise_id=ent.id,
            device_id=device.id,
            camera_id=cam.id,
            alarm_type="WATER_DO",
            title="溶氧偏低告警（演示）",
            content="DO=4.2 < 5.0",
            status="OPEN",
            occurred_at=datetime.now(timezone.utc),
        )
    )

    db.add(
        CmsArticle(
            project_id=project.id,
            title="寄生虫介绍之大鲵复口吸虫病",
            category="科普知识",
            content="演示资讯正文",
            source="外部维护",
            recommend=1,
            ent_visible=1,
        )
    )
    db.add(
        SpecialtySalamander(
            project_id=project.id,
            enterprise_id=ent.id,
            record_type="DISEASE",
            title="大鲵病害检测记录（演示）",
            content="检测正常",
        )
    )

    # issued sample code for public trace
    code = TrMarkCode(
        project_id=project.id,
        enterprise_id=ent.id,
        apply_id=apply.id,
        batch_id=batch.id,
        code="NZTRACE20260001",
        status="BOUND",
    )
    db.add(code)
    db.commit()
