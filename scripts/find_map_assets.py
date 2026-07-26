from pathlib import Path
import re, json

t = Path("crawl_output/tech/home_probe/index.a973d79c.js").read_text(encoding="utf-8", errors="ignore")
urls = sorted(set(re.findall(r"https?://[^\"'\\]+?\.(?:json|geojson)", t)))
rels = sorted(set(re.findall(r"[\"'](/[^\"']*(?:map|boundary|area|geo|json)[^\"']*\.json)[\"']", t, re.I)))
print("http", len(urls))
for u in urls[:40]:
    print(u)
print("rel", len(rels))
for u in rels[:40]:
    print(u)

# also search img assets used by header
imgs = sorted(set(re.findall(r"img/[^\"']+\.png", t)))
print("imgs", len(imgs))
for u in imgs:
    if any(k in u.lower() for k in ["header", "title", "di", "bg", "menu", "btn", "top"]):
        print(u)
