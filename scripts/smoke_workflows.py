# -*- coding: utf-8 -*-
"""冒烟：质量整改 / 指挥调度 / 标识审核 全闭环。"""
import json
import urllib.error
import urllib.request

BASE = "http://127.0.0.1:8000/api/v1"


def req(method, path, token=None, body=None):
    data = None if body is None else json.dumps(body).encode()
    h = {"Content-Type": "application/json"}
    if token:
        h["Authorization"] = f"Bearer {token}"
    r = urllib.request.Request(BASE + path, data=data, headers=h, method=method)
    try:
        with urllib.request.urlopen(r, timeout=20) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="ignore")
        raise RuntimeError(f"{method} {path} -> HTTP{e.code} {body}") from e


def login(u):
    return req("POST", "/auth/login", body={"username": u, "password": "123456"})["data"]["accessToken"]


def main():
    gov = login("gov_admin")
    ent = login("ent_admin")

    print("=== 1 质量整改闭环 ===")
    rects = req("GET", "/quality/rectifications", ent)["data"]
    assert rects and rects[0].get("enterpriseName") not in (None, "", "None"), rects[0]
    print("list fields ok", rects[0].get("enterpriseName"), rects[0].get("pondName"), rects[0].get("status"))
    rid = next((x["id"] for x in rects if x["status"] == "PENDING"), None)
    if not rid:
        # 新建不合格抽检触发整改
        insp = req(
            "POST",
            "/quality/inspections",
            gov,
            {
                "title": "冒烟不合格抽检",
                "species": "大鲵",
                "result": "UNQUALIFIED",
                "enterpriseId": 1,
                "year": 2026,
                "quarter": "Q3",
                "level": "区级",
            },
        )
        print("spawn insp", insp)
        rects = req("GET", "/quality/rectifications", ent)["data"]
        rid = next(x["id"] for x in rects if x["status"] == "PENDING")
    req("POST", f"/quality/rectifications/{rid}/accept", ent)
    req(
        "POST",
        f"/quality/rectifications/{rid}/reply",
        ent,
        {"reply": "已完善用药台账并更换滤网", "rectifyDate": "2026-07-22", "proofFile": "整改证明.jpg"},
    )
    st = next(x for x in req("GET", "/quality/rectifications", gov)["data"] if x["id"] == rid)
    assert st["status"] == "REVIEW", st
    req("POST", f"/quality/rectifications/{rid}/review", gov, {"approved": True, "opinion": "验收通过", "reviewDate": "2026-07-22"})
    st = next(x for x in req("GET", "/quality/rectifications", gov)["data"] if x["id"] == rid)
    assert st["status"] == "CLOSED", st
    print("rect CLOSED ok")

    print("=== 2 指挥调度闭环 ===")
    ds = [d for d in req("GET", "/effluent/dispatches", ent)["data"] if d["status"] == "PENDING" and "?" not in (d.get("title") or "")]
    if not ds:
        req("POST", "/effluent/dispatches", gov, {"title": "冒烟调度", "enterpriseId": 1, "content": "请立即处置", "result": "需处置"})
        ds = [d for d in req("GET", "/effluent/dispatches", ent)["data"] if d["status"] == "PENDING"]
    did = ds[0]["id"]
    req("POST", f"/effluent/dispatches/{did}/accept", ent)
    mid = next(x for x in req("GET", "/effluent/dispatches", ent)["data"] if x["id"] == did)
    assert mid["status"] == "DOING", mid
    req("POST", f"/effluent/dispatches/{did}/feedback", ent, {"feedback": "已按计划排放并监测合格"})
    done = next(x for x in req("GET", "/effluent/dispatches", ent)["data"] if x["id"] == did)
    assert done["status"] == "DONE", done
    print("dispatch DONE ok")

    print("=== 3 标识审核闭环 ===")
    applies = req("GET", "/trace/applies", gov)["data"]
    pending = next((a for a in applies if a["status"] == "PENDING"), None)
    if not pending:
        created = req("POST", "/trace/applies", ent, {"species": "大鲵", "brand": "本地大鲵", "applyQty": 5})
        aid = created["data"]["id"]
    else:
        aid = pending["id"]
    req("POST", f"/trace/applies/{aid}/audit", gov, {"approved": True, "opinion": "同意"})
    req("POST", f"/trace/applies/{aid}/issue", gov)
    final = next(x for x in req("GET", "/trace/applies", gov)["data"] if x["id"] == aid)
    assert final["status"] == "ISSUED", final
    print("trace ISSUED ok")

    print("=== 4 尾水整改闭环 ===")
    efs = req("GET", "/effluent/rectifications", ent)["data"]
    ef = next((x for x in efs if x["status"] == "PENDING"), None)
    if not ef:
        req("POST", "/effluent/rectifications", gov, {"title": "冒烟尾水整改", "enterpriseId": 1, "content": "补标识"})
        ef = next(x for x in req("GET", "/effluent/rectifications", ent)["data"] if x["status"] == "PENDING")
    eid = ef["id"]
    req("POST", f"/effluent/rectifications/{eid}/accept", ent)
    req("POST", f"/effluent/rectifications/{eid}/reply", ent, {"feedback": "已补齐标识牌"})
    req("POST", f"/effluent/rectifications/{eid}/review", gov, {"approved": True, "opinion": "通过"})
    ef2 = next(x for x in req("GET", "/effluent/rectifications", ent)["data"] if x["id"] == eid)
    assert ef2["status"] == "CLOSED", ef2
    print("ef rect CLOSED ok")

    print("=== 5 设备预警闭环 ===")
    alarms = req("GET", "/iot/alarms", ent)["data"]
    assert alarms and alarms[0].get("deviceName"), alarms[:1]
    open_a = next((a for a in alarms if a["status"] == "OPEN"), None)
    if not open_a:
        # 触发低溶氧
        req("POST", "/iot/telemetry", ent, {"deviceId": 1, "pointCode": "DO", "pointValue": 3.5})
        open_a = next(a for a in req("GET", "/iot/alarms", ent)["data"] if a["status"] == "OPEN")
    aid = open_a["id"]
    req("POST", f"/iot/alarms/{aid}/ack", ent)
    mid = next(a for a in req("GET", "/iot/alarms", ent)["data"] if a["id"] == aid)
    assert mid["status"] == "ACK", mid
    req("POST", f"/iot/alarms/{aid}/close", ent)
    closed = next(a for a in req("GET", "/iot/alarms", ent)["data"] if a["id"] == aid)
    assert closed["status"] == "CLOSED", closed
    print("alarm CLOSED ok")

    print("=== 6 尾水排放计划闭环 ===")
    plans = req("GET", "/effluent/plans", gov)["data"]
    assert plans and plans[0].get("enterpriseName") not in ("", None), plans[0]
    draft = next((p for p in plans if p["status"] in ("DRAFT", "REJECTED")), None)
    if not draft:
        created = req(
            "POST",
            "/effluent/plans",
            gov,
            {
                "title": "冒烟排放计划",
                "enterpriseId": 1,
                "planMonth": "2026-08",
                "volume": 80,
                "contactName": "张示范",
                "dischargeStart": "2026-08-01",
            },
        )
        pid = created["data"]["id"]
    else:
        pid = draft["id"]
    req("POST", f"/effluent/plans/{pid}/submit", gov)
    req("POST", f"/effluent/plans/{pid}/file", gov)
    filed = next(p for p in req("GET", "/effluent/plans", gov)["data"] if p["id"] == pid)
    assert filed["status"] == "FILED" and filed.get("fileDate"), filed
    unfiled = req("GET", "/effluent/plans/unfiled-enterprises", gov)["data"]
    print("plan FILED ok, unfiled count", len(unfiled))

    print("=== 7 销售订单闭环 ===")
    created = req(
        "POST",
        "/circulation/sales-orders",
        ent,
        {"buyer": "冒烟客户", "productName": "商品大鲵", "qty": 10, "unitPrice": 200, "deliverDate": "2026-07-28"},
    )
    oid = created["data"]["id"]
    req("POST", f"/circulation/sales-orders/{oid}/confirm", ent)
    req("POST", f"/circulation/sales-orders/{oid}/fulfill", ent)
    order = next(o for o in req("GET", "/circulation/sales-orders", ent)["data"] if o["id"] == oid)
    assert order["status"] == "DONE", order
    transports = req("GET", "/circulation/transports", ent)["data"]
    assert any(t.get("orderId") == oid for t in transports), transports[:3]
    print("sales DONE + transport ok")

    print("ALL WORKFLOWS OK")


if __name__ == "__main__":
    main()
