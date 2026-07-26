"""Audit Pydantic *In models: string fields that reject numeric JSON values (422 risk)."""
from __future__ import annotations

import importlib
import inspect
import pkgutil
from typing import get_args, get_origin

from pydantic import BaseModel
from pydantic.fields import FieldInfo


def _is_str_field(annotation) -> bool:
    if annotation is str:
        return True
    origin = get_origin(annotation)
    if origin is None:
        return False
    args = get_args(annotation)
    if origin is type(str | None):  # Union
        return str in args
    return False


def _sample_for(annotation):
    if _is_str_field(annotation):
        return 17600001314
    origin = get_origin(annotation)
    args = get_args(annotation)
    if origin is list:
        return []
    if annotation is int or (origin is type(int | None) and int in args):
        return 1
    if annotation is float or (origin is type(float | None) and float in args):
        return 1.0
    if annotation is bool:
        return True
    return "demo"


def main() -> None:
    import app.routers as routers_pkg

    risks: list[tuple[str, str, str]] = []
    ok: list[str] = []

    for modinfo in pkgutil.iter_modules(routers_pkg.__path__):
        if modinfo.name.startswith("_"):
            continue
        mod = importlib.import_module(f"app.routers.{modinfo.name}")
        for name, obj in inspect.getmembers(mod):
            if not (inspect.isclass(obj) and issubclass(obj, BaseModel) and obj is not BaseModel):
                continue
            if not name.endswith("In"):
                continue
            fields = getattr(obj, "model_fields", None) or {}
            for fname, finfo in fields.items():
                ann = finfo.annotation
                if not _is_str_field(ann):
                    continue
                payload = {}
                for fn2, fi2 in fields.items():
                    if fn2 == fname:
                        payload[fn2] = 17600001314
                    else:
                        default = fi2.default
                        if default is not None and default is not ... and not isinstance(default, FieldInfo):
                            payload[fn2] = default
                        elif fn2 in ("name", "title", "username", "reply", "feedback", "content", "symptom"):
                            payload[fn2] = "demo"
                        elif fn2.endswith("Id"):
                            payload[fn2] = 1
                try:
                    obj.model_validate(payload)
                    ok.append(f"{modinfo.name}.{name}.{fname}")
                except Exception as exc:
                    risks.append((f"{modinfo.name}.{name}", fname, str(exc)))

    print(f"string_fields_ok={len(ok)} string_fields_risk={len(risks)}")
    for model, field, err in risks:
        short = err.split("\n")[0][:120]
        print(f"RISK {model}.{field}: {short}")


if __name__ == "__main__":
    main()
