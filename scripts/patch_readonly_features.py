"""Mark readonly CrudPage features: stats/monitor/query-only pages."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FEATURES = ROOT / "frontend/apps/admin/src/catalog/features.json"

READONLY_PATHS = {
    "/gov/quality/stats-mgmt",
    "/gov/trace/codes",
    "/gov/trace/label-stats",
    "/ent/iot/telemetry",
    "/ent/iot/water-lab",
    "/ent/iot/tailwater",
    "/ent/iot/weather",
    "/ent/ledger/fees",
    "/ent/ledger/purchase-history",
    "/ent/ledger/portrait",
    "/ent/ledger/budgets",
    "/ent/ledger/analysis",
    "/ent/trace/codes",
}

READONLY_APIS = {
    "/quality/stats-records",
    "/trace/codes",
    "/trace/label-stats",
    "/iot/telemetry",
    "/iot/water-lab",
    "/iot/weather",
    "/ledger/fees",
    "/ledger/purchase-history",
    "/ledger/portrait",
    "/ledger/budgets",
    "/ledger/analysis",
}


def main() -> None:
    data = json.loads(FEATURES.read_text(encoding="utf-8"))
    n = 0
    for portal in ("GOV", "ENT"):
        for feat in data.get(portal, []):
            path = feat.get("path") or ""
            api = (feat.get("api") or "").split("?")[0]
            if path in READONLY_PATHS or api in READONLY_APIS or "telemetry?type=TAILWATER" in (feat.get("api") or ""):
                feat["readonly"] = True
                feat["buttons"] = ["query", "reset", "export"]
                n += 1
                print(f"  readonly: {feat.get('name')} ({path})")
    FEATURES.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Updated {n} features")


if __name__ == "__main__":
    main()
