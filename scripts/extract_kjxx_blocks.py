from pathlib import Path
import re, json

t = Path("crawl_output/tech/home_probe/index.a973d79c.js").read_text(encoding="utf-8", errors="ignore")
out = {}
for key in [
    "yzpzButtons:",
    "scpclButtons:",
    "yzczyTabList:",
    "yzmsModeButtons:",
    "contentTopStyleMap:",
    "breedDotColors:",
    "seedlingData:",
    "yzmsColorMap:",
    "sblxListv2:",
]:
    i = t.find(key)
    out[key] = t[i : i + 700] if i >= 0 else None

# chart component usages near breedDot
i = t.find("breedDotList")
out["breedDot_ctx"] = t[i : i + 900] if i >= 0 else None
i = t.find("DotRingChart")
out["DotRingChart_ctx"] = t[max(0, i - 200) : i + 500] if i >= 0 else None
i = t.find("StackedBarChart")
out["StackedBar_ctx"] = t[max(0, i - 200) : i + 500] if i >= 0 else None
i = t.find("FanDiagramChart")
out["Fan_ctx"] = t[max(0, i - 120) : i + 500] if i >= 0 else None

# footer for kjxx page specifically
for label in ["数字孪生", "生产记录", "首页", "退出全屏"]:
    idxs = [m.start() for m in re.finditer(label, t)]
    out[f"label_{label}"] = [t[max(0, i - 120) : i + 160] for i in idxs[:4]]

# redirect home -> kjxx?
for pat in [r'path:"/home"[^}]{0,200}', r'redirect:"/kjxx"', r'alias:"/home"', r'name:"kjxx"']:
    out[pat] = [m.group(0) for m in re.finditer(pat, t)][:5]

Path("crawl_output/tech/home_probe/kjxx_blocks.json").write_text(
    json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8"
)
print("ok")
for k, v in out.items():
    if k.endswith(":") or k.endswith("_ctx"):
        print("\n##", k)
        print((v or "")[:400])
