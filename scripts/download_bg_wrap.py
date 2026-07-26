import httpx
from pathlib import Path

base = "http://60.165.239.173:9000/universalLargescreen"
out = Path("frontend/apps/admin/public/cockpit")
out.mkdir(parents=True, exist_ok=True)
c = httpx.Client(timeout=90, trust_env=False)
for rel in [
    "img/bg_wrap.9eb85a01.jpg",
    "img/bg_wrap.9eb85a01.png",
    "img/qxbg.b364e84f.png",
]:
    try:
        r = c.get(f"{base}/{rel}")
        print(rel, r.status_code, len(r.content), r.headers.get("content-type"))
        if r.status_code == 200 and len(r.content) > 1000:
            path = out / Path(rel).name
            path.write_bytes(r.content)
            print("saved", path, path.stat().st_size)
    except Exception as e:
        print("fail", rel, e)

print("files", [p.name for p in out.glob("bg_wrap*")])
print("qxbg", list(out.glob("qxbg*")))
