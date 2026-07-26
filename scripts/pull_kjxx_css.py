import httpx, re
from pathlib import Path

base = "http://60.165.239.173:9000/universalLargescreen"
out = Path("crawl_output/tech/home_probe")
out.mkdir(parents=True, exist_ok=True)
c = httpx.Client(timeout=60, trust_env=False)
html = c.get(base + "/").text
css = sorted(set(re.findall(r"css/[^\"']+\.css", html)))
print("css_count", len(css))
keys = [
    "kjxx",
    "contentTop",
    "page-left",
    "pageHeader",
    "con-top",
    "sblx-grid",
    "progress-ball",
    "scpcl",
    "qyyzmj",
    "menuItem",
    "fullScreenBtn",
    "yzms-progress",
]
hits = {}
for rel in css + ["css/index.1565166d.css", "css/chunk-vendors.d15c396e.css"]:
    try:
        t = c.get(f"{base}/{rel}").text
        path = out / Path(rel).name
        path.write_text(t, encoding="utf-8")
        found = [k for k in keys if k in t]
        if found:
            hits[rel] = found
            print(rel, len(t), found)
    except Exception as e:
        print("fail", rel, e)

# extract relevant rule blocks from hit files
snippets = {}
for rel, found in hits.items():
    text = (out / Path(rel).name).read_text(encoding="utf-8", errors="ignore")
    for k in found:
        for m in re.finditer(re.escape(k) + r"[^{]{0,80}\{[^}]{0,800}\}", text):
            snippets.setdefault(k, []).append(m.group(0)[:500])

Path("crawl_output/tech/home_probe/css_snippets.json").write_text(
    __import__("json").dumps(snippets, ensure_ascii=False, indent=2), encoding="utf-8"
)
print("snippet_keys", list(snippets.keys()))
