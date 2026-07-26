"""Extract StackedBarChart / TitleRow / layout CSS details for visual rebuild."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JS = (ROOT / "crawl_output/tech/home_probe/index.a973d79c.js").read_text(encoding="utf-8", errors="ignore")
CSS = (ROOT / "crawl_output/tech/home_probe/index.1565166d.css").read_text(encoding="utf-8", errors="ignore")
OUT = ROOT / "crawl_output/tech/home_probe/visual_extract.json"

# pull TitleRow component render + styles
chunks = {}
for key in [
    "chartTitle",
    "TitleRow",
    "StackedBarChart",
    "showTotalLabel",
    "lineData",
    "rightYAxisName",
    "FanDiagramChart",
    "DotRingChart",
    "WaveBall",
    "layout_wrapper",
    "page-left",
    "kjxxPage-left",
    "border-image",
    "bg_title",
]:
    idxs = [m.start() for m in re.finditer(re.escape(key), JS if key[0].isupper() or key in JS else CSS)]
    src = JS if JS.count(key) >= CSS.count(key) else CSS
    idxs = [m.start() for m in re.finditer(re.escape(key), src)]
    chunks[key] = [src[max(0, i - 100) : i + 500] for i in idxs[:2]]

# specific: stacked bar option builder
m = re.search(r"StackedBarChart.{0,200}", JS)
# find series construction near yzpzStatistics
m2 = re.search(r"yzpzStatistics.{0,800}", JS)
chunks["yzpzStatistics_data"] = m2.group(0) if m2 else None

# layout rem sizes
for pat in [
    r"\.layout_wrapper[^}]{0,400}\}",
    r"\.page-left[^}]{0,500}\}",
    r"\.kjxxPage-left[^}]{0,800}\}",
    r"\.kjxxPage-right[^}]{0,800}\}",
    r"\.pageHeader[^}]{0,500}\}",
]:
    mm = re.search(pat, CSS)
    if mm:
        chunks[pat] = mm.group(0)

# TitleRow template from js
m = re.search(r'staticClass:"title-row"[^;]{0,600}', JS)
if not m:
    m = re.search(r'TitleRow.*?staticClass:"[^"]+"[^;]{0,400}', JS)
chunks["title_row_tpl"] = m.group(0) if m else None

# find getGisData / township markers
m = re.search(r"townshipData.{0,400}", JS)
chunks["townshipData"] = m.group(0) if m else None

OUT.write_text(json.dumps(chunks, ensure_ascii=False, indent=2), encoding="utf-8")
print("wrote", OUT)
print("keys", list(chunks.keys())[:20])
for k in ["yzpzStatistics_data", "title_row_tpl", "townshipData"]:
    print("\n##", k)
    print((chunks.get(k) or "")[:400])
