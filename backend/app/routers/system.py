from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, field_validator
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.common.response import ApiError, ok
from app.db import get_db
from app.deps import CurrentUser, get_current_user
from app.models import SysAuditLog, SysDictItem, SysDictType, SysMenu, SysRole, SysRoleMenu, SysUser, SysUserRole
from app.security import hash_password

router = APIRouter(prefix="/system", tags=["system"])


def _require_gov(cu: CurrentUser):
    if cu.portal not in ("GOV", "BOTH"):
        raise ApiError(40300, "仅区县可操作", 403)


@router.get("/users")
def list_users(cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    _require_gov(cu)
    q = select(SysUser).where(SysUser.deleted == 0)
    if cu.user.project_id:
        q = q.where((SysUser.project_id == cu.user.project_id) | (SysUser.project_id.is_(None)))
    rows = db.scalars(q.order_by(SysUser.id.desc())).all()
    user_ids = [u.id for u in rows]
    role_map: dict[int, str] = {}
    if user_ids:
        pairs = db.execute(
            select(SysUserRole.user_id, SysRole.code)
            .join(SysRole, SysRole.id == SysUserRole.role_id)
            .where(SysUserRole.user_id.in_(user_ids))
        ).all()
        role_map = {uid: code for uid, code in pairs}
    return ok(
        [
            {
                "id": u.id,
                "username": u.username,
                "realName": u.real_name,
                "userType": u.user_type,
                "enterpriseId": u.enterprise_id,
                "projectId": u.project_id,
                "projectName": "绿色循环渔业试点项目",
                "status": u.status,
                "mobile": u.mobile,
                "roleCode": role_map.get(u.id) or ("COUNTY_ADMIN" if u.user_type == "COUNTY" else "ENT_ADMIN"),
                "roleName": "区县管理员" if u.user_type == "COUNTY" else "企业管理员",
                "orgName": "示范县" if u.user_type == "COUNTY" else "示范养殖场",
                "source": "本地",
            }
            for u in rows
        ]
    )


class UserIn(BaseModel):
    username: str
    password: str = "123456"
    realName: Optional[str] = None
    userType: str = "COUNTY"
    enterpriseId: Optional[int] = None
    roleCode: Optional[str] = None
    mobile: Optional[str] = None

    @field_validator("mobile", mode="before")
    @classmethod
    def _mobile_as_str(cls, v):
        if v is None or v == "":
            return v
        return str(v)


class UserUpdateIn(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None
    realName: Optional[str] = None
    userType: Optional[str] = None
    enterpriseId: Optional[int] = None
    roleCode: Optional[str] = None
    mobile: Optional[str] = None

    @field_validator("mobile", mode="before")
    @classmethod
    def _mobile_as_str(cls, v):
        if v is None or v == "":
            return v
        return str(v)


def _apply_user_role(db: Session, user_id: int, role_code: str | None, user_type: str | None) -> None:
    code = role_code
    if not code and user_type:
        code = "COUNTY_ADMIN" if user_type == "COUNTY" else "ENT_ADMIN"
    if not code:
        return
    role = db.scalar(select(SysRole).where(SysRole.code == code))
    if not role:
        return
    db.execute(delete(SysUserRole).where(SysUserRole.user_id == user_id))
    db.add(SysUserRole(user_id=user_id, role_id=role.id))


@router.post("/users")
def create_user(body: UserIn, cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    _require_gov(cu)
    if db.scalar(select(SysUser).where(SysUser.username == body.username)):
        raise ApiError(40900, "用户名已存在")
    u = SysUser(
        username=body.username,
        password_hash=hash_password(body.password),
        real_name=body.realName or body.username,
        user_type=body.userType,
        enterprise_id=body.enterpriseId,
        project_id=cu.user.project_id,
        mobile=body.mobile,
        status=1,
        data_scope="ENTERPRISE" if body.userType == "ENTERPRISE" else "ALL_COUNTY",
    )
    db.add(u)
    db.flush()
    _apply_user_role(db, u.id, body.roleCode, body.userType)
    db.add(SysAuditLog(user_id=cu.user.id, username=cu.user.username, action="CREATE_USER", resource=body.username))
    db.commit()
    return ok({"id": u.id})


@router.put("/users/{uid}")
def update_user(uid: int, body: UserUpdateIn, cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    _require_gov(cu)
    u = db.get(SysUser, uid)
    if not u or u.deleted:
        raise ApiError(40400, "用户不存在", 404)
    if body.username:
        u.username = body.username
    if body.realName is not None:
        u.real_name = body.realName
    if body.mobile is not None:
        u.mobile = body.mobile
    if body.userType:
        u.user_type = body.userType
        u.data_scope = "ENTERPRISE" if body.userType == "ENTERPRISE" else "ALL_COUNTY"
    if body.enterpriseId is not None:
        u.enterprise_id = body.enterpriseId
    if body.password:
        u.password_hash = hash_password(body.password)
    _apply_user_role(db, u.id, body.roleCode, body.userType or u.user_type)
    db.commit()
    return ok(True)


@router.put("/users/{uid}/status")
def user_status(uid: int, status: int = Query(...), cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    _require_gov(cu)
    u = db.get(SysUser, uid)
    if not u:
        raise ApiError(40400, "用户不存在", 404)
    u.status = status
    db.commit()
    return ok(True)


@router.put("/users/{uid}/reset-password")
def reset_password(uid: int, cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    _require_gov(cu)
    u = db.get(SysUser, uid)
    if not u:
        raise ApiError(40400, "用户不存在", 404)
    u.password_hash = hash_password("123456")
    db.commit()
    return ok(True)


@router.get("/roles")
def list_roles(cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.scalars(select(SysRole).where(SysRole.deleted == 0)).all()
    return ok([{"id": r.id, "code": r.code, "name": r.name, "portal": r.portal, "status": r.status} for r in rows])


@router.get("/dicts/{code}/items")
def dict_items(code: str, db: Session = Depends(get_db)):
    rows = db.scalars(
        select(SysDictItem).where(SysDictItem.type_code == code, SysDictItem.deleted == 0, SysDictItem.status == 1).order_by(SysDictItem.sort_no)
    ).all()
    return ok([{"label": i.label, "value": i.value, "sortNo": i.sort_no} for i in rows])


@router.get("/dict-types")
def dict_types(cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.scalars(select(SysDictType).where(SysDictType.deleted == 0)).all()
    return ok([{"id": t.id, "code": t.code, "name": t.name, "status": t.status} for t in rows])


class DictTypeIn(BaseModel):
    code: str
    name: str


@router.post("/dict-types")
def create_dict_type(body: DictTypeIn, cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    _require_gov(cu)
    t = SysDictType(code=body.code, name=body.name)
    db.add(t)
    db.commit()
    db.refresh(t)
    return ok({"id": t.id})


class DictItemIn(BaseModel):
    typeCode: str
    label: str
    value: str
    sortNo: int = 0


@router.post("/dict-items")
def create_dict_item(body: DictItemIn, cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    _require_gov(cu)
    i = SysDictItem(type_code=body.typeCode, label=body.label, value=body.value, sort_no=body.sortNo)
    db.add(i)
    db.commit()
    db.refresh(i)
    return ok({"id": i.id})


@router.get("/audit-logs")
def audit_logs(page: int = 1, size: int = 20, cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    _require_gov(cu)
    q = select(SysAuditLog).where(SysAuditLog.deleted == 0)
    total = db.scalar(select(func.count()).select_from(q.subquery())) or 0
    rows = db.scalars(q.order_by(SysAuditLog.id.desc()).offset((page - 1) * size).limit(size)).all()
    return ok(
        {
            "list": [
                {
                    "id": a.id,
                    "username": a.username,
                    "action": a.action,
                    "resource": a.resource,
                    "detail": a.detail,
                    "createdAt": a.created_at.isoformat() if a.created_at else None,
                }
                for a in rows
            ],
            "page": page,
            "size": size,
            "total": total,
        }
    )


@router.get("/menus")
def list_menus(cu: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    _require_gov(cu)
    rows = db.scalars(select(SysMenu).where(SysMenu.deleted == 0).order_by(SysMenu.sort_no)).all()
    return ok(
        [
            {
                "id": m.id,
                "parentId": m.parent_id,
                "name": m.name,
                "path": m.path,
                "portal": m.portal,
                "permission": m.permission,
                "type": m.type,
            }
            for m in rows
        ]
    )
