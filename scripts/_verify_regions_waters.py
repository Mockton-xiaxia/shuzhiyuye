"""一次性验证：区划导入、地名清洗、排放水域编辑。"""
from __future__ import annotations

import json
import urllib.request

from sqlalchemy import create_engine, text

from app.config import get_settings

engine = create_engine(get_settings().database_url)
with engine.connect() as c:
    n = c.execute(text("select count(*) from sys_region where deleted=0")).scalar()
    print("regions", n)
    bad = c.execute(
        text("select count(*) from tr_mark_apply where remark like '%南郑%' and deleted=0")
    ).scalar()
    print("trace_nanzheng", bad)
    rows = c.execute(text("select name from ef_water_body where deleted=0 limit 3")).fetchall()
    print("waters_db", rows)

body = json.dumps({"username": "gov_admin", "password": "123456"}).encode()
req = urllib.request.Request(
    "http://127.0.0.1:8000/api/v1/auth/login",
    data=body,
    headers={"Content-Type": "application/json"},
    method="POST",
)
token = json.loads(urllib.request.urlopen(req, timeout=10).read())["data"]["accessToken"]
headers = {"Authorization": f"Bearer {token}"}

tree = json.loads(
    urllib.request.urlopen(
        urllib.request.Request("http://127.0.0.1:8000/api/v1/party/regions/tree", headers=headers),
        timeout=15,
    ).read()
)["data"]
print("provinces", len(tree), "first", tree[0]["label"])

waters = json.loads(
    urllib.request.urlopen(
        urllib.request.Request("http://127.0.0.1:8000/api/v1/effluent/waters", headers=headers),
        timeout=10,
    ).read()
)["data"]
if not waters:
    print("no waters")
    raise SystemExit(0)
wid = waters[0]["id"]
print("before", waters[0])
upd = json.dumps({"zone": "测试水域-已保存", "level": "II"}).encode()
urllib.request.urlopen(
    urllib.request.Request(
        f"http://127.0.0.1:8000/api/v1/effluent/waters/{wid}",
        data=upd,
        headers={**headers, "Content-Type": "application/json"},
        method="PUT",
    ),
    timeout=10,
)
waters2 = json.loads(
    urllib.request.urlopen(
        urllib.request.Request("http://127.0.0.1:8000/api/v1/effluent/waters", headers=headers),
        timeout=10,
    ).read()
)["data"]
row = next(w for w in waters2 if w["id"] == wid)
print("after", row)
assert row["zone"] == "测试水域-已保存", row
print("OK")
