from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import SysRole, SysUser, SysUserRole

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
settings = get_settings()


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)


def create_access_token(claims: dict[str, Any], minutes: Optional[int] = None) -> str:
    payload = claims.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=minutes or settings.access_token_minutes)
    payload["exp"] = expire
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_alg)


def decode_token(token: str) -> dict[str, Any]:
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_alg])


def get_user_by_username(db: Session, username: str) -> Optional[SysUser]:
    return db.scalar(select(SysUser).where(SysUser.username == username, SysUser.deleted == 0))


def get_user_roles(db: Session, user_id: int) -> list[SysRole]:
    rows = db.execute(
        select(SysRole)
        .join(SysUserRole, SysUserRole.role_id == SysRole.id)
        .where(SysUserRole.user_id == user_id, SysRole.deleted == 0)
    ).scalars().all()
    return list(rows)


def portal_of(roles: list[SysRole], user_type: str) -> str:
    if any(r.portal == "GOV" for r in roles) or user_type == "COUNTY":
        if any(r.portal == "ENT" for r in roles):
            return "BOTH"
        return "GOV"
    if user_type == "ENTERPRISE" or any(r.portal == "ENT" for r in roles):
        return "ENT"
    return "GOV"
