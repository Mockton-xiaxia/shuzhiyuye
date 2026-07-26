"""Extract map click / drill-down / popup / getGisData behavior from live index.js."""
from __future__ import annotations

import json
import re
from pathlib import Path

js = Path("crawl_output/tech/home_probe/index.a973d79c.js").read_text(encoding="utf-8", errors="ignore")
out = {}

needles = [
    "clearHighlightMarker",
    "highlightMarker",
    "townshipData",
    "getGisData",
    "subjectNum",
    "fishPondAcreageCount",
    "activeAreaName",
    "setZoom",
    "fit",
    "popup",
    "areaName",
    "click",
    "下钻",
    "drill",
    "ol-popup",
    "SZXY_areaMapJson",
    "getMapJson",
]
for n in needles:
    idxs = [m.start() for m in re.finditer(re.escape(n), js)]
    out[n] = {"count": len(idxs), "snips": [js[max(0, i - 120) : i + 380] for i in idxs[:3]]}

# larger block around ensureProjectBoundary / pageInit already known
for key in ["pageInit:function", "getGisData:function", "clearHighlightMarker:function"]:
    i = js.find(key)
    out[key] = js[i : i + 1500] if i >= 0 else None

Path("crawl_output/tech/home_probe/map_drill_extract.json").write_text(
    json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8"
)
print("wrote map_drill_extract.json")
for k in ["getGisData", "clearHighlightMarker", "activeAreaName", "townshipData", "ol-popup"]:
    print(k, out[k]["count"] if isinstance(out.get(k), dict) else "n/a")
