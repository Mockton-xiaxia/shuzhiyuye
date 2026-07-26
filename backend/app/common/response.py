from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


def new_trace_id() -> str:
    return uuid.uuid4().hex


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ApiResponse(BaseModel, Generic[T]):
    code: int = 0
    message: str = "ok"
    data: Optional[T] = None
    traceId: str = Field(default_factory=new_trace_id)


class PageResult(BaseModel, Generic[T]):
    list: list[T]
    page: int
    size: int
    total: int


class ApiError(Exception):
    def __init__(self, code: int, message: str, status_code: int = 400):
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)


def ok(data: Any = None, message: str = "ok") -> dict:
    return {"code": 0, "message": message, "data": data, "traceId": new_trace_id()}
