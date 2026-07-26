"""打包 GitHub 开源发布目录：源码 + 文档 + API + 截图说明。"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import urllib.request
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RELEASE = ROOT / "github-release" / "shuzhi-fishery-platform"
DOCS = RELEASE / "docs"
SCREENSHOTS = DOCS / "screenshots"

EXCLUDE_DIRS = {
    "node_modules",
    ".venv",
    "__pycache__",
    ".git",
    ".cursor",
    "agent-transcripts",
    "terminals",
    "github-release",
    "dist",  # 源码包不含构建产物，用户自行 npm run build
}

EXCLUDE_FILES = {
    ".env",
    "fishery.db",
    ".DS_Store",
    "Thumbs.db",
}

EXCLUDE_GLOBS = ["*.pyc", "*.pyo", "*.log"]

# crawl_output 仅复制验收/设计摘要，跳过含现网爬取敏感内容的原始抓取
CRAWL_INCLUDE = {
    "11-全量验收记录.md",
    "12-数据库全量检查.md",
    "17-全栈自检报告-2026-07-25.md",
    "00-详细设计索引.md",
}


def should_skip(path: Path, base: Path) -> bool:
    rel = path.relative_to(base)
    parts = rel.parts
    for p in parts:
        if p in EXCLUDE_DIRS:
            return True
    if path.name in EXCLUDE_FILES:
        return True
    if path.suffix in (".pyc", ".pyo"):
        return True
    return False


def copy_tree(src: Path, dst: Path, base: Path) -> int:
    n = 0
    if not src.exists():
        return 0
    for item in src.rglob("*"):
        if should_skip(item, base):
            continue
        rel = item.relative_to(base)
        target = dst / rel
        if item.is_dir():
            target.mkdir(parents=True, exist_ok=True)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, target)
            n += 1
    return n


def fetch_openapi() -> dict:
    url = "http://127.0.0.1:8000/openapi.json"
    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"WARN: cannot fetch openapi ({e}), using stub")
        return {"paths": {}, "info": {"title": "数智渔业平台", "version": "1.0.0"}}


def gen_api_md(spec: dict) -> str:
    lines = [
        "# API 接口文档",
        "",
        f"> 自动生成 · 前缀 `/api/v1` · {datetime.now().strftime('%Y-%m-%d')}",
        "",
        "## 在线文档",
        "",
        "启动后端后访问：",
        "",
        "- Swagger UI: http://localhost:8000/docs",
        "- ReDoc: http://localhost:8000/redoc",
        "- OpenAPI JSON: http://localhost:8000/openapi.json",
        "",
        "## 认证",
        "",
        "```http",
        "POST /api/v1/auth/login",
        "Content-Type: application/json",
        "",
        '{"username":"gov_admin","password":"123456"}',
        "```",
        "",
        "响应 `data.accessToken` 用于后续请求：",
        "",
        "```",
        "Authorization: Bearer <accessToken>",
        "```",
        "",
        "## 演示账号",
        "",
        "| 用户名 | 密码 | 门户 |",
        "|--------|------|------|",
        "| gov_admin | 123456 | 区县 GOV |",
        "| ent_admin | 123456 | 企业 ENT |",
        "",
        "## 接口清单",
        "",
    ]
    paths = spec.get("paths") or {}
    grouped: dict[str, list[tuple[str, str, dict]]] = {}
    for path, methods in sorted(paths.items()):
        if not path.startswith("/api/v1"):
            continue
        short = path.replace("/api/v1", "") or "/"
        tag = "other"
        for meth, detail in methods.items():
            if meth in ("get", "post", "put", "delete", "patch"):
                tags = detail.get("tags") or ["other"]
                tag = tags[0]
                grouped.setdefault(tag, []).append((meth.upper(), short, detail))

    for tag in sorted(grouped.keys()):
        lines.append(f"### {tag}")
        lines.append("")
        lines.append("| 方法 | 路径 | 说明 |")
        lines.append("|------|------|------|")
        for meth, short, detail in sorted(grouped[tag], key=lambda x: x[1]):
            summary = (detail.get("summary") or detail.get("operationId") or "-").replace("|", "\\|")
            lines.append(f"| {meth} | `{short}` | {summary} |")
        lines.append("")

    lines += [
        "## 核心业务域",
        "",
        "| 域 | 前缀 | 说明 |",
        "|----|------|------|",
        "| 平台 | `/auth`, `/todos` | 登录、待办 |",
        "| 系统 | `/system` | 用户、角色 |",
        "| 主体 | `/party` | 企业、塘口、GIS、人员 |",
        "| 质量 | `/quality` | 政策、抽检、整改 |",
        "| 追溯 | `/trace` | 标识申请、分发 |",
        "| 尾水 | `/effluent` | 计划、巡检、调度 |",
        "| 养殖 | `/breeding` | 批次、农事、销售 |",
        "| 物联 | `/iot` | 设备、摄像头、告警 |",
        "| 仓储 | `/wms`, `/inputs` | 仓库、库存、投入品 |",
        "| 账本 | `/ledger` | 客户、合同、记账 |",
        "| 流通 | `/circulation` | 销售订单、运输 |",
        "| 供应 | `/supply` | 渔需推介、行情 |",
        "| 资讯 | `/cms` | 文章、视频 |",
        "| 分析 | `/analytics` | 驾驶舱、企业大屏 |",
        "| 通用 | `/feature/update` | CrudPage 编辑兜底 |",
        "",
    ]
    return "\n".join(lines)


def gen_features_md() -> str:
    return """# 功能说明

## 双门户架构

| 门户 | 路径前缀 | 角色 | 能力 |
|------|----------|------|------|
| 区县监管 GOV | `/gov/*` | 区县管理员 | 审核、备案、统计、政策 |
| 企业生产 ENT | `/ent/*` | 企业用户 | 生产、仓储、物联、销售 |

## 核心功能模块

### 1. 工作台 & 待办
- 登录后按门户展示菜单与待办
- 支持质量整改、标识审核、塘口审核等流程待办跳转

### 2. 质量安全
- 政策管理、检测机构、质量抽检（工作台）
- 质量整改流程：下发 → 企业接收/回复 → 区县复核
- 标识申请/审核/分发/统计

### 3. 尾水监管
- 排放水域、尾水排放计划（草稿→提交→备案/驳回，**支持草稿编辑**）
- 巡检记录、指挥调度、整改记录

### 4. 主体 & GIS
- 养殖主体深表单（区县列表 + 企业自维护）
- 塘口采集/审核/统计，GeoJSON 导入，几何校验

### 5. 养殖生产
- 批次、农事、销售；投入品、仓储、库存
- 休药期校验（出塘前检查）

### 6. 物联 & 视频
- 水质/尾水/气象监测（只读）
- 设备规则、摄像头、萤石云配置、告警确认/关闭

### 7. 账本 & 流通
- 客户、合同、手工记账、售后
- 销售订单状态流、运输管理

### 8. 大屏
- 区县领导驾驶舱、企业大屏（ECharts + 地图）

## 页面类型

| shape | 说明 |
|-------|------|
| crud | 通用列表增删改查（CrudPage） |
| workbench | 工作台（内置 FeaturePage 路由） |
| gis | 地图采集/审核/统计 |
| screen | 大屏 |
| enterprise | 养殖主体深表单 |

## 数据持久化策略

- **专用 PUT**：用户、主体、塘口、批次等
- **feature/update**：通用编辑兜底，见 `backend/app/routers/fill.py`
- **只读页**：统计、监测、演示型页面（features.json `readonly: true`）
- **流程页**：整改、标识、销售订单等走状态 API，非行内编辑
"""


def gen_database_md() -> str:
    return """# 数据库说明

## 引擎

- **开发默认**：SQLite（`backend/fishery.db`，首次启动自动建表+种子）
- **生产推荐**：PostgreSQL（见 `docker-compose.yml` PostGIS 服务）

## 表规模

- ORM 模型 **70** 张表，与 SQLite 结构一致
- 启动时 `create_all` + `seed_upgrade` 幂等迁移（补列、演示数据）

## 核心表分组

| 前缀 | 示例表 | 说明 |
|------|--------|------|
| sys_ | sys_user, sys_menu, sys_role | 平台用户权限菜单 |
| biz_ | biz_enterprise, biz_pond, biz_staff | 主体资源 |
| qa_ | qa_policy, qa_inspection, qa_rectification | 质量安全 |
| tr_ | tr_mark_apply, tr_mark_code | 追溯标识 |
| ef_ | ef_discharge_plan, ef_patrol | 尾水监管 |
| br_ | br_batch, br_activity, br_sale | 养殖生产 |
| in_/wm_ | in_item, wm_stock, wm_warehouse | 投入品仓储 |
| lg_/ci_ | lg_customer, ci_sales_order | 账本流通 |
| iot_ | iot_camera, iot_rule, iot_alarm | 物联 |
| cms_/su_ | cms_article, su_listing | 资讯供应 |

## 校验脚本

```powershell
cd backend
uv run python ..\\scripts\\audit_db_schema.py
```

报告输出：`docs/reports/数据库全量检查.md`（打包时复制）

## 配置

复制 `backend/.env.example` 为 `.env`，**务必修改** `JWT_SECRET`。
"""


def gen_deploy_md() -> str:
    return """# 部署指南

## 方式一：本机开发（推荐上手）

### 环境
- Python 3.11+（推荐 uv）
- Node.js 20+
- 可选：Docker Desktop

### 后端
```powershell
cd backend
uv sync
copy .env.example .env
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 前端
```powershell
cd frontend/apps/admin
npm install
npm run dev
```

- 管理端：http://localhost:5173
- API 文档：http://localhost:8000/docs

## 方式二：Docker Compose

```bash
docker compose up -d --build
```

- Web: http://localhost:8080
- API: http://localhost:8000

## 生产检查清单

- [ ] 修改 `JWT_SECRET` 为强随机字符串
- [ ] 配置 `CORS_ORIGINS` 为实际前端域名
- [ ] 使用 PostgreSQL 替代 SQLite
- [ ] 配置 HTTPS 反向代理（Nginx/Caddy）
- [ ] 定期备份数据库
- [ ] 萤石云密钥通过环境变量注入，勿提交仓库

## 验收

```powershell
cd backend
uv run python ..\\scripts\\accept_full.py
uv run python ..\\scripts\\smoke_edit.py
uv run python ..\\scripts\\audit_db_schema.py
uv run python ..\\scripts\\audit_edit_buttons.py
```
"""


def gen_readme(screenshot_ext: str = "png") -> str:
    img = f"docs/screenshots/01-login.{screenshot_ext}"
    return f"""# 数智渔业平台 · 开源版

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-green.svg)](backend/)
[![Vue 3](https://img.shields.io/badge/vue-3.x-brightgreen.svg)](frontend/)

> 面向区县监管与企业生产的 **双门户** 渔业数字化管理平台。  
> 涵盖质量追溯、尾水监管、GIS 塘口、养殖生产、物联监测、仓储账本等模块。

<p align="center">
  <img src="{img}" width="720" alt="登录页" />
</p>

## 特性亮点

- **双门户**：区县 GOV（31 菜单）+ 企业 ENT（63 菜单）
- **流程闭环**：质量整改、标识审核、尾水计划备案、销售订单履约
- **GIS 塘口**：OpenLayers 地图、GeoJSON 导入、几何面积校验
- **通用 CRUD**：配置驱动页面（`features.json`）+ 编辑白名单 + `feature/update` 兜底
- **开箱即用**：SQLite 零配置启动，内置演示账号与种子数据
- **可验收**：`accept_full.py` 全菜单 API 冒烟 + 数据库/schema 审计脚本

## 快速开始

```powershell
# 后端
cd backend && uv sync && uv run uvicorn app.main:app --port 8000

# 前端（新终端）
cd frontend/apps/admin && npm install && npm run dev
```

| 账号 | 密码 | 门户 |
|------|------|------|
| gov_admin | 123456 | 区县 |
| ent_admin | 123456 | 企业 |

## 文档

| 文档 | 说明 |
|------|------|
| [docs/API.md](docs/API.md) | 接口清单与认证 |
| [docs/FEATURES.md](docs/FEATURES.md) | 功能模块说明 |
| [docs/DATABASE.md](docs/DATABASE.md) | 数据库表结构 |
| [docs/DEPLOY.md](docs/DEPLOY.md) | 部署与生产清单 |
| [docs/功能使用说明.md](docs/功能使用说明.md) | **功能使用说明（操作手册）** |
| [docs/SCREENSHOTS.md](docs/SCREENSHOTS.md) | 功能截图索引 |
| [docs/openapi.json](docs/openapi.json) | OpenAPI 规范 |

## 技术栈

| 层 | 技术 |
|----|------|
| 后端 | FastAPI · SQLAlchemy 2 · JWT · Pydantic |
| 前端 | Vue 3 · Vite · Element Plus · Pinia · ECharts · OpenLayers |
| 数据库 | SQLite（开发）/ PostgreSQL（生产） |

## 目录结构

```
backend/                 FastAPI 应用、模型、路由、种子
frontend/apps/admin/     Vue3 管理端
scripts/                 验收、审计、打包脚本
docs/                    文档与截图
docker-compose.yml       容器化部署
```

## 截图预览

详见 [docs/SCREENSHOTS.md](docs/SCREENSHOTS.md)

## 开源协议

[MIT License](LICENSE)

## 致谢

本项目为渔业监管数字化演示/开源实现，设计参考行业监管业务流程。

---
打包时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}
"""


def gen_screenshots_md(use_svg: bool = False) -> str:
    ext = "svg" if use_svg else "png"
    shots = [
        (f"01-login.{ext}", "登录页", "双门户登录入口"),
        (f"02-gov-workbench.{ext}", "区县工作台", "待办与快捷入口"),
        (f"03-ent-workbench.{ext}", "企业工作台", "企业生产首页"),
        (f"04-gov-cockpit.{ext}", "领导驾驶舱", "区县大屏指标"),
        (f"05-quality-inspection.{ext}", "质量抽检", "抽检工作台"),
        (f"06-trace-apply.{ext}", "标识审核", "追溯标识流程"),
        (f"07-effluent-plan.{ext}", "尾水计划", "排放计划备案流"),
        (f"08-enterprise-gis.{ext}", "GIS 塘口", "地图采集/审核"),
        (f"09-party-enterprise.{ext}", "养殖主体", "主体深表单"),
        (f"10-user-manage.{ext}", "用户管理", "区县用户维护"),
        (f"11-api-docs.{ext}", "API 文档", "Swagger UI"),
    ]
    lines = ["# 功能截图", "", "> 路径：`docs/screenshots/`", ""]
    for fname, title, desc in shots:
        lines.append(f"## {title}")
        lines.append("")
        lines.append(f"![{title}](screenshots/{fname})")
        lines.append("")
        lines.append(f"{desc}")
        lines.append("")
    return "\n".join(lines)


def gen_gitignore() -> str:
    return """# Python
.venv/
__pycache__/
*.py[cod]
*.db
.env

# Node
node_modules/
dist/

# IDE
.idea/
.vscode/
*.swp

# OS
.DS_Store
Thumbs.db

# Uploads & logs
backend/uploads/*
!backend/uploads/.gitkeep
*.log
"""


def gen_license() -> str:
    year = datetime.now().year
    return f"""MIT License

Copyright (c) {year} 数智渔业平台 contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""


def try_capture_screenshots() -> bool:
    """尝试用 playwright 截图；失败则生成占位说明。"""
    script = RELEASE / "scripts" / "_capture_screenshots.py"
    script.write_text(
        '''"""Playwright 截图（需: uv pip install playwright && playwright install chromium）"""
import asyncio
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "docs" / "screenshots"
BASE = "http://127.0.0.1:5173"
API = "http://127.0.0.1:8000"

SHOTS = [
    ("01-login.png", "/login", None),
    ("02-gov-workbench.png", "/gov/workbench", ("gov_admin", "123456")),
    ("03-ent-workbench.png", "/ent/workbench", ("ent_admin", "123456")),
    ("04-gov-cockpit.png", "/gov/cockpit", ("gov_admin", "123456")),
    ("05-quality-inspection.png", "/gov/quality/inspections", ("gov_admin", "123456")),
    ("06-trace-apply.png", "/gov/trace/applies", ("gov_admin", "123456")),
    ("07-effluent-plan.png", "/gov/effluent/plans", ("gov_admin", "123456")),
    ("08-enterprise-gis.png", "/gov/party/gis-collect", ("gov_admin", "123456")),
    ("09-party-enterprise.png", "/gov/party/enterprises", ("gov_admin", "123456")),
    ("10-user-manage.png", "/gov/party/users", ("gov_admin", "123456")),
]

async def main():
    from playwright.async_api import async_playwright
    OUT.mkdir(parents=True, exist_ok=True)
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 1440, "height": 900})
        for fname, path, creds in SHOTS:
            if creds:
                await page.goto(f"{BASE}/login")
                await page.wait_for_timeout(800)
                await page.fill('input[placeholder*="用户"], input[type="text"]', creds[0])
                await page.fill('input[type="password"]', creds[1])
                await page.click('button:has-text("登录"), button[type="submit"]')
                await page.wait_for_timeout(1500)
            await page.goto(BASE + path)
            await page.wait_for_timeout(2000)
            await page.screenshot(path=str(OUT / fname), full_page=False)
            print("OK", fname)
        await page.goto(API + "/docs")
        await page.wait_for_timeout(1500)
        await page.screenshot(path=str(OUT / "11-api-docs.png"), full_page=False)
        print("OK 11-api-docs.png")
        await browser.close()

asyncio.run(main())
''',
        encoding="utf-8",
    )
    # 尝试 openapi docs 截图（不依赖前端）
    try:
        import urllib.request
        urllib.request.urlopen("http://127.0.0.1:8000/docs", timeout=3)
    except Exception:
        return False

    # 仅用 subprocess 调 playwright 若已安装
    try:
        result = subprocess.run(
            [sys.executable, str(script)],
            cwd=str(RELEASE),
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode == 0:
            print("Screenshots captured via Playwright")
            return True
        print("Playwright capture skipped:", result.stderr[:300] if result.stderr else result.stdout[:300])
    except Exception as e:
        print(f"Playwright not available: {e}")

    return False


def try_generate_png_screenshots() -> bool:
    """用 Pillow 生成 PNG 演示截图（无需 Node/Playwright）。"""
    gen = ROOT / "scripts" / "generate_docs_screenshots.py"
    if not gen.exists():
        return False
    try:
        result = subprocess.run(
            [sys.executable, str(gen), "--out", str(SCREENSHOTS)],
            cwd=str(ROOT / "backend"),
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode == 0:
            print("PNG screenshots generated via Pillow")
            return True
        print("PNG generation failed:", (result.stderr or result.stdout)[:300])
    except Exception as e:
        print(f"PNG generation error: {e}")
    return False


def create_placeholder_screenshots():
    """无浏览器时生成 SVG 占位图。"""
    SCREENSHOTS.mkdir(parents=True, exist_ok=True)
    placeholders = [
        ("01-login.png", "登录页", "#1a3a5c"),
        ("02-gov-workbench.png", "区县工作台", "#2d5016"),
        ("03-ent-workbench.png", "企业工作台", "#5c3d1a"),
        ("04-gov-cockpit.png", "领导驾驶舱", "#1a1a5c"),
        ("05-quality-inspection.png", "质量抽检", "#5c1a3a"),
        ("06-trace-apply.png", "标识审核", "#3a5c1a"),
        ("07-effluent-plan.png", "尾水计划", "#1a5c5c"),
        ("08-enterprise-gis.png", "GIS 塘口", "#4a4a2a"),
        ("09-party-enterprise.png", "养殖主体", "#2a4a4a"),
        ("10-user-manage.png", "用户管理", "#4a2a4a"),
        ("11-api-docs.png", "API 文档 Swagger", "#333355"),
    ]
    for fname, title, color in placeholders:
        svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="1440" height="900" viewBox="0 0 1440 900">
  <rect width="1440" height="900" fill="{color}"/>
  <rect x="40" y="40" width="1360" height="820" rx="8" fill="#ffffff" opacity="0.95"/>
  <text x="720" y="420" font-family="Arial,sans-serif" font-size="42" fill="#333" text-anchor="middle">{title}</text>
  <text x="720" y="480" font-family="Arial,sans-serif" font-size="20" fill="#666" text-anchor="middle">数智渔业平台 · 演示截图占位</text>
  <text x="720" y="520" font-family="Arial,sans-serif" font-size="16" fill="#999" text-anchor="middle">启动前后端后可运行 scripts/_capture_screenshots.py 生成真实截图</text>
</svg>'''
        # 保存为 svg（GitHub 可预览）；同时保留 .png 扩展名用 svg 内容需转换
        # 为兼容性写 svg 文件并在 SCREENSHOTS.md 说明
        (SCREENSHOTS / fname.replace(".png", ".svg")).write_text(svg, encoding="utf-8")

    note = SCREENSHOTS / "README.txt"
    note.write_text(
        "占位图为 .svg 格式。生成真实 PNG 截图：\n"
        "1. 启动后端 uvicorn 与前端 npm run dev\n"
        "2. uv pip install playwright && playwright install chromium\n"
        "3. python scripts/_capture_screenshots.py\n",
        encoding="utf-8",
    )


def _clear_release_keep_git() -> None:
    """清空发布目录内容，保留 .git（避免 Windows 锁 pack 导致 rmtree 失败）。"""
    if not RELEASE.exists():
        RELEASE.mkdir(parents=True)
        return
    for item in RELEASE.iterdir():
        if item.name == ".git":
            continue
        if item.is_dir():
            shutil.rmtree(item, ignore_errors=True)
        else:
            try:
                item.unlink()
            except OSError:
                pass


def main() -> None:
    _clear_release_keep_git()
    DOCS.mkdir(parents=True)
    (DOCS / "reports").mkdir(parents=True)
    SCREENSHOTS.mkdir(parents=True)

    print("Copying source...")
    n = 0
    for folder in ("backend", "frontend", "scripts"):
        src = ROOT / folder
        if src.exists():
            n += copy_tree(src, RELEASE / folder, src)
    # 根文件
    for f in ("docker-compose.yml", "README.md"):
        p = ROOT / f
        if p.exists():
            shutil.copy2(p, RELEASE / f)
            n += 1

    # crawl 摘要
    crawl_src = ROOT / "crawl_output"
    crawl_dst = RELEASE / "docs" / "design"
    crawl_dst.mkdir(parents=True, exist_ok=True)
    for name in CRAWL_INCLUDE:
        p = crawl_src / name
        if p.exists():
            shutil.copy2(p, crawl_dst / name)

    # 验收报告
    for name in ("11-全量验收记录.md", "12-数据库全量检查.md"):
        p = crawl_src / name
        if p.exists():
            shutil.copy2(p, DOCS / "reports" / name)

    # uploads gitkeep
    uploads = RELEASE / "backend" / "uploads"
    uploads.mkdir(parents=True, exist_ok=True)
    (uploads / ".gitkeep").touch()

    print(f"Copied {n} files")

    # OpenAPI
    spec = fetch_openapi()
    (DOCS / "openapi.json").write_text(json.dumps(spec, ensure_ascii=False, indent=2), encoding="utf-8")
    (DOCS / "API.md").write_text(gen_api_md(spec), encoding="utf-8")

    # Docs
    (DOCS / "FEATURES.md").write_text(gen_features_md(), encoding="utf-8")
    (DOCS / "DATABASE.md").write_text(gen_database_md(), encoding="utf-8")
    (DOCS / "DEPLOY.md").write_text(gen_deploy_md(), encoding="utf-8")

    print("Generating screenshots...")
    captured = try_capture_screenshots()
    if not captured:
        captured = try_generate_png_screenshots()
    if not captured:
        create_placeholder_screenshots()
    shot_ext = "png" if captured else "svg"
    (DOCS / "SCREENSHOTS.md").write_text(gen_screenshots_md(use_svg=not captured), encoding="utf-8")
    (RELEASE / "README.md").write_text(gen_readme(screenshot_ext=shot_ext), encoding="utf-8")

    user_guide = ROOT / "docs" / "功能使用说明.md"
    if user_guide.exists():
        shutil.copy2(user_guide, DOCS / "功能使用说明.md")

    (DOCS / "CONTRIBUTING.md").write_text(
        """# 贡献指南

1. Fork 本仓库
2. 创建特性分支 `git checkout -b feature/xxx`
3. 提交前运行验收脚本（见 DEPLOY.md）
4. 提交 PR 并描述变更范围

## 代码规范

- 后端：与现有 FastAPI 路由风格一致，模型字段 snake_case
- 前端：Vue 3 Composition API，Element Plus 组件
- 演示数据使用中性地名（示范县/示范市），勿提交真实隐私
""",
        encoding="utf-8",
    )

    (DOCS / "CHANGELOG.md").write_text(
        f"""# 更新日志

## [1.0.0] - {datetime.now().strftime('%Y-%m-%d')}

### 新增
- 双门户渔业监管平台完整开源版
- 70 张数据表 + 种子数据 + 幂等迁移
- 全菜单 API 验收脚本 accept_full.py
- 数据库/schema/编辑按钮审计脚本
- 尾水计划草稿编辑、用户管理修复、CrudPage 编辑白名单

### 文档
- API.md、FEATURES.md、DATABASE.md、DEPLOY.md
- OpenAPI JSON 导出
""",
        encoding="utf-8",
    )

    (RELEASE / "LICENSE").write_text(gen_license(), encoding="utf-8")
    (RELEASE / ".gitignore").write_text(gen_gitignore(), encoding="utf-8")

    # 统计
    total = sum(1 for _ in RELEASE.rglob("*") if _.is_file())
    size_mb = sum(f.stat().st_size for f in RELEASE.rglob("*") if f.is_file()) / 1024 / 1024

    manifest = RELEASE / "MANIFEST.txt"
    manifest.write_text(
        f"Package: shuzhi-fishery-platform\n"
        f"Built: {datetime.now().isoformat()}\n"
        f"Files: {total}\n"
        f"Size: {size_mb:.2f} MB\n"
        f"Path: {RELEASE}\n",
        encoding="utf-8",
    )

    print(f"\nDone: {RELEASE}")
    print(f"Files: {total}, Size: {size_mb:.2f} MB")
    print("Upload this folder to GitHub as a new repository.")


if __name__ == "__main__":
    main()
