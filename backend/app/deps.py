from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from fastapi import Depends, Header
from jose import JWTError
from sqlalchemy.orm import Session

from app.common.response import ApiError
from app.db import get_db
from app.models import SysUser
from app.security import decode_token, get_user_by_username, get_user_roles, portal_of


@dataclass
class CurrentUser:
    user: SysUser
    roles: list[str]
    portal: str
    permissions: list[str]


def get_current_user(
    authorization: Optional[str] = Header(default=None),
    db: Session = Depends(get_db),
) -> CurrentUser:
    if not authorization or not authorization.startswith("Bearer "):
        raise ApiError(40100, "未登录", 401)
    token = authorization[7:].strip()
    try:
        payload = decode_token(token)
    except JWTError as e:
        raise ApiError(40100, "登录已失效", 401) from e
    username = payload.get("sub")
    user = get_user_by_username(db, username) if username else None
    if not user or user.status != 1:
        raise ApiError(40100, "用户不可用", 401)
    roles = get_user_roles(db, user.id)
    role_codes = [r.code for r in roles]
    portal = portal_of(roles, user.user_type)
    perms = payload.get("permissions") or []
    return CurrentUser(user=user, roles=role_codes, portal=portal, permissions=list(perms))


def require_portal(*portals: str):
    def _dep(cu: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if cu.portal == "BOTH" or cu.portal in portals:
            return cu
        raise ApiError(40300, "无门户权限", 403)

    return _dep
