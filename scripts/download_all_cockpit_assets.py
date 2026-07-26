"""Download ALL visual assets referenced by universalLargescreen CSS/JS for cockpit."""
from __future__ import annotations

import json
import re
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
BASE = "http://60.165.239.173:9000/universalLargescreen"
OUT = ROOT / "frontend/apps/admin/public/cockpit"
OUT.mkdir(parents=True, exist_ok=True)
PROBE = ROOT / "crawl_output/tech/home_probe"

css_files = list(PROBE.glob("*.css"))
js_files = [PROBE / "index.a973d79c.js"]
text = ""
for f in css_files + [j for j in js_files if j.exists()]:
    text += "\n" + f.read_text(encoding="utf-8", errors="ignore")

# urls like img/xxx.png or ../img/xxx.jpg or fonts/xxx.ttf
rels = set()
for m in re.finditer(r"(?:(?:\.\./)?(?:img|fonts)/)[^)\"'\\?\s]+\.(?:png|jpe?g|gif|webp|svg|ttf|otf|woff2?)", text, re.I):
    rel = m.group(0).lstrip("./")
    if rel.startswith("../"):
        rel = rel[3:]
    rels.add(rel)

# force critical wrap + common
forced = [
    "img/bg_wrap.9eb85a01.jpg",
    "img/bg_header.3f43da79.png",
    "img/bg_bottom.fd759d3b.png",
    "img/bg_left.4af176d4.png",
    "img/bg_right.528b0034.png",
    "img/bg_title_left.3b5b0477.png",
    "img/bg_title_right.8b2703f3.png",
    "img/bottom_tab.ef307880.png",
    "img/bottom_tab_active.d44e4f9d.png",
    "img/menu_active.70f50b01.png",
    "img/title.f839fcb5.png",
    "img/di1_pic.3cda33d2.png",
    "img/di2_pic@2x.7d7c8ad4.png",
]
for f in forced:
    rels.add(f)

print("candidates", len(rels))
client = httpx.Client(timeout=60, trust_env=False)
saved = []
failed = []
for rel in sorted(rels):
    # only cockpit-relevant prefixes to avoid downloading entire app (still many)
    name = Path(rel).name
    # skip huge duplicates already with ascii aliases for fonts if chinese
    url = f"{BASE}/{rel}"
    try:
        r = client.get(url)
        if r.status_code != 200 or len(r.content) < 200:
            failed.append({"rel": rel, "status": r.status_code, "len": len(r.content)})
            continue
        path = OUT / name
        # avoid clobbering large fonts with tiny iconfont wrongly named - keep unique
        if path.exists() and path.stat().st_size > len(r.content) and path.suffix in {".ttf", ".otf"}:
            # keep larger existing
            continue
        path.write_bytes(r.content)
        saved.append({"name": name, "rel": rel, "bytes": len(r.content)})
        print("ok", name, len(r.content))
    except Exception as e:
        failed.append({"rel": rel, "error": str(e)})
        print("fail", rel, e)

manifest = {"saved": saved, "failed": failed, "count_saved": len(saved), "count_failed": len(failed)}
(PROBE / "cockpit_assets_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
print("DONE saved", len(saved), "failed", len(failed))
