# -*- coding: utf-8 -*-
import json
import urllib.request

BASE = "http://127.0.0.1:8000/api/v1"


def req(method, path, token=None, body=None):
    data = None if body is None else json.dumps(body).encode()
    h = {"Content-Type": "application/json"}
    if token:
        h["Authorization"] = f"Bearer {token}"
    r = urllib.request.Request(BASE + path, data=data, headers=h, method=method)
    with urllib.request.urlopen(r, timeout=15) as resp:
        return json.loads(resp.read().decode())


def walk(ns, leaves):
    for n in ns or []:
        if n.get("children"):
            walk(n["children"], leaves)
        elif n.get("name"):
            leaves.append(n["name"])


def main():
    from app.db import SessionLocal
    from app.seed_upgrade import upgrade_seed

    db = SessionLocal()
    upgrade_seed(db)
    db.close()

    gov = req("POST", "/auth/login", body={"username": "gov_admin", "password": "123456"})["data"]["accessToken"]
    ent = req("POST", "/auth/login", body={"username": "ent_admin", "password": "123456"})["data"]["accessToken"]
    print("gov cams", [(c["name"], c["enterpriseName"]) for c in req("GET", "/iot/cameras", token=gov)["data"]])
    print("ent cams", [(c["name"], c["enterpriseName"]) for c in req("GET", "/iot/cameras", token=ent)["data"]])
    pool = req("GET", "/iot/cameras?unassigned=true", token=gov)["data"]
    print("pool", [(c["id"], c["name"]) for c in pool])
    if pool:
        r = req("POST", f"/iot/cameras/{pool[0]['id']}/assign", token=gov, body={"enterpriseId": 1})
        print("assign ->", r["data"]["enterpriseName"])
        # reclaim for demo leftover? keep assigned
    cfg = req("GET", "/iot/ezviz/config", token=gov)["data"]
    print("gov cfg", cfg["status"], "canEdit", cfg["canEdit"])
    print("ent canEdit", req("GET", "/iot/ezviz/config", token=ent)["data"]["canEdit"])
    leaves = []
    walk(req("GET", "/auth/me", token=gov)["data"]["menus"], leaves)
    print("gov has 萤石云配置", "萤石云配置" in leaves)
    leaves = []
    walk(req("GET", "/auth/me", token=ent)["data"]["menus"], leaves)
    print("ent has 萤石云配置", "萤石云配置" in leaves)


if __name__ == "__main__":
    main()
