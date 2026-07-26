# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from pathlib import Path

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models import SysMenu, SysRole, SysRoleMenu

CATALOG_PATH = Path(__file__).with_name("menu_catalog.json")


def load_catalog() -> dict:
    return json.loads(CATALOG_PATH.read_text(encoding="utf-8"))


def _bind(db: Session, role: SysRole | None, menu_id: int) -> None:
    if not role:
        return
    exist = db.scalar(select(SysRoleMenu).where(SysRoleMenu.role_id == role.id, SysRoleMenu.menu_id == menu_id))
    if not exist:
        db.add(SysRoleMenu(role_id=role.id, menu_id=menu_id))


def rebuild_menus_from_catalog(db: Session) -> None:
    """Wipe and recreate GOV/ENT menus to match live catalog names."""
    catalog = load_catalog()
    db.execute(delete(SysRoleMenu))
    db.execute(delete(SysMenu))
    db.commit()

    role_gov = db.scalar(select(SysRole).where(SysRole.code == "COUNTY_ADMIN"))
    role_ent = db.scalar(select(SysRole).where(SysRole.code == "ENT_ADMIN"))

    for portal, role in (("GOV", role_gov), ("ENT", role_ent)):
        items = catalog.get(portal, [])
        groups: dict[str, SysMenu] = {}
        gsort = 0
        leaf_sort: dict[str, int] = {}
        for it in items:
            gname = it["group"]
            if gname not in groups:
                gsort += 1
                g = SysMenu(
                    parent_id=0,
                    name=gname,
                    type=1,
                    path=f"/{portal.lower()}/g/{gsort}",
                    portal=portal,
                    sort_no=gsort,
                    icon="Folder",
                    status=1,
                )
                db.add(g)
                db.flush()
                groups[gname] = g
                leaf_sort[gname] = 0
                _bind(db, role, g.id)
            leaf_sort[gname] += 1
            leaf = SysMenu(
                parent_id=groups[gname].id,
                name=it["name"],
                type=2,
                path=it["path"],
                component=it["path"],
                permission=f"{portal.lower()}:{it['path'].strip('/').replace('/', ':')}",
                portal=portal,
                sort_no=leaf_sort[gname],
                icon="Menu",
                status=1,
            )
            db.add(leaf)
            db.flush()
            _bind(db, role, leaf.id)
        db.flush()
    db.commit()
