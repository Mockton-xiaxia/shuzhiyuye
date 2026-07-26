"""Smoke test critical edit/create flows for production readiness."""
from __future__ import annotations

import sys

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[1]))

from scripts.accept_full import login, req


def main() -> None:
    ent = login("ent_admin")
    gov = login("gov_admin")
    fails = []

    # staff create + update
    r = req("POST", "/party/staffs", token=ent, body={"name": "测试员", "phone": "13800000099", "post": "饲养"})
    sid = r.get("data", {}).get("id")
    if not sid:
        fails.append("staff create")
    else:
        r2 = req("PUT", f"/party/staffs/{sid}", token=ent, body={"name": "测试员2", "phone": "13800000098", "post": "主管"})
        if r2.get("code") != 0:
            fails.append("staff update")

    # supplier
    r = req("POST", "/inputs/suppliers", token=ent, body={"name": "测试供应商", "category": "FEED", "phone": "13900001111"})
    if r.get("code") != 0:
        fails.append("supplier create")

    # warehouse + customer
    r = req("POST", "/wms/warehouses", token=ent, body={"name": "测试仓", "code": "T01"})
    if r.get("code") != 0:
        fails.append("warehouse create")
    r = req("POST", "/ledger/customers", token=ent, body={"name": "测试客户", "phone": "13700001111"})
    if r.get("code") != 0:
        fails.append("customer create")

    # effluent plan update (find draft)
    plans = req("GET", "/effluent/plans", token=gov)
    plist = plans.get("data") or []
    draft = next((p for p in plist if p.get("status") in ("DRAFT", "REJECTED")), None)
    if draft:
        r = req(
            "PUT",
            f"/effluent/plans/{draft['id']}",
            token=gov,
            body={
                "title": draft.get("title") or "测试计划",
                "enterpriseId": draft.get("enterpriseId") or 1,
                "contactName": "张示范",
                "contactPhone": "13800001111",
                "dischargeStart": "2026-08-01",
                "dischargeEnd": "2026-08-31",
                "volume": 100,
            },
        )
        if r.get("code") != 0:
            fails.append("plan update")

    # feature/update sample
    pol = req("GET", "/quality/policies?page=1&size=1", token=gov)
    pdata = pol.get("data")
    pl = (pdata if isinstance(pdata, list) else pdata.get("list", []))[0]
    r = req(
        "PUT",
        "/feature/update",
        token=gov,
        body={"api": "/quality/policies", "id": pl["id"], "data": {"name": pl["name"], "fileUrl": pl.get("fileUrl"), "publishDate": pl.get("publishDate")}},
    )
    if r.get("code") != 0 or r.get("data", {}).get("soft"):
        fails.append("feature/update policy")

    if fails:
        print("FAIL:", ", ".join(fails))
        raise SystemExit(1)
    print("SMOKE_EDIT_OK")


if __name__ == "__main__":
    main()
