"""生成 docs/screenshots/*.png 演示截图（无需启动前端）。

用法:
  cd backend && uv run python ../scripts/generate_docs_screenshots.py
  cd backend && uv run python ../scripts/generate_docs_screenshots.py --out ../github-release/shuzhi-fishery-platform/docs/screenshots
"""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Callable

from PIL import Image, ImageDraw, ImageFont

W, H = 1440, 900
ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "github-release" / "shuzhi-fishery-platform" / "docs" / "screenshots"

# 配色（与 Login.vue / Element Plus 风格一致）
GREEN = "#0b6e4f"
GREEN_DARK = "#084a38"
GREEN_LIGHT = "#e9f5f1"
BLUE = "#409EFF"
GRAY_BG = "#f5f7fa"
GRAY_BORDER = "#e4e7ed"
GRAY_TEXT = "#606266"
WHITE = "#ffffff"
SIDEBAR_W = 220


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "C:/Windows/Fonts/msyhbd.ttc" if bold else "C:/Windows/Fonts/msyh.ttc",
        "C:/Windows/Fonts/simhei.ttf",
        "C:/Windows/Fonts/simsun.ttc",
    ]
    for path in candidates:
        p = Path(path)
        if p.exists():
            try:
                return ImageFont.truetype(str(p), size)
            except OSError:
                continue
    return ImageFont.load_default()


def _rect(draw: ImageDraw.ImageDraw, xy, fill, outline=None, r=4):
    draw.rounded_rectangle(xy, radius=r, fill=fill, outline=outline)


def _btn(draw, x, y, w, h, text, primary=False):
    fill = BLUE if primary else WHITE
    fg = WHITE if primary else GRAY_TEXT
    _rect(draw, (x, y, x + w, y + h), fill, GRAY_BORDER if not primary else BLUE)
    draw.text((x + w // 2, y + h // 2), text, fill=fg, font=_font(13), anchor="mm")


def _table(draw, x, y, w, headers, rows, col_widths=None):
    if not col_widths:
        col_widths = [w // len(headers)] * len(headers)
    row_h = 36
    header_h = 40
    _rect(draw, (x, y, x + w, y + header_h), "#fafafa", GRAY_BORDER)
    cx = x
    for i, h in enumerate(headers):
        draw.text((cx + 12, y + header_h // 2), h, fill=GRAY_TEXT, font=_font(13, True), anchor="lm")
        cx += col_widths[i]
    for ri, row in enumerate(rows):
        ry = y + header_h + ri * row_h
        bg = WHITE if ri % 2 == 0 else "#fafcff"
        _rect(draw, (x, ry, x + w, ry + row_h), bg, GRAY_BORDER)
        cx = x
        for i, cell in enumerate(row):
            color = BLUE if cell in ("编辑", "进入", "审核", "查看", "提交", "备案") else "#303133"
            draw.text((cx + 12, ry + row_h // 2), str(cell), fill=color, font=_font(12), anchor="lm")
            cx += col_widths[i]


def _sidebar(draw, items, active: str):
    _rect(draw, (0, 0, SIDEBAR_W, H), GREEN_DARK)
    draw.text((SIDEBAR_W // 2, 28), "数智渔业", fill=WHITE, font=_font(18, True), anchor="mm")
    draw.text((SIDEBAR_W // 2, 52), "监管平台", fill="#a8d5c8", font=_font(11), anchor="mm")
    y = 80
    for item in items:
        is_active = item == active
        if is_active:
            _rect(draw, (8, y, SIDEBAR_W - 8, y + 36), GREEN, r=6)
        draw.text((24, y + 18), item, fill=WHITE if is_active else "#c8e6d9", font=_font(13), anchor="lm")
        y += 42


def _header(draw, title: str, user: str = "gov_admin"):
    _rect(draw, (SIDEBAR_W, 0, W, 56), WHITE, GRAY_BORDER)
    draw.text((SIDEBAR_W + 24, 28), title, fill="#303133", font=_font(16, True), anchor="lm")
    draw.text((W - 24, 28), user, fill=GRAY_TEXT, font=_font(13), anchor="rm")


def _admin_page(title, menu, active, user, content_fn: Callable[[ImageDraw.ImageDraw, int, int], None]):
    img = Image.new("RGB", (W, H), GRAY_BG)
    draw = ImageDraw.Draw(img)
    _sidebar(draw, menu, active)
    _header(draw, title, user)
    content_fn(draw, SIDEBAR_W + 24, 72)
    return img


GOV_MENU = [
    "工作台", "领导驾驶舱", "质量抽检", "质量整改", "标识审核",
    "尾水计划", "GIS 塘口", "养殖主体", "用户管理", "政策管理",
]

ENT_MENU = [
    "工作台", "企业大屏", "养殖批次", "农事记录", "投入品",
    "仓储库存", "销售订单", "标识申请", "尾水排放", "物联监测",
]


def shot_login() -> Image.Image:
    img = Image.new("RGB", (W, H), GREEN_LIGHT)
    draw = ImageDraw.Draw(img)
    # 背景渐变感
    for i in range(H):
        c = int(233 + (247 - 233) * i / H)
        draw.line([(0, i), (W, i)], fill=(c, 245, 241))
    px, py, pw, ph = 510, 220, 420, 380
    _rect(draw, (px, py, px + pw, py + ph), (255, 255, 255, 235), r=16)
    draw.text((px + pw // 2, py + 40), "数智渔业平台", fill=GREEN, font=_font(28, True), anchor="mm")
    draw.text((px + pw // 2, py + 72), "绿色循环渔业 · 双门户登录", fill="#678899", font=_font(14), anchor="mm")
    draw.text((px + 36, py + 120), "账号", fill=GRAY_TEXT, font=_font(13))
    _rect(draw, (px + 36, py + 142, px + pw - 36, py + 178), WHITE, GRAY_BORDER)
    draw.text((px + 48, py + 160), "gov_admin", fill="#303133", font=_font(14), anchor="lm")
    draw.text((px + 36, py + 200), "密码", fill=GRAY_TEXT, font=_font(13))
    _rect(draw, (px + 36, py + 222, px + pw - 36, py + 258), WHITE, GRAY_BORDER)
    draw.text((px + 48, py + 240), "••••••", fill="#303133", font=_font(14), anchor="lm")
    _btn(draw, px + 36, py + 290, pw - 72, 40, "登 录", primary=True)
    draw.text((px + pw // 2, py + 350), "演示：区县 gov_admin / 企业 ent_admin，密码 123456", fill="#8899aa", font=_font(11), anchor="mm")
    return img


def shot_gov_workbench() -> Image.Image:
    def content(draw, x, y):
        cards = [("待办事项", "12", BLUE), ("质量整改", "3", "#E6A23C"), ("标识审核", "5", GREEN), ("尾水备案", "2", "#909399")]
        cw = 260
        for i, (t, n, c) in enumerate(cards):
            cx = x + i * (cw + 16)
            _rect(draw, (cx, y, cx + cw, y + 100), WHITE, GRAY_BORDER, r=8)
            draw.text((cx + 20, y + 24), t, fill=GRAY_TEXT, font=_font(14))
            draw.text((cx + 20, y + 58), n, fill=c, font=_font(32, True))
        draw.text((x, y + 130), "快捷入口", fill="#303133", font=_font(15, True))
        links = ["质量抽检工作台", "标识申请审核", "尾水计划备案", "GIS 塘口审核", "养殖主体维护"]
        for i, link in enumerate(links):
            ly = y + 160 + i * 44
            _rect(draw, (x, ly, x + 680, ly + 36), WHITE, GRAY_BORDER)
            draw.text((x + 16, ly + 18), link, fill="#303133", font=_font(13), anchor="lm")
            draw.text((x + 640, ly + 18), "进入 →", fill=BLUE, font=_font(13), anchor="rm")

    return _admin_page("工作台", GOV_MENU, "工作台", "gov_admin · 区县", content)


def shot_ent_workbench() -> Image.Image:
    def content(draw, x, y):
        cards = [("在养批次", "8", GREEN), ("待出塘", "2", BLUE), ("库存预警", "1", "#F56C6C"), ("物联告警", "0", "#909399")]
        cw = 260
        for i, (t, n, c) in enumerate(cards):
            cx = x + i * (cw + 16)
            _rect(draw, (cx, y, cx + cw, y + 100), WHITE, GRAY_BORDER, r=8)
            draw.text((cx + 20, y + 24), t, fill=GRAY_TEXT, font=_font(14))
            draw.text((cx + 20, y + 58), n, fill=c, font=_font(32, True))
        draw.text((x, y + 130), "今日待办", fill="#303133", font=_font(15, True))
        _table(draw, x, y + 160, 1100, ["事项", "状态", "操作"], [
            ["批次 B2026-03 休药期检查", "待处理", "进入"],
            ["标识申请 #1042", "审核中", "查看"],
            ["尾水排放计划 7月", "草稿", "编辑"],
        ], [500, 200, 120])

    return _admin_page("工作台", ENT_MENU, "工作台", "ent_admin · 企业", content)


def shot_cockpit() -> Image.Image:
    img = Image.new("RGB", (W, H), "#0a1628")
    draw = ImageDraw.Draw(img)
    draw.text((W // 2, 36), "南漳县渔业领导驾驶舱", fill="#00e5ff", font=_font(24, True), anchor="mm")
    metrics = [("养殖主体", "126"), ("塘口面积", "3,842亩"), ("尾水达标率", "96.2%"), ("抽检合格率", "98.5%")]
    for i, (k, v) in enumerate(metrics):
        cx = 80 + i * 340
        _rect(draw, (cx, 70, cx + 300, 150), "#132238", "#1e3a5f", r=8)
        draw.text((cx + 150, 100), k, fill="#8ab4d4", font=_font(13), anchor="mm")
        draw.text((cx + 150, 130), v, fill="#00e5ff", font=_font(22, True), anchor="mm")
    _rect(draw, (80, 180, 720, 520), "#132238", "#1e3a5f", r=8)
    draw.text((400, 200), "区域养殖分布", fill="#8ab4d4", font=_font(14), anchor="mm")
    for i in range(6):
        draw.ellipse([180 + i * 90, 280 + (i % 3) * 60, 230 + i * 90, 330 + (i % 3) * 60], fill="#0b6e4f")
    _rect(draw, (760, 180, 1360, 520), "#132238", "#1e3a5f", r=8)
    draw.text((1060, 200), "尾水排放趋势", fill="#8ab4d4", font=_font(14), anchor="mm")
    for i, h in enumerate([120, 180, 140, 200, 160, 190, 170]):
        draw.rectangle([820 + i * 70, 480 - h, 860 + i * 70, 480], fill="#409EFF")
    _rect(draw, (80, 550, 1360, 860), "#132238", "#1e3a5f", r=8)
    draw.text((720, 570), "质量抽检与整改动态", fill="#8ab4d4", font=_font(14), anchor="mm")
    _table(draw, 100, 600, 1240, ["时间", "企业", "类型", "状态"], [
        ["07-24 14:20", "鱼秀坊养殖", "抽检", "合格"],
        ["07-23 09:15", "绿源水产", "整改", "复核中"],
        ["07-22 16:40", "汉水渔场", "标识", "已通过"],
    ], [200, 300, 200, 200])
    return img


def shot_quality() -> Image.Image:
    def content(draw, x, y):
        _btn(draw, x, y, 80, 32, "新建", primary=True)
        _btn(draw, x + 90, y, 80, 32, "查询")
        _table(draw, x, y + 48, 1100, ["批次号", "企业", "检测机构", "结果", "操作"], [
            ["QC-2026-071", "鱼秀坊养殖", "市检中心", "合格", "查看"],
            ["QC-2026-068", "绿源水产", "县检站", "不合格", "整改"],
            ["QC-2026-065", "汉水渔场", "第三方", "合格", "查看"],
        ], [160, 220, 180, 100, 100])

    return _admin_page("质量抽检", GOV_MENU, "质量抽检", "gov_admin · 区县", content)


def shot_trace() -> Image.Image:
    def content(draw, x, y):
        _btn(draw, x, y, 80, 32, "查询")
        _table(draw, x, y + 48, 1100, ["申请号", "企业", "数量", "状态", "操作"], [
            ["TA-1042", "鱼秀坊养殖", "5000枚", "待审核", "审核"],
            ["TA-1038", "绿源水产", "3000枚", "已通过", "查看"],
            ["TA-1035", "汉水渔场", "8000枚", "已分发", "查看"],
        ], [140, 240, 120, 120, 100])

    return _admin_page("标识审核", GOV_MENU, "标识审核", "gov_admin · 区县", content)


def shot_effluent() -> Image.Image:
    def content(draw, x, y):
        _btn(draw, x, y, 80, 32, "新建", primary=True)
        _table(draw, x, y + 48, 1100, ["计划编号", "企业", "排放水域", "状态", "操作"], [
            ["EP-2026-07", "鱼秀坊养殖", "汉水支流", "草稿", "编辑"],
            ["EP-2026-06", "绿源水产", "内湖", "已备案", "查看"],
            ["EP-2026-05", "汉水渔场", "渠道", "已驳回", "编辑"],
        ], [160, 200, 180, 120, 120])

    return _admin_page("尾水排放计划", GOV_MENU, "尾水计划", "gov_admin · 区县", content)


def shot_gis() -> Image.Image:
    def content(draw, x, y):
        _rect(draw, (x, y, x + 760, y + 520), "#d4e8dc", GRAY_BORDER)
        draw.text((x + 380, y + 260), "OpenLayers 地图 · 塘口多边形", fill=GREEN, font=_font(16), anchor="mm")
        for pts in [(120, 80, 200, 60), (300, 120, 180, 100), (180, 280, 220, 80)]:
            draw.polygon([(x + pts[0], y + pts[1]), (x + pts[0] + pts[2], y + pts[1]), (x + pts[0] + pts[2], y + pts[1] + pts[3]), (x + pts[0], y + pts[1] + pts[3])], fill=(11, 110, 79, 80), outline=GREEN)
        _rect(draw, (x + 780, y, x + 1100, y + 520), WHITE, GRAY_BORDER)
        draw.text((x + 800, y + 20), "塘口列表", fill="#303133", font=_font(14, True))
        _table(draw, x + 790, y + 48, 300, ["名称", "面积", "状态"], [
            ["1号塘", "32亩", "待审"],
            ["2号塘", "28亩", "已通过"],
            ["3号塘", "45亩", "采集中"],
        ], [100, 80, 80])

    return _admin_page("GIS 塘口采集", GOV_MENU, "GIS 塘口", "gov_admin · 区县", content)


def shot_enterprise() -> Image.Image:
    def content(draw, x, y):
        fields = [("主体名称", "鱼秀坊养殖有限公司"), ("统一社会信用代码", "91420600MA4XXXXXX"), ("负责人", "余秀芳"), ("联系电话", "138****5678"), ("养殖品种", "草鱼、鲫鱼")]
        fy = y
        for label, val in fields:
            draw.text((x, fy), label, fill=GRAY_TEXT, font=_font(13))
            _rect(draw, (x + 140, fy - 8, x + 520, fy + 24), WHITE, GRAY_BORDER)
            draw.text((x + 152, fy + 8), val, fill="#303133", font=_font(13), anchor="lm")
            fy += 44
        draw.text((x, fy + 10), "养殖品种明细", fill="#303133", font=_font(14, True))
        _table(draw, x, fy + 40, 700, ["品种", "面积(亩)", "模式"], [
            ["草鱼", "120", "池塘"],
            ["鲫鱼", "80", "池塘"],
        ], [200, 200, 200])
        _btn(draw, x + 720, y, 80, 36, "提交", primary=True)

    return _admin_page("养殖主体维护", GOV_MENU, "养殖主体", "gov_admin · 区县", content)


def shot_users() -> Image.Image:
    def content(draw, x, y):
        _btn(draw, x, y, 80, 32, "新增", primary=True)
        _table(draw, x, y + 48, 1100, ["用户名", "姓名", "角色", "门户", "操作"], [
            ["gov_admin", "南漳县管理员", "区县管理员", "GOV", "编辑"],
            ["ent_admin", "余秀芳", "企业用户", "ENT", "编辑"],
            ["inspector01", "张检查", "检测员", "GOV", "编辑"],
        ], [140, 160, 160, 100, 100])

    return _admin_page("用户管理", GOV_MENU, "用户管理", "gov_admin · 区县", content)


def shot_api_docs() -> Image.Image:
    img = Image.new("RGB", (W, H), WHITE)
    draw = ImageDraw.Draw(img)
    _rect(draw, (0, 0, W, 56), "#1b1b1b")
    draw.text((24, 28), "Swagger UI — 数智渔业平台 API", fill=WHITE, font=_font(16, True), anchor="lm")
    draw.text((W - 24, 28), "http://127.0.0.1:8000/docs", fill="#aaa", font=_font(12), anchor="rm")
    sections = [
        ("auth", "POST /api/v1/auth/login", "用户登录"),
        ("party", "GET /api/v1/party/enterprises", "养殖主体列表"),
        ("quality", "POST /api/v1/quality/rectifications", "下发质量整改"),
        ("effluent", "PUT /api/v1/effluent/plans/{id}", "尾水计划编辑"),
        ("trace", "POST /api/v1/trace/applies/{id}/approve", "标识审核通过"),
        ("fill", "PUT /api/v1/fill/feature/update", "通用字段更新"),
    ]
    y = 80
    for tag, path, desc in sections:
        _rect(draw, (40, y, W - 40, y + 56), "#fafafa", GRAY_BORDER)
        draw.text((60, y + 18), tag.upper(), fill=WHITE, font=_font(11), anchor="lm")
        _rect(draw, (60, y + 10, 60 + len(tag) * 10 + 16, y + 30), GREEN, r=4)
        draw.text((60 + (len(tag) * 10 + 16) // 2, y + 20), tag.upper(), fill=WHITE, font=_font(10), anchor="mm")
        draw.text((140, y + 20), path, fill="#303133", font=_font(13, True), anchor="lm")
        draw.text((140, y + 38), desc, fill=GRAY_TEXT, font=_font(12), anchor="lm")
        y += 64
    draw.text((W // 2, H - 40), "完整规范见 docs/openapi.json", fill="#999", font=_font(12), anchor="mm")
    return img


SHOTS: list[tuple[str, Callable[[], Image.Image]]] = [
    ("01-login.png", shot_login),
    ("02-gov-workbench.png", shot_gov_workbench),
    ("03-ent-workbench.png", shot_ent_workbench),
    ("04-gov-cockpit.png", shot_cockpit),
    ("05-quality-inspection.png", shot_quality),
    ("06-trace-apply.png", shot_trace),
    ("07-effluent-plan.png", shot_effluent),
    ("08-enterprise-gis.png", shot_gis),
    ("09-party-enterprise.png", shot_enterprise),
    ("10-user-manage.png", shot_users),
    ("11-api-docs.png", shot_api_docs),
]


def generate(out_dir: Path) -> int:
    out_dir.mkdir(parents=True, exist_ok=True)
    for fname, fn in SHOTS:
        path = out_dir / fname
        fn().save(path, "PNG", optimize=True)
        print("OK", path)
    readme = out_dir / "README.txt"
    readme.write_text(
        "本目录为功能演示截图（PNG）。\n"
        "若已安装 Node.js 与 Playwright，可运行 scripts/_capture_screenshots.py 替换为真实页面截图。\n"
        "生成占位 PNG：uv run python scripts/generate_docs_screenshots.py\n",
        encoding="utf-8",
    )
    return len(SHOTS)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    n = generate(args.out)
    print(f"Generated {n} PNG screenshots -> {args.out}")


if __name__ == "__main__":
    main()
