"""Replace real place/vendor names in demo data with neutral labels."""
from pathlib import Path

REPLACEMENTS = [
    ("汉中市南郑区绿色循环渔业试点项目", "绿色循环渔业试点项目"),
    ("汉中市南郑区渔业总体情况", "区县渔业总体情况"),
    ("汉中市南郑区绿色循环渔业试点", "绿色循环渔业试点"),
    ("南郑区绿色循环渔业", "绿色循环渔业"),
    ("南郑区汉山街道养殖区巡查", "示范县示范镇养殖区巡查"),
    ("南郑区汉山街道余秀芳养殖场周边", "示范县示范镇示范养殖场周边"),
    ("南郑区余秀芳养殖场", "示范县示范养殖场"),
    ("南郑区尾水排放管理办法", "示范县尾水排放管理办法"),
    ("南郑区水产品质量安全监管办法", "示范县水产品质量安全监管办法"),
    ("南郑区水产检测中心", "区县水产检测中心"),
    ("南郑区水产市场", "区县水产市场"),
    ("南郑区全域", "示范县全域"),
    ("南郑渔政执法", "区县渔政执法"),
    ("汉中水产批发市场", "本地水产批发市场"),
    ("汉中水产批发商", "本地水产批发商"),
    ("余秀芳养殖场", "示范养殖场"),
    ("南郑大鲵", "本地大鲵"),
    ("捷安物联", "智联物联"),
    ("汉中饲料厂", "本地饲料厂"),
    ("汉中渔药店", "本地渔药店"),
    ("南郑区县管理员", "区县管理员"),
    ("陕西省汉中市南郑区", "陕西省示范市示范县"),
    ("陕西省,汉中市,南郑区", "陕西省,示范市,示范县"),
    ("南郑区圣水镇王营村", "示范县圣水镇王营村"),
    ("南郑区红庙镇中心村", "示范县红庙镇中心村"),
    ('"regionPathLabel": "陕西省,汉中市,南郑区,汉山街道"', '"regionPathLabel": "陕西省,示范市,示范县,示范镇"'),
    ("南郑区", "示范县"),
    ("汉中市", "示范市"),
    ("汉中批发", "本地批发"),
    ("余秀芳", "张示范"),
    ("南郑城区西侧", "示范城区西侧"),
    ("南郑东南部", "示范县东南部"),
    ("南郑西南部", "示范县西南部"),
    ("南郑东部", "示范县东部"),
    ("南郑南部", "示范县南部"),
    ("南郑西部", "示范县西部"),
    ('township="南郑"', 'township="示范镇"'),
    ("township: '南郑'", "township: '示范镇'"),
    ("fromPlace:'南郑'", "fromPlace:'示范镇'"),
    ("toPlace:'汉中'", "toPlace:'示范市'"),
    ("fromAddr: '南郑'", "fromAddr: '示范镇'"),
    ("toAddr: '汉中'", "toAddr: '示范市'"),
    ('"fromAddr": "南郑"', '"fromAddr": "示范镇"'),
    ('"toAddr": "汉中"', '"toAddr": "示范市"'),
    ('or "南郑"', 'or "示范镇"'),
    ("# 南郑区", "# 示范县"),
    ("南郑区 GeoJSON", "示范县 GeoJSON"),
    ("南郑坐标", "示范县坐标"),
    ("陕西省 → 汉中市 → 南郑区", "陕西省 → 示范市 → 示范县"),
    ('"name": "南郑区"', '"name": "示范县"'),
    ('"address": (c.address if c else "汉中市")', '"address": (c.address if c else "示范市")'),
    ('"dest": "汉中"', '"dest": "示范市"'),
]

ROOT = Path(__file__).resolve().parents[1]
INCLUDE_DIRS = ["backend/app", "frontend/apps/admin/src", "scripts"]
INCLUDE_FILES = [
    "frontend/apps/admin/public/cockpit/nanzheng.json",
    "backend/frontend/apps/admin/public/cockpit/nanzheng.json",
]
SKIP_PARTS = {"dist", "crawl_output", "__pycache__", ".git"}

files: list[Path] = []
for d in INCLUDE_DIRS:
    p = ROOT / d
    if not p.exists():
        continue
    for f in p.rglob("*"):
        if not f.is_file() or f.suffix not in {".py", ".vue", ".json", ".csv", ".js"}:
            continue
        if any(s in f.parts for s in SKIP_PARTS):
            continue
        if f.name == "cleanup_demo_names.py" or f.name == "seed_upgrade.py":
            continue
        files.append(f)

for rel in INCLUDE_FILES:
    f = ROOT / rel
    if f.exists():
        files.append(f)

changed: list[str] = []
for f in sorted(set(files)):
    try:
        text = f.read_text(encoding="utf-8")
    except OSError:
        continue
    orig = text
    for old, new in REPLACEMENTS:
        text = text.replace(old, new)
    if text != orig:
        f.write_text(text, encoding="utf-8")
        changed.append(str(f.relative_to(ROOT)))

print(f"Updated {len(changed)} files:")
for c in changed:
    print(f"  {c}")
