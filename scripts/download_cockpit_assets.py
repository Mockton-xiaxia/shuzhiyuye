"""Download key visual assets from universalLargescreen."""
from pathlib import Path
import httpx
import re

base = "http://60.165.239.173:9000/universalLargescreen"
out = Path("frontend/apps/admin/public/cockpit")
out.mkdir(parents=True, exist_ok=True)

# discover header/bottom imgs from css
css = Path("crawl_output/tech/home_probe/index.1565166d.css").read_text(encoding="utf-8", errors="ignore")
imgs = sorted(set(re.findall(r"img/[^)\"']+\.png", css)))
wanted = [u for u in imgs if any(k in u for k in ["header", "bottom", "title", "di", "menu", "bg_"])]
# also known from js
wanted += [
    "img/bg_header.3f43da79.png",
    "img/bg_bottom.fd759d3b.png",
    "img/bg_title_left.3b5b0477.png",
    "img/bg_title_right.8b2703f3.png",
    "img/title.f839fcb5.png",
]
wanted = sorted(set(wanted))
print("wanted", len(wanted))
c = httpx.Client(timeout=60, trust_env=False)
saved = []
for rel in wanted:
    name = Path(rel).name
    try:
        r = c.get(f"{base}/{rel}")
        if r.status_code != 200:
            print("skip", rel, r.status_code)
            continue
        (out / name).write_bytes(r.content)
        saved.append(name)
        print("ok", name, len(r.content))
    except Exception as e:
        print("fail", rel, e)

# also try common header name variants via html/js references
js = Path("crawl_output/tech/home_probe/index.a973d79c.js").read_text(encoding="utf-8", errors="ignore")
for rel in sorted(set(re.findall(r"img/(?:bg_header|bg_bottom|bg_title[^\"']*|di\d[^\"']*|contentTop[^\"']*)[^\"']*\.png", js))):
    name = Path(rel).name
    if (out / name).exists():
        continue
    try:
        r = c.get(f"{base}/{rel}")
        if r.status_code == 200:
            (out / name).write_bytes(r.content)
            saved.append(name)
            print("jsok", name, len(r.content))
    except Exception as e:
        print("jsfail", rel, e)

Path("crawl_output/tech/home_probe/assets_saved.json").write_text(
    __import__("json").dumps(saved, ensure_ascii=False, indent=2), encoding="utf-8"
)
print("saved_count", len(saved))
