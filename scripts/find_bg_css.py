from pathlib import Path
import re

css = Path("crawl_output/tech/home_probe/index.1565166d.css").read_text(encoding="utf-8", errors="ignore")
for pat in [
    r"\.layout_wrapper\{[^}]+\}",
    r"\.mapPage\{[^}]+\}",
    r"#app\{[^}]+\}",
    r"body,html\{[^}]+\}",
    r"\.page-left\{[^}]+\}",
    r"\.page-right\{[^}]+\}",
]:
    m = re.search(pat, css)
    print(pat, "=>", (m.group(0)[:250] if m else "NONE"))
    print("---")

# find map container absolute full
for key in ["position:absolute", "z-index:0", "map-id", "contentTop"]:
    print(key, css.count(key))

imgs = sorted(set(re.findall(r"img/[^)\"']+\.png", css)))
for u in imgs:
    low = u.lower()
    if any(k in low for k in ["bg", "map", "body", "layout", "screen", "grid", "di"]):
        print("IMG", u)
