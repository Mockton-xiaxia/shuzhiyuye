from __future__ import annotations

from datetime import date
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.common.response import ApiError
from app.models import BrActivity


def assert_withdrawal_ok(db: Session, batch_id: Optional[int]) -> None:
    if not batch_id:
        return
    today = date.today()
    rows = db.scalars(
        select(BrActivity).where(
            BrActivity.batch_id == batch_id,
            BrActivity.deleted == 0,
            BrActivity.activity_type == "MEDICINE",
            BrActivity.withdrawal_until.is_not(None),
        )
    ).all()
    blocked = [a for a in rows if a.withdrawal_until and a.withdrawal_until > today]
    if blocked:
        latest = max(blocked, key=lambda x: x.withdrawal_until or today)
        raise ApiError(
            40900,
            f"休药期未结束，最早可出塘/赋码日期：{latest.withdrawal_until}（{latest.title}）",
        )
