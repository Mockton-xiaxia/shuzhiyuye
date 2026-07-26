"""Extract key CSS rules for kjxx home screen from live index.css."""
from pathlib import Path
import re, json

css = Path("crawl_output/tech/home_probe/index.1565166d.css").read_text(encoding="utf-8", errors="ignore")
# also kjxx chunk
for extra in ["chunk-770d262a.2603c6f5.css", "chunk-7712d6ae.2732bca3.css", "chunk-74ad3b81.dabe9105.css"]:
    p = Path("crawl_output/tech/home_probe") / extra
    if p.exists():
        css += "\n" + p.read_text(encoding="utf-8", errors="ignore")

selectors = [
    "pageHeader",
    "header-wrap",
    "btn-setting",
    "contentTop",
    "con-top-item",
    "con-top-num",
    "page-left",
    "page-right",
    "kjxxPage",
    "TitleRow",
    "title-row",
    "qyyzmj",
    "sblx-grid",
    "sblx-card",
    "yzms-progress",
    "progress-item",
    "progress-ball",
    "scpcl",
    "menuItem",
    "fullScreenBtn",
    "pageMenu",
    "isMenu",
    "group-button",
]


def extract_blocks(name: str, limit: int = 8):
    # naive: find .name or [class*=name] nearby braces - CSS may be minified
    out = []
    for m in re.finditer(re.escape(name), css):
        start = m.start()
        # walk back to previous } or start
        left = css.rfind("}", 0, start)
        left = left + 1 if left >= 0 else max(0, start - 40)
        # walk forward to matching closing for first {
        brace = css.find("{", start)
        if brace < 0 or brace - start > 120:
            continue
        depth = 0
        i = brace
        while i < len(css) and i < brace + 2500:
            if css[i] == "{":
                depth += 1
            elif css[i] == "}":
                depth -= 1
                if depth == 0:
                    block = css[left : i + 1].strip()
                    if len(block) > 20:
                        out.append(block[:1200])
                    break
            i += 1
        if len(out) >= limit:
            break
    return out


result = {s: extract_blocks(s) for s in selectors}
# keep non-empty
result = {k: v for k, v in result.items() if v}
Path("crawl_output/tech/home_probe/css_rules.json").write_text(
    json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
)
print("keys", list(result.keys()))
for k, v in result.items():
    print("\n====", k, "n=", len(v))
    print(v[0][:400])
