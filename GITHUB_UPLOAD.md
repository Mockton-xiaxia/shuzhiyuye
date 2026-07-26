# GitHub 上传指南

本目录 `github-release/shuzhi-fishery-platform/` 为**可直接上传 GitHub 的完整开源包**。

## 包内内容

| 路径 | 说明 |
|------|------|
| `backend/` | FastAPI 后端源码 |
| `frontend/apps/admin/` | Vue3 管理端源码 |
| `scripts/` | 验收、审计、打包脚本 |
| `docs/API.md` | 接口文档（Markdown） |
| `docs/openapi.json` | OpenAPI 3 规范 |
| `docs/FEATURES.md` | 功能说明 |
| `docs/DATABASE.md` | 数据库说明 |
| `docs/DEPLOY.md` | 部署指南 |
| `docs/功能使用说明.md` | **功能使用说明（操作手册）** |
| `docs/SCREENSHOTS.md` | 功能截图索引 |
| `docs/screenshots/` | 功能截图（8 张真实 PNG，可直接预览） |
| `docs/reports/` | 验收与数据库检查报告 |
| `docs/design/` | 设计文档摘要 |
| `LICENSE` | MIT 开源协议 |
| `.gitignore` | Git 忽略规则 |

**已排除**：`node_modules`、`.venv`、`fishery.db`、`.env`、构建产物 `dist/`

## 方式一：GitHub 网页创建仓库

1. 登录 https://github.com/new
2. 仓库名建议：`shuzhi-fishery-platform` 或 `fishery-platform`
3. 选 **Public**，勾选 **Add a README** 可取消（本包已有）
4. 本地进入发布目录：

```powershell
cd d:\ai\domo\yuye\github-release\shuzhi-fishery-platform
git init
git add .
git commit -m "feat: 数智渔业平台开源初版 v1.0.0"
git branch -M main
git remote add origin https://github.com/<你的用户名>/<仓库名>.git
git push -u origin main
```

## 方式二：GitHub CLI

```powershell
cd d:\ai\domo\yuye\github-release\shuzhi-fishery-platform
git init && git add . && git commit -m "feat: 数智渔业平台开源初版 v1.0.0"
gh repo create shuzhi-fishery-platform --public --source=. --push
```

## 方式三：打 ZIP 上传

```powershell
Compress-Archive -Path "d:\ai\domo\yuye\github-release\shuzhi-fishery-platform\*" -DestinationPath "d:\ai\domo\yuye\github-release\shuzhi-fishery-platform.zip"
```

然后在 GitHub 仓库页 **Upload files** 上传（不推荐大仓库，建议用 git push）。

## 上传前检查

- [ ] 确认无 `.env`、无 `fishery.db`（本包已排除）
- [ ] README 中演示账号密码仅为演示用途
- [ ] 生产部署务必修改 `JWT_SECRET`

## 生成真实功能截图（可选）

启动前后端后：

```powershell
# 终端1
cd backend && uv run uvicorn app.main:app --port 8000

# 终端2
cd frontend/apps/admin && npm install && npm run dev

# 终端3
cd backend
uv pip install playwright
uv run playwright install chromium
uv run python ..\github-release\shuzhi-fishery-platform\scripts\_capture_screenshots.py
```

截图将写入 `docs/screenshots/*.png`，提交即可。

**无需 Node 时**（当前包已含演示 PNG），可重新生成：

```powershell
cd backend
uv run python ../scripts/generate_docs_screenshots.py --out ../github-release/shuzhi-fishery-platform/docs/screenshots
```

## 仓库描述建议（GitHub About）

**Description:** 数智渔业双门户监管平台 · FastAPI + Vue3 · 质量追溯/尾水/GIS/物联

**Topics:** `fishery` `aquaculture` `fastapi` `vue3` `gis` `traceability`

## 重新打包

在项目根目录执行：

```powershell
cd d:\ai\domo\yuye\backend
uv run python ..\scripts\build_github_release.py
```

输出目录：`github-release/shuzhi-fishery-platform/`
