from pathlib import Path
import re, json

css = Path("crawl_output/tech/home_probe/index.1565166d.css").read_text(encoding="utf-8", errors="ignore")
for p in Path("crawl_output/tech/home_probe").glob("chunk-*.css"):
    css += "\n" + p.read_text(encoding="utf-8", errors="ignore")

# pull larger context around unique class clusters
needles = [
    ".mapPage .contentTop",
    ".kjxxPage-left",
    ".kjxxPage-right",
    ".pageHeader",
    ".pageMenu",
    ".menuItem",
    ".fullScreenBtn",
    ".sblx-card-v2",
    ".yzms-progress-group",
    ".progress-item",
    ".scpcl-content",
    ".scpcl-legend",
    ".group-button-wrap",
    ".rightBox",
    "TitleRow",
]


def around(s: str, n: int = 1800):
    i = css.find(s)
    if i < 0:
        return None
    return css[i : i + n]


out = {s: around(s) for s in needles}
out = {k: v for k, v in out.items() if v}
Path("crawl_output/tech/home_probe/css_context.json").write_text(
    json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8"
)
for k, v in out.items():
    print("====", k)
    print(v[:500])
    print()
