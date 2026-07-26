from pathlib import Path
import re

js = Path("crawl_output/tech/home_probe/index.a973d79c.js").read_text(encoding="utf-8", errors="ignore")

for key in ["sblxListv2:", "this.sblxListv2", "水质监测", "增氧机", "尾水设备", "摄像头"]:
    idxs = [m.start() for m in re.finditer(re.escape(key), js)]
    print(key, idxs[:5])
    if idxs:
        i = idxs[0]
        print(js[max(0, i - 80) : i + 600])
        print("---")

for mid in ["e217", "cede", "a993", "f823"]:
    m = re.search('"%s":function' % mid, js)
    if not m:
        print(mid, "NO")
        continue
    print(mid, js[m.start() : m.start() + 180])
