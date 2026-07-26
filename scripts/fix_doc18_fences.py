"""Repair broken Markdown code fences in 18-前端技术栈分析.md"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "crawl_output" / "18-前端技术栈分析.md"


def main() -> None:
    text = TARGET.read_text(encoding="utf-8")
    text = re.sub(r"^`\s*v?ue\s*$", "```vue", text, flags=re.MULTILINE)
    text = re.sub(r"^`\s*javascript\s*$", "```javascript", text, flags=re.MULTILINE)

    lines = text.splitlines()
    out: list[str] = []
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped in ("`", "``"):
            nxt = lines[i + 1].strip() if i + 1 < len(lines) else ""
            if nxt.startswith("#") or nxt.startswith("**") or nxt.startswith("|") or nxt == "" or nxt.startswith("```"):
                continue
        if stripped == "`" and out:
            prev = out[-1].strip()
            if prev and not prev.startswith("```"):
                if (
                    prev.endswith(("}", ")", ";", ">", "`"))
                    or prev.startswith(("import", "const", "export", "<", "//", "/*"))
                ):
                    out.append("```")
                    continue
        out.append(line)

    fixed = "\n".join(out) + ("\n" if text.endswith("\n") else "")
    TARGET.write_text(fixed, encoding="utf-8")
    print("vue blocks:", len(re.findall(r"^```vue", fixed, re.MULTILINE)))
    print("js blocks:", len(re.findall(r"^```javascript", fixed, re.MULTILINE)))
    print("orphan `:", len(re.findall(r"^`$", fixed, re.MULTILINE)))


if __name__ == "__main__":
    main()
