"""Download Nanzheng district GeoJSON for cockpit map."""
from pathlib import Path
import httpx
import json

out = Path("frontend/apps/admin/public/cockpit")
out.mkdir(parents=True, exist_ok=True)
urls = {
    "nanzheng.json": "https://geo.datav.aliyun.com/areas_v3/bound/610703.json",
    "nanzheng_full.json": "https://geo.datav.aliyun.com/areas_v3/bound/610703_full.json",
}
c = httpx.Client(timeout=60, trust_env=False)
for name, url in urls.items():
    try:
        r = c.get(url)
        print(name, r.status_code, len(r.content))
        if r.status_code == 200:
            data = r.json()
            (out / name).write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
            feats = data.get("features") or []
            print("  features", len(feats))
            for f in feats[:5]:
                print("   ", (f.get("properties") or {}).get("name"))
    except Exception as e:
        print("fail", name, e)
