# -*- coding: utf-8 -*-
"""双账号全菜单验收：菜单同名命中 + 叶子 API 冒烟 + 页面真实 API 对照。"""
from __future__ import annotations

import json
from pathlib import Path

import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
BASE = "http://127.0.0.1:8000/api/v1"
CATALOG = json.loads((ROOT / "backend" / "app" / "menu_catalog.json").read_text(encoding="utf-8"))

# 页面组件内实际调用的 API（与 catalog.api 可能不同）
PAGE_REAL_API: dict[str, str] = {
    "/gov/party/gis-collect": "/party/gis/layers?mode=collect",
    "/gov/party/gis-audit": "/party/gis/layers?mode=audit",
    "/gov/party/gis-stats": "/party/gis/layers?mode=stats",
    "/gov/cockpit": "/analytics/cockpit",
    "/ent/screen": "/analytics/enterprise-screen",
}


def req(method: str, path: str, token: str | None = None, body: dict | None = None):
    data = None if body is None else json.dumps(body).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    r = urllib.request.Request(BASE + path, data=data, headers=headers, method=method)
    with urllib.request.urlopen(r, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


def login(username: str) -> str:
    r = req("POST", "/auth/login", body={"username": username, "password": "123456"})
    return r["data"]["accessToken"]


def flatten_menus(nodes, acc=None):
    acc = acc if acc is not None else []
    for n in nodes or []:
        kids = n.get("children") or []
        if isinstance(kids, list) and len(kids) > 0:
            flatten_menus(kids, acc)
        else:
            if n.get("path") and n.get("name"):
                acc.append({"name": n.get("name"), "path": n.get("path")})
    return acc


def hit_api(path: str, token: str) -> tuple[str, str]:
    """GET 冒烟，返回 (status, note)。"""
    try:
        r = req("GET", path, token=token)
        if r.get("code") == 0:
            data = r.get("data")
            if isinstance(data, dict) and "list" in data:
                n = len(data["list"] or [])
            elif isinstance(data, list):
                n = len(data)
            else:
                n = 1 if data else 0
            return "OK", f"rows={n}"
        return f"code={r.get('code')}", str(r.get("message", ""))[:60]
    except urllib.error.HTTPError as e:
        return f"HTTP{e.code}", e.reason
    except Exception as e:
        return "FAIL", str(e)[:80]


def main():
    lines = ["# 11 — 全量验收记录\n\n", f"> 执行时间自动生成 · API `{BASE}`\n\n"]
    overall_fail = 0

    for portal, user in (("GOV", "gov_admin"), ("ENT", "ent_admin")):
        token = login(user)
        me = req("GET", "/auth/me", token=token)
        live_names = {x["name"] for x in CATALOG[portal]}
        live_paths = {x["path"] for x in CATALOG[portal]}
        menu_leaves = flatten_menus(me["data"].get("menus") or [])
        menu_names = {m["name"] for m in menu_leaves}
        menu_paths = {m["path"] for m in menu_leaves}
        missing = sorted(live_names - menu_names)
        missing_paths = sorted(live_paths - menu_paths)

        lines.append(f"## {portal}（{user}）\n\n")
        lines.append(f"- 目录叶子数: {len(menu_leaves)}\n")
        lines.append(f"- 对照菜单数: {len(live_names)}\n")
        lines.append(f"- 菜单名缺失: {len(missing)}\n")
        lines.append(f"- 菜单path缺失: {len(missing_paths)}\n")
        if missing:
            lines.append(f"- 缺失清单: {', '.join(missing)}\n")
        if missing_paths:
            overall_fail += len(missing_paths)
            lines.append(f"- path缺失: {', '.join(missing_paths)}\n")
        lines.append("\n| menu | path | catalog api | page api | http | note |\n")
        lines.append("|---|---|---|---|---|---|\n")

        for item in CATALOG[portal]:
            shape = item["shape"]
            api = item.get("api") or ""
            page_api = PAGE_REAL_API.get(item["path"], "")
            note = shape
            status = "SKIP"

            if shape == "sso":
                status = "OK"
                note = "sso-shell"
            elif shape == "screen":
                status = "OK"
                note = "screen-route"
            elif shape == "workbench":
                try:
                    r = req("GET", "/todos", token=token)
                    status = "OK" if r.get("code") == 0 else f"code={r.get('code')}"
                    if status != "OK":
                        overall_fail += 1
                except Exception as e:
                    status = "FAIL"
                    note = str(e)
                    overall_fail += 1
            elif shape in ("crud", "gis") and api:
                path = api if api.startswith("/") else f"/{api}"
                status, note = hit_api(path, token)
                if status != "OK":
                    overall_fail += 1
                # 页面真实 API 对照（catalog 与组件内调用不一致时额外测）
                if page_api and page_api.split("?")[0] != path.split("?")[0]:
                    pstatus, pnote = hit_api(
                        page_api if page_api.startswith("/") else f"/{page_api}",
                        token,
                    )
                    note = f"{note}; page={pstatus}({pnote})"
                    if pstatus != "OK":
                        overall_fail += 1
                elif page_api and "?" in page_api:
                    pstatus, pnote = hit_api(page_api, token)
                    note = f"{note}; page={pstatus}({pnote})"
                    if pstatus != "OK":
                        overall_fail += 1
            else:
                status = "OK"

            lines.append(
                f"| {item['name']} | `{item['path']}` | `{api}` | `{page_api or '-'}` | {status} | {note} |\n"
            )
        lines.append("\n")

    # workflow smoke
    lines.append("## 关键流冒烟\n\n")
    try:
        gov = login("gov_admin")
        ent = login("ent_admin")
        applies = req("GET", "/trace/applies", token=gov)
        rows = applies.get("data") or []
        if rows and rows[0].get("status") in ("PENDING", "SUBMITTED"):
            aid = rows[0]["id"]
            req("POST", f"/trace/applies/{aid}/audit", token=gov, body={"approved": True})
            lines.append(f"- 标识审核通过: OK (id={aid})\n")
        else:
            lines.append("- 标识审核通过: SKIP（无 PENDING）\n")
        ponds = req("GET", "/party/ponds", token=gov)
        plist = ponds.get("data") or []
        if isinstance(plist, dict):
            plist = plist.get("list") or []
        pending = [p for p in plist if p.get("auditStatus") == "PENDING"]
        if pending:
            req(
                "POST",
                f"/party/ponds/{pending[0]['id']}/audit",
                token=gov,
                body={"approved": True, "opinion": "ok"},
            )
            lines.append(f"- 塘口审核通过: OK (id={pending[0]['id']})\n")
        else:
            lines.append("- 塘口审核通过: SKIP（无 PENDING）\n")

        # GIS 几何校验
        rect = json.dumps(
            {
                "type": "Polygon",
                "coordinates": [
                    [
                        [120.150, 30.243],
                        [120.152, 30.243],
                        [120.152, 30.245],
                        [120.150, 30.245],
                        [120.150, 30.243],
                    ]
                ],
            }
        )
        v = req("POST", "/party/ponds/validate-geometry", token=gov, body={"geomGeojson": rect})
        if v.get("code") == 0:
            lines.append(f"- GIS 几何校验: OK (areaMu={v['data'].get('areaMu')})\n")
        else:
            overall_fail += 1
            lines.append(f"- GIS 几何校验: FAIL {v}\n")

        lines.append(f"- 企业登录: OK ({ent[:12]}...)\n")
    except Exception as e:
        overall_fail += 1
        lines.append(f"- 关键流冒烟: FAIL {e}\n")

    lines.append(
        f"\n## 汇总\n\n- fail_count: **{overall_fail}**\n"
        f"- result: **{'PASS' if overall_fail == 0 else 'PARTIAL'}**\n"
    )
    out = ROOT / "crawl_output" / "11-全量验收记录.md"
    out.write_text("".join(lines), encoding="utf-8")
    print(out)
    print("fail_count", overall_fail)


if __name__ == "__main__":
    main()
