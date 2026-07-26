"""全国省 / 市 / 区县划导入（数据来源：pca-code.json）。"""
from __future__ import annotations

import json
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import SysRegion

DATA_FILE = Path(__file__).resolve().parents[1] / "data" / "pca-code.json"


def import_national_regions(db: Session, force: bool = False) -> int:
    """幂等导入全国三级区划。返回新增/更新条数。"""
    if not DATA_FILE.is_file():
        return 0
    existing = db.scalar(select(func.count()).select_from(SysRegion).where(SysRegion.deleted == 0)) or 0
    if existing >= 500 and not force:
        return 0

    tree = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    if not isinstance(tree, list):
        return 0

    code_to_id: dict[str, int] = {}
    for row in db.scalars(select(SysRegion).where(SysRegion.deleted == 0)).all():
        code_to_id[row.code] = row.id

    changed = 0

    def upsert(code: str, name: str, level: int, parent_code: str | None, sort_no: int) -> int:
        nonlocal changed
        parent_id = code_to_id.get(parent_code or "", 0) if parent_code else 0
        row = db.scalar(select(SysRegion).where(SysRegion.code == code).limit(1))
        if row:
            dirty = False
            if row.name != name:
                row.name = name
                dirty = True
            if row.level != level:
                row.level = level
                dirty = True
            if (row.parent_id or 0) != (parent_id or 0):
                row.parent_id = parent_id
                dirty = True
            if row.sort_no != sort_no:
                row.sort_no = sort_no
                dirty = True
            if dirty:
                changed += 1
            code_to_id[code] = row.id
            return row.id
        row = SysRegion(code=code, name=name, level=level, parent_id=parent_id, sort_no=sort_no)
        db.add(row)
        db.flush()
        code_to_id[code] = row.id
        changed += 1
        return row.id

    for pi, prov in enumerate(tree):
        pcode = str(prov["code"])
        upsert(pcode, prov["name"], 1, None, pi + 1)
        for ci, city in enumerate(prov.get("children") or []):
            ccode = str(city["code"])
            upsert(ccode, city["name"], 2, pcode, ci + 1)
            for di, dist in enumerate(city.get("children") or []):
                dcode = str(dist["code"])
                upsert(dcode, dist["name"], 3, ccode, di + 1)

    db.commit()
    return changed
