"""Deep extract kjxx/home cockpit structure from universalLargescreen index.js."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JS = ROOT / "crawl_output" / "tech" / "home_probe" / "index.a973d79c.js"
OUT = ROOT / "crawl_output" / "tech" / "home_probe" / "kjxx_spec.json"

text = JS.read_text(encoding="utf-8", errors="ignore")

needles = [
    "kjxxPage-left",
    "yzpzStatistics",
    "yzpzButtons",
    "seedlingData",
    "FanDiagramChart",
    "breedDotList",
    "scpclButtons",
    "synthesizeList",
    "yzczyTabList",
    "sblxListv2",
    "yzmsModeButtons",
    "yzmsColorMap",
    "contentTopStyleMap",
    "contentTopItems",
    "subjectNum",
    "pondAcreage",
    "leftMenu",
    "path:\"/kjxx\"",
    "path:\"/home\"",
    "DotChart",
    "BreedDot",
    "Pie3D",
    "环图",
    "统计",
    "累计",
]


def ctx(idx: int, before: int = 250, after: int = 450) -> str:
    return text[max(0, idx - before) : min(len(text), idx + after)]


found: dict[str, list[str]] = {}
for n in needles:
    idxs = [m.start() for m in re.finditer(re.escape(n), text)]
    if not idxs:
        continue
    found[n] = [ctx(i) for i in idxs[:3]]

# Pull larger data() blocks around kjxx markers
blocks = {}
for key in ["yzpzButtons", "scpclButtons", "yzczyTabList", "yzmsModeButtons", "seedlingData", "yzmsColorMap", "contentTopStyleMap", "breedDotColors", "sblxListv2"]:
    m = re.search(re.escape(key) + r".{0,1200}", text)
    if m:
        blocks[key] = m.group(0)

# route table snippets
routes = []
for m in re.finditer(r'path:"/(kjxx|home|yzsc|szls)"[^,]{0,80}', text):
    routes.append(m.group(0))

# component names near left/right panels
comps = sorted(set(re.findall(r"a\(\"([A-Za-z][A-Za-z0-9]+)\"", text[text.find("kjxxPage-left") : text.find("kjxxPage-left") + 8000] if "kjxxPage-left" in text else "")))

OUT.write_text(
    json.dumps(
        {
            "routes": sorted(set(routes))[:40],
            "nearby_components": comps[:80],
            "blocks": blocks,
            "contexts": {k: v[:2] for k, v in found.items()},
        },
        ensure_ascii=False,
        indent=2,
    ),
    encoding="utf-8",
)
print("wrote", OUT)
print("routes", sorted(set(routes))[:20])
print("block_keys", list(blocks.keys()))
print("comp_sample", comps[:30])
