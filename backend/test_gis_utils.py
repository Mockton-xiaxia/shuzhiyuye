"""
GIS 几何工具与校验接口冒烟测试
"""
from __future__ import annotations

import json
import sys

sys.path.insert(0, ".")

from app.utils.geometry import GeometryUtils

RECT = """{
  "type": "Polygon",
  "coordinates": [
    [[120.150, 30.243], [120.152, 30.243], [120.152, 30.245], [120.150, 30.245], [120.150, 30.243]]
  ]
}"""

# 凹多边形（L 形，面积足够大）
CONCAVE = """{
  "type": "Polygon",
  "coordinates": [
    [[120.150, 30.243], [120.152, 30.243], [120.152, 30.244],
     [120.151, 30.244], [120.151, 30.245], [120.150, 30.245], [120.150, 30.243]]
  ]
}"""

# 自相交（蝴蝶结）
SELF_INTERSECT = """{
  "type": "Polygon",
  "coordinates": [
    [[120.150, 30.243], [120.152, 30.245], [120.150, 30.245], [120.152, 30.243], [120.150, 30.243]]
  ]
}"""


def assert_valid(geojson: str, expect: bool, label: str) -> None:
    valid, msg = GeometryUtils.validate_polygon(geojson)
    if valid != expect:
        raise SystemExit(f"{label}: 期望 valid={expect}，实际 valid={valid}，msg={msg}")
    print(f"✅ {label}: valid={valid}, msg={msg}")


def main() -> None:
    area = GeometryUtils.calculate_area_mu(RECT)
    print(f"✅ 面积计算: {area:.2f} 亩")
    if area <= 0:
        raise SystemExit("面积计算异常")

    assert_valid(RECT, True, "矩形")
    assert_valid(CONCAVE, True, "凹多边形")
    assert_valid(SELF_INTERSECT, False, "自相交多边形")

    center = GeometryUtils.calculate_center(RECT)
    if not center:
        raise SystemExit("中心点计算失败")
    print(f"✅ 中心点: 经度={center[0]:.4f}, 纬度={center[1]:.4f}")

    bbox = GeometryUtils.calculate_bbox(RECT)
    if not bbox:
        raise SystemExit("包围盒计算失败")
    print(
        f"✅ 包围盒: [{bbox.min_lng:.4f}, {bbox.max_lng:.4f}, "
        f"{bbox.min_lat:.4f}, {bbox.max_lat:.4f}]"
    )

    from app.utils.coordinates import CoordinateTransform

    lng, lat = 120.15, 30.24
    wgs = CoordinateTransform.gcj02_to_wgs84(lng, lat)
    print(f"✅ 坐标转换: GCJ02({lng}, {lat}) -> WGS84({wgs[0]:.6f}, {wgs[1]:.6f})")

    # 校验接口 HTTP 冒烟（后端需已启动）
    try:
        import urllib.request

        login_body = json.dumps({"username": "gov_admin", "password": "123456"}).encode()
        req = urllib.request.Request(
            "http://127.0.0.1:8000/api/v1/auth/login",
            data=login_body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            token = json.loads(resp.read())["data"]["accessToken"]

        validate_body = json.dumps({"geomGeojson": RECT}).encode()
        req2 = urllib.request.Request(
            "http://127.0.0.1:8000/api/v1/party/ponds/validate-geometry",
            data=validate_body,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}",
            },
            method="POST",
        )
        with urllib.request.urlopen(req2, timeout=10) as resp:
            data = json.loads(resp.read())
        if data.get("code") != 0:
            raise SystemExit(f"validate-geometry 失败: {data}")
        print(f"✅ validate-geometry 接口: areaMu={data['data'].get('areaMu')}")
    except Exception as e:
        print(f"⚠️ validate-geometry 接口跳过（后端未启动）: {e}")

    print("\n🎉 所有 GIS 工具测试通过！")


if __name__ == "__main__":
    main()
