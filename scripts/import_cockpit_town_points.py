# -*- coding: utf-8 -*-
"""
将 CSV 导入驾驶舱乡镇点位配置。

CSV 表头（UTF-8）：
  level,name,lon,lat,parent
  town,高台镇,106.854999,33.018699,
  village,高台社区,106.858,33.022,高台镇

用法：
  cd backend
  uv run python ../scripts/import_cockpit_town_points.py ../path/to/points.csv
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "backend" / "app" / "data" / "cockpit_town_points.json"


def main() -> None:
    if len(sys.argv) < 2:
        print("用法: uv run python scripts/import_cockpit_town_points.py <points.csv>")
        sys.exit(1)
    csv_path = Path(sys.argv[1])
    cfg = json.loads(TARGET.read_text(encoding="utf-8")) if TARGET.is_file() else {"towns": {}}
    towns = cfg.setdefault("towns", {})

    with csv_path.open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            level = (row.get("level") or "").strip().lower()
            name = (row.get("name") or "").strip()
            parent = (row.get("parent") or "").strip()
            if not name:
                continue
            try:
                lon = float(row["lon"])
                lat = float(row["lat"])
            except (KeyError, ValueError):
                print("跳过无效行:", row)
                continue
            if level == "town":
                towns.setdefault(name, {})
                towns[name]["lon"] = lon
                towns[name]["lat"] = lat
                towns[name]["source"] = f"CSV 导入 {csv_path.name}"
            elif level == "village" and parent:
                towns.setdefault(parent, {})
                towns[parent].setdefault("villages", {})
                towns[parent]["villages"][name] = {"lon": lon, "lat": lat}
            else:
                print("跳过未知 level:", row)

    TARGET.write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("已写入", TARGET, "乡镇数", len(towns))


if __name__ == "__main__":
    main()
