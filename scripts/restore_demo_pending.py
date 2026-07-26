# -*- coding: utf-8 -*-
"""恢复可演示的 PENDING 单据（冒烟消耗后补种）。"""
from app.db import SessionLocal
from app.seed_upgrade import upgrade_seed
from app.models import QaRectification, TrMarkApply, EfDispatch, EfRectification, SysTodo
from sqlalchemy import select


def main():
    db = SessionLocal()
    upgrade_seed(db)

    if not db.scalar(select(QaRectification).where(QaRectification.status == "PENDING", QaRectification.deleted == 0).limit(1)):
        r = QaRectification(
            project_id=1,
            enterprise_id=1,
            inspection_id=1,
            title="待接收-演示整改",
            status="PENDING",
            content="请接收并回复整改说明",
        )
        db.add(r)
        db.flush()
        db.add(
            SysTodo(
                project_id=1,
                enterprise_id=1,
                title="待处理整改：待接收-演示整改",
                biz_type="QA_RECTIFICATION",
                biz_id=r.id,
                status="PENDING",
                portal="ENT",
                link_path="/ent/quality/rectifications",
            )
        )

    if not db.scalar(select(TrMarkApply).where(TrMarkApply.status == "PENDING", TrMarkApply.deleted == 0).limit(1)):
        a = TrMarkApply(
            project_id=1,
            enterprise_id=1,
            batch_id=1,
            apply_qty=15,
            status="PENDING",
            remark='{"species":"大鲵","brand":"本地大鲵"}',
        )
        db.add(a)
        db.flush()
        db.add(
            SysTodo(
                project_id=1,
                enterprise_id=1,
                title="标识申请待审核",
                biz_type="TRACE_APPLY",
                biz_id=a.id,
                status="PENDING",
                portal="GOV",
                link_path="/gov/trace/applies",
            )
        )

    if not db.scalar(select(EfDispatch).where(EfDispatch.status == "PENDING", EfDispatch.deleted == 0).limit(1)):
        db.add(
            EfDispatch(
                project_id=1,
                enterprise_id=1,
                title="尾水排放调度提醒",
                content="请按计划排放并做好监测",
                status="PENDING",
                remark='{"officerName":"区县渔政执法","labName":"区县水产检测中心","result":"需处置","unqualified":"COD偏高"}',
            )
        )

    if not db.scalar(select(EfRectification).where(EfRectification.status == "PENDING", EfRectification.deleted == 0).limit(1)):
        db.add(
            EfRectification(
                project_id=1,
                enterprise_id=1,
                title="排放口标识不完善",
                content="请补齐排放口标识牌并拍照回传",
                status="PENDING",
            )
        )

    # 设备预警保持可确认
    from app.models import IotAlarm, EfDischargePlan, CiSalesOrder
    from datetime import datetime, timezone

    if not db.scalar(select(IotAlarm).where(IotAlarm.status == "OPEN", IotAlarm.deleted == 0).limit(1)):
        db.add(
            IotAlarm(
                project_id=1,
                enterprise_id=1,
                device_id=1,
                alarm_type="WATER_DO",
                title="溶氧偏低告警",
                content="DO=4.2 LT 5.0",
                status="OPEN",
                occurred_at=datetime.now(timezone.utc),
            )
        )

    # 排放计划草稿
    if not db.scalar(select(EfDischargePlan).where(EfDischargePlan.status.in_(["DRAFT", "SUBMITTED"]), EfDischargePlan.deleted == 0).limit(1)):
        db.add(
            EfDischargePlan(
                project_id=1,
                enterprise_id=1,
                water_body_id=1,
                title="2026-07 尾水排放计划",
                plan_month="2026-07",
                volume=120,
                status="DRAFT",
                remark='{"contactName":"张示范","contactPhone":"13800001111","dischargeStart":"2026-07-01","dischargeEnd":"2026-07-31"}',
            )
        )

    # 销售订单草稿
    if not db.scalar(select(CiSalesOrder).where(CiSalesOrder.status.in_(["DRAFT", "CREATED"]), CiSalesOrder.deleted == 0).limit(1)):
        db.add(
            CiSalesOrder(
                project_id=1,
                enterprise_id=1,
                order_no="SO20260722001",
                buyer="本地水产批发商",
                amount=9000,
                status="DRAFT",
                remark='{"productName":"商品大鲵","qty":50,"unitPrice":180,"orderDate":"2026-07-22","deliverDate":"2026-07-30"}',
            )
        )

    db.commit()
    print("demo pending restored")
    db.close()


if __name__ == "__main__":
    main()
