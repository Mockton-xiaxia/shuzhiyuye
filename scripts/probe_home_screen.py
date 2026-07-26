"""Download universalLargescreen assets and extract #/home related strings."""
from __future__ import annotations

import json
import re
from pathlib import Path

import httpx

BASE = "http://60.165.239.173:9000/universalLargescreen"
OUT = Path(__file__).resolve().parents[1] / "crawl_output" / "tech" / "home_probe"
OUT.mkdir(parents=True, exist_ok=True)

KEYWORDS = [
    "渔业总体情况",
    "养殖品种面积排行",
    "种苗数量",
    "水产品产量",
    "渔业综合产值",
    "设备类型分析",
    "养殖模式",
    "数字孪生",
    "生产记录",
    "养殖主体",
    "物联设备",
    "视频监控",
    "汉山街道",
    "梁山镇",
    "水库养殖",
    "陆基圆池",
    "退出全屏",
    "path:\"/home\"",
    "path:'/home'",
    "#/home",
    "name:\"home\"",
]


def main() -> None:
    client = httpx.Client(timeout=60.0, trust_env=False)
    html = client.get(f"{BASE}/").text
    (OUT / "index.html").write_text(html, encoding="utf-8")
    js_files = sorted(set(re.findall(r'js/[^"\']+\.js', html)))
    print("js_files", len(js_files))
    (OUT / "js_list.json").write_text(json.dumps(js_files, ensure_ascii=False, indent=2), encoding="utf-8")

    hits: dict[str, list[dict]] = {}
    # Prefer known hashed files from prior crawl, plus whatever index references
    candidates = list(dict.fromkeys(js_files + [
        "js/index.a973d79c.js",
        "js/chunk-vendors.9f7e0a0a.js",
    ]))
    for rel in candidates:
        url = f"{BASE}/{rel}"
        try:
            r = client.get(url)
            if r.status_code != 200:
                print("skip", rel, r.status_code)
                continue
            text = r.text
            path = OUT / Path(rel).name
            path.write_text(text, encoding="utf-8")
            print("saved", rel, "bytes", len(text))
            for kw in KEYWORDS:
                idx = text.find(kw)
                if idx < 0:
                    continue
                start = max(0, idx - 180)
                end = min(len(text), idx + 220)
                hits.setdefault(kw, []).append({
                    "file": rel,
                    "snippet": text[start:end],
                })
        except Exception as e:  # noqa: BLE001
            print("fail", rel, e)

    # Also scan previously downloaded chunk list if present
    old = Path(__file__).resolve().parents[1] / "crawl_output" / "tech" / "largescreen.json"
    if old.exists():
        data = json.loads(old.read_text(encoding="utf-8"))
        for url in data.get("js", []) or data.get("scripts", []) or []:
            if not isinstance(url, str) or "/js/" not in url:
                continue
            rel = url.split("/universalLargescreen/")[-1]
            if (OUT / Path(rel).name).exists():
                continue
            # only pull likely route chunks by probing a few home-related names later
            pass

    (OUT / "keyword_hits.json").write_text(json.dumps(hits, ensure_ascii=False, indent=2), encoding="utf-8")
    print("keywords_hit", list(hits.keys()))


if __name__ == "__main__":
    main()
