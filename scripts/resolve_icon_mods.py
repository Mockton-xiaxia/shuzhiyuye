from pathlib import Path
import re

js = Path("crawl_output/tech/home_probe/index.a973d79c.js").read_text(encoding="utf-8", errors="ignore")
for mid in ["6a6b", "633f", "1ef4", "5ac7", "e217", "cede", "a993", "f823"]:
    m = re.search('"%s":function' % mid, js)
    if not m:
        print(mid, "NO def")
        continue
    chunk = js[m.start() : m.start() + 250]
    print(mid, chunk)
    fm = re.search(r'img/[^"\\]+', chunk)
    print("  ->", fm.group(0) if fm else "?")
