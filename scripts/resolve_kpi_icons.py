from pathlib import Path
import re

js = Path("crawl_output/tech/home_probe/index.a973d79c.js").read_text(encoding="utf-8", errors="ignore")
for mid in ["e217", "cede", "a993", "f823"]:
    m = re.search(rf'"{mid}":function\(e,t,a\)\{{e\.exports=a\.p\+"([^"]+)"', js)
    print(mid, m.group(1) if m else "NOT FOUND")

i = js.find("sblxListv2")
print("sblxListv2", i)
print(js[i : i + 1200] if i >= 0 else "")

# resolve common icon module ids near sblx
for mid in re.findall(r'icon:a\("([0-9a-f]+)"\)', js[i : i + 2000] if i >= 0 else ""):
    m = re.search(rf'"{mid}":function\(e,t,a\)\{{e\.exports=a\.p\+"([^"]+)"', js)
    print("icon", mid, "->", m.group(1) if m else "?")
