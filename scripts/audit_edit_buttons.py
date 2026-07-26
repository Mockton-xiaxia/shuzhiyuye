"""Audit edit-button coverage: CrudPage APIs vs backend PUT / feature/update."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FEATURES = json.loads((ROOT / "frontend/apps/admin/src/catalog/features.json").read_text(encoding="utf-8"))

DIRECT_PUT = {
    "/system/users",
    "/quality/policies",
    "/effluent/policies",
    "/party/enterprises",
    "/party/ponds",
    "/party/staffs",
    "/quality/labs",
    "/breeding/batches",
    "/breeding/activities",
    "/breeding/sales",
    "/circulation/transports",
    "/iot/rules",
    "/iot/cameras",
    "/disease/alerts",
    "/effluent/patrols",
    "/effluent/plans",
}

FEATURE_UPDATE = {
    "/quality/labs",
    "/quality/policies",
    "/supply/listings",
    "/supply/markets",
    "/supply/prices",
    "/effluent/waters",
    "/cms/articles",
    "/cms/categories",
    "/cms/videos",
    "/inputs/items",
    "/inputs/suppliers",
    "/party/staffs",
    "/breeding/batches",
    "/breeding/activities",
    "/breeding/sales",
    "/ledger/customers",
    "/ledger/contracts",
    "/ledger/after-sales",
    "/ledger/entries",
    "/wms/warehouses",
    "/wms/stocks",
    "/wms/inbounds",
    "/wms/outbounds",
    "/wms/stocktakes",
    "/circulation/transports",
    "/iot/rules",
    "/iot/cameras",
    "/disease/alerts",
    "/effluent/patrols",
    "/specialty/disease-tests",
    "/quality/inspections",
    "/party/ponds",
}

DEDICATED_WORKBENCH = {
    "/effluent/plans",
    "/quality/inspections",
    "/quality/self-checks",
    "/quality/rectifications",
    "/trace/applies",
    "/effluent/dispatches",
    "/effluent/rectifications",
    "/iot/alarms",
    "/circulation/sales-orders",
    "/party/enterprises",
    "/specialty/domestication",
    "/uav/patrol",
}

READONLY_OR_STATS = {
    "/analytics/cockpit",
    "/analytics/enterprise-screen",
    "/quality/stats-records",
    "/trace/label-stats",
    "/trace/codes",
    "/ledger/portrait",
    "/ledger/analysis",
    "/ledger/fees",
    "/ledger/purchase-history",
    "/ledger/budgets",
    "/iot/telemetry",
    "/iot/water-lab",
    "/iot/weather",
    "/iot/commands",
    "/specialty/domestication/stats",
    "/specialty/processing",
    "/specialty/transports",
    "/wms/warehouse-equip",
    "/uav/stats",
    "/party/gis/layers",
    "/iot/ezviz/config",
}


def base_api(api: str | None) -> str | None:
    if not api:
        return None
    return api.split("?")[0].rstrip("/")


WORKBENCH_PATHS = (
    "/quality/rectifications",
    "/trace/applies",
    "/quality/self-checks",
    "/quality/trace-apply",
    "/effluent/plans",
    "/effluent/dispatches",
    "/effluent/rectifications",
    "/iot/alarms",
    "/circulation/sales",
    "/circulation/match",
)


def classify(feat: dict) -> str:
    shape = feat.get("shape")
    path = feat.get("path") or ""
    api = base_api(feat.get("api"))

    if feat.get("readonly"):
        return "readonly_crud"

    if any(seg in path for seg in WORKBENCH_PATHS):
        return "workbench_crud"

    if shape != "crud":
        if shape in ("workbench", "gis", "screen", "sso", "ezviz", "enterprise", "domestication", "uav"):
            return "workbench"
        return "other"

    if path in READONLY_OR_STATS or api in READONLY_OR_STATS:
        return "readonly_crud"

    if api in DIRECT_PUT:
        return "direct_put"

    if api in FEATURE_UPDATE:
        return "feature_update"

    return "soft_or_none"


def main() -> None:
    rows = []
    for portal in ("GOV", "ENT"):
        for feat in FEATURES.get(portal, []):
            if feat.get("shape") != "crud":
                continue
            api = base_api(feat.get("api"))
            cat = classify(feat)
            rows.append(
                {
                    "portal": portal,
                    "name": feat.get("name"),
                    "path": feat.get("path"),
                    "api": feat.get("api"),
                    "category": cat,
                }
            )

    from collections import Counter

    c = Counter(r["category"] for r in rows)
    print("CRUD pages by edit support:")
    for k, v in sorted(c.items()):
        print(f"  {k}: {v}")

    soft = [r for r in rows if r["category"] == "soft_or_none"]
    print(f"\n--- soft_or_none ({len(soft)}) ---")
    for r in soft:
        print(f"  [{r['portal']}] {r['name']} -> {r['api']}")

    if soft:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
