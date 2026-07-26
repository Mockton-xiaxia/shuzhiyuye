# 部署指南

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
uv run python ..\scripts\accept_full.py
uv run python ..\scripts\smoke_edit.py
uv run python ..\scripts\audit_db_schema.py
uv run python ..\scripts\audit_edit_buttons.py
```
