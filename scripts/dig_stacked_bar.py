from pathlib import Path
import re, json

js = Path("crawl_output/tech/home_probe/index.a973d79c.js").read_text(encoding="utf-8", errors="ignore")
# locate StackedBarChart module by unique attr
needle = 'rightYAxisName'
# find setOption-like construction
for m in re.finditer(r"yAxis:\[\{[^]]{0,400}\]", js):
    s = m.group(0)
    if "亩" in s or "ton" in s or "value" in s:
        print("YAXIS", s[:300])
        print("---")

# FanDiagram related
i = js.find("FanDiagramChart")
print("Fan ctx", js[i : i + 300] if i > 0 else None)

# sample yzpz buttons again
i = js.find('yzpzButtons:[{label:"吨"')
print("buttons", js[i : i + 120] if i > 0 else None)

# colorMap
i = js.find("colorMap:[{start:")
print("colors", js[i : i + 350] if i > 0 else None)

# get species area API response shape
i = js.find("yzpzStatistics=")
print("assign", js[i : i + 500] if i > 0 else None)
i = js.find("seriesTitle")
print("seriesTitle contexts:")
for m in re.finditer("seriesTitle", js):
    print(js[m.start() - 80 : m.start() + 160])
    print("---")
    break
