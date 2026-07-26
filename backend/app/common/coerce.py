"""Pydantic helpers: tolerate numeric JSON for string fields (前端 el-input 纯数字场景)."""
from __future__ import annotations

from typing import Annotated, Optional

from pydantic import BeforeValidator


def _as_optional_str(v):
    if v is None or v == "":
        return v
    return str(v)


LooseStr = Annotated[str, BeforeValidator(_as_optional_str)]
OptionalLooseStr = Annotated[Optional[str], BeforeValidator(_as_optional_str)]
