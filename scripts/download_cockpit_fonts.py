from pathlib import Path
import re, httpx

css = Path("crawl_output/tech/home_probe/index.1565166d.css").read_text(encoding="utf-8", errors="ignore")
fonts = sorted(set(re.findall(r"url\(([^)]+\.(?:woff2?|ttf|otf))\)", css)))
print("css_fonts", fonts[:30])
out = Path("frontend/apps/admin/public/cockpit")
base = "http://60.165.239.173:9000/universalLargescreen"
c = httpx.Client(timeout=60, trust_env=False)
for f in fonts:
    f = f.strip("\"'")
    if f.startswith("data:"):
        continue
    if f.startswith("../"):
        rel = f.replace("../", "")
    elif f.startswith("/"):
        rel = f.lstrip("/")
    else:
        rel = f
    name = Path(rel).name
    try:
        r = c.get(f"{base}/{rel}" if not rel.startswith("http") else rel)
        if r.status_code == 200 and len(r.content) > 1000:
            (out / name).write_bytes(r.content)
            print("font", name, len(r.content))
    except Exception as e:
        print("fail", rel, e)

print("assets", [p.name for p in out.iterdir()])
