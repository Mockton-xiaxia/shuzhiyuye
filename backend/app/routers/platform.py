from __future__ import annotations

import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, File, Query, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.common.response import ApiError, ok
from app.db import get_db
from app.deps import CurrentUser, get_current_user
from app.models import SysMenu, SysMessage, SysRoleMenu, SysTodo, SysUser
from app.security import (
    create_access_token,
    get_user_by_username,
    get_user_roles,
    portal_of,
    verify_password,
)

router = APIRouter(tags=["platform"])

UPLOAD_ROOT = Path(__file__).resolve().parents[2] / "uploads"
UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)


class LoginIn(BaseModel):
    username: str
    password: str
    rememberMe: bool = True


def build_menu_tree(menus: list[SysMenu], portal: str) -> list[dict]:
    filtered = [m for m in menus if m.portal in (portal, "BOTH") and m.type in (1, 2) and m.status == 1]
    by_parent: dict[int, list[SysMenu]] = {}
    for m in filtered:
        by_parent.setdefault(m.parent_id, []).append(m)
    for lst in by_parent.values():
        lst.sort(key=lambda x: x.sort_no)

    def walk(pid: int) -> list[dict]:
        nodes = []
        for m in by_parent.get(pid, []):
            nodes.append(
                {
                    "id": m.id,
                    "name": m.name,
                    "path": m.path,
                    "component": m.component,
                    "permission": m.permission,
                    "icon": m.icon,
                    "children": walk(m.id),
                }
            )
        return nodes

    return walk(0)


def collect_permissions(db: Session, role_ids: list[int]) -> list[str]:
    if not role_ids:
        return []
    menus = db.scalars(
        select(SysMenu)
        .join(SysRoleMenu, SysRoleMenu.menu_id == SysMenu.id)
        .where(SysRoleMenu.role_id.in_(role_ids), SysMenu.permission.is_not(None))
    ).all()
    return sorted({m.permission for m in menus if m.permission})


@router.post("/auth/login")
def login(body: LoginIn, db: Session = Depends(get_db)):
    user = get_user_by_username(db, body.username)
    if not user or not verify_password(body.password, user.password_hash):
        raise ApiError(40100, "用户名或密码错误", 401)
    roles = get_user_roles(db, user.id)
    portal = portal_of(roles, user.user_type)
    perms = collect_permissions(db, [r.id for r in roles])
    token = create_access_token(
        {
            "sub": user.username,
            "uid": user.id,
            "portal": portal,
            "projectId": user.project_id,
            "enterpriseId": user.enterprise_id,
            "permissions": perms,
        }
    )
    return ok(
        {
            "accessToken": token,
            "refreshToken": token,
            "expiresIn": 7200,
            "user": {
                "id": user.id,
                "username": user.username,
                "realName": user.real_name,
                "userType": user.user_type,
                "portal": portal,
                "projectId": user.project_id,
                "enterpriseId": user.enterprise_id,
            },
            "roles": [r.code for r in roles],
            "permissions": perms,
        }
    )


@router.post("/auth/logout")
def logout(cu: CurrentUser = Depends(get_current_user)):
    return ok(True)


@router.get("/auth/me")
def me(cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    roles = get_user_roles(db, cu.user.id)
    portal = portal_of(roles, cu.user.user_type)
    menus = db.scalars(select(SysMenu).where(SysMenu.deleted == 0)).all()
    # filter by role
    role_ids = [r.id for r in roles]
    allowed_ids = set(
        db.scalars(select(SysRoleMenu.menu_id).where(SysRoleMenu.role_id.in_(role_ids))).all()
    )
    my_menus = [m for m in menus if m.id in allowed_ids]
    return ok(
        {
            "user": {
                "id": cu.user.id,
                "username": cu.user.username,
                "realName": cu.user.real_name,
                "userType": cu.user.user_type,
                "portal": portal,
                "projectId": cu.user.project_id,
                "enterpriseId": cu.user.enterprise_id,
                "regionId": cu.user.region_id,
            },
            "roles": [r.code for r in roles],
            "permissions": collect_permissions(db, role_ids),
            "menus": build_menu_tree(my_menus, portal if portal != "BOTH" else "GOV"),
            "menusEnt": build_menu_tree(my_menus, "ENT") if portal == "BOTH" else None,
        }
    )


@router.get("/system/menus/tree")
def menu_tree(cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    roles = get_user_roles(db, cu.user.id)
    portal = portal_of(roles, cu.user.user_type)
    role_ids = [r.id for r in roles]
    allowed_ids = set(
        db.scalars(select(SysRoleMenu.menu_id).where(SysRoleMenu.role_id.in_(role_ids))).all()
    )
    menus = [m for m in db.scalars(select(SysMenu).where(SysMenu.deleted == 0)).all() if m.id in allowed_ids]
    return ok(build_menu_tree(menus, "GOV" if portal == "GOV" else "ENT"))


@router.get("/todos")
def list_todos(
    status: Optional[str] = None,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    cu: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = select(SysTodo).where(SysTodo.deleted == 0)
    if cu.portal == "GOV":
        q = q.where(SysTodo.portal == "GOV")
        if cu.user.project_id:
            q = q.where(SysTodo.project_id == cu.user.project_id)
    else:
        q = q.where(SysTodo.portal == "ENT")
        if cu.user.enterprise_id:
            q = q.where(SysTodo.enterprise_id == cu.user.enterprise_id)
    if status:
        q = q.where(SysTodo.status == status)
    total = db.scalar(select(func.count()).select_from(q.subquery())) or 0
    rows = db.scalars(q.order_by(SysTodo.id.desc()).offset((page - 1) * size).limit(size)).all()
    return ok(
        {
            "list": [
                {
                    "id": t.id,
                    "title": t.title,
                    "bizType": t.biz_type,
                    "bizId": t.biz_id,
                    "status": t.status,
                    "portal": t.portal,
                    "linkPath": t.link_path,
                    "enterpriseId": t.enterprise_id,
                }
                for t in rows
            ],
            "page": page,
            "size": size,
            "total": total,
        }
    )


class TodoDoneIn(BaseModel):
    pass


@router.post("/todos/{todo_id}/done")
def done_todo(todo_id: int, cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    todo = db.get(SysTodo, todo_id)
    if not todo or todo.deleted:
        raise ApiError(40400, "待办不存在", 404)
    todo.status = "DONE"
    db.commit()
    return ok(True)


@router.get("/messages")
def messages(cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.scalars(
        select(SysMessage).where(SysMessage.user_id == cu.user.id, SysMessage.deleted == 0).limit(50)
    ).all()
    return ok([{"id": m.id, "title": m.title, "content": m.content, "readFlag": m.read_flag} for m in rows])


@router.post("/platform/upload")
async def upload_file(
    file: UploadFile = File(...),
    cu: CurrentUser = Depends(get_current_user),
):
    """政策/附件上传（演示：落盘 uploads/，返回可访问 URL）。"""
    _ = cu
    raw_name = file.filename or "file.bin"
    ext = Path(raw_name).suffix or ".bin"
    safe = f"{uuid.uuid4().hex}{ext}"
    dest = UPLOAD_ROOT / safe
    content = await file.read()
    if len(content) > 20 * 1024 * 1024:
        raise ApiError(40000, "文件不能超过 20MB")
    dest.write_bytes(content)
    return ok({"url": f"/uploads/{safe}", "fileName": raw_name})
