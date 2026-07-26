# 数智渔业平台 · 开源版

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-green.svg)](backend/)
[![Vue 3](https://img.shields.io/badge/vue-3.x-brightgreen.svg)](frontend/)

面向 **区县监管** 与 **企业生产** 的双门户渔业数字化管理平台。  
覆盖工作台待办、领导驾驶舱、GIS 塘口、质量安全、追溯标识、尾水监管、物联视频、产业资讯、大鲵专项等完整业务链，**开箱可跑、可验收、可二次开发**。

---

## 这是什么？

| 维度 | 说明 |
|------|------|
| **定位** | 区县渔业主管部门 + 养殖企业 一体化监管与生产平台（演示/开源参考实现） |
| **门户** | **GOV 区县端**（审核、备案、统计） + **ENT 企业端**（生产、仓储、物联、销售） |
| **数据** | 70+ 张业务表、内置演示种子数据、启动自动幂等迁移 |
| **地图** | 演示区划为 **浙江省杭州市西湖区**，驾驶舱/GIS 已对齐真实坐标与 GeoJSON |
| **扩展** | 通用 CRUD（`features.json` 配置驱动）+ 专用 API + `feature/update` 兜底 |

### 演示账号

| 用户名 | 密码 | 门户 | 说明 |
|--------|------|------|------|
| `gov_admin` | `123456` | 区县 GOV | 工作台、审核、驾驶舱、GIS 审核 |
| `ent_admin` | `123456` | 企业 ENT | 生产、塘口采集、整改回复、销售 |

> 详细操作步骤见 **[docs/功能使用说明.md](docs/功能使用说明.md)**

---

## 功能预览（真实截图）

### 监管指挥 · 工作台 & 大屏

<table>
  <tr>
    <td width="50%" align="center">
      <b>区县工作台 · 待办驱动</b><br/>
      <img src="docs/screenshots/01-gov-workbench.png?v=20260726" width="100%" alt="区县工作台"/>
      <br/><sub>待办统计、标识审核等待办任务，一键进入业务页面</sub>
    </td>
    <td width="50%" align="center">
      <b>领导驾驶舱 · 区县大屏</b><br/>
      <img src="docs/screenshots/02-gov-cockpit.png?v=20260726" width="100%" alt="领导驾驶舱"/>
      <br/><sub>KPI 指标、乡镇下钻、品种排行、设备与养殖模式分析</sub>
    </td>
  </tr>
</table>

### 空间监管 · GIS 塘口

<table>
  <tr>
    <td align="center">
      <b>塘口信息采集 / 审核 / 统计</b><br/>
      <img src="docs/screenshots/03-gis-pond-collect.png?v=20260726" width="100%" alt="GIS塘口"/>
      <br/><sub>OpenLayers 地图 · 养殖区/尾水区/出水口 · GeoJSON 导入 · 面积校验 · 提交审核</sub>
    </td>
  </tr>
</table>

### 质量 · 追溯 · 视频

<table>
  <tr>
    <td width="50%" align="center">
      <b>质量安全 · 政策管理</b><br/>
      <img src="docs/screenshots/04-quality-policy.png?v=20260726" width="100%" alt="政策管理"/>
      <br/><sub>政策文件 CRUD、附件、发布日期；同类还有抽检、整改、检测机构</sub>
    </td>
    <td width="50%" align="center">
      <b>追溯标识 · 统计查询</b><br/>
      <img src="docs/screenshots/05-trace-stats.png?v=20260726" width="100%" alt="标识统计"/>
      <br/><sub>标签码全生命周期查询、主体/品种/销售去向、导出</sub>
    </td>
  </tr>
  <tr>
    <td colspan="2" align="center">
      <b>萤石云 · 摄像头台账与企业划分</b><br/>
      <img src="docs/screenshots/06-ezviz-config.png?v=20260726" width="100%" alt="萤石云配置"/>
      <br/><sub>AppKey/Secret 配置、资源池划分、按企业分配、在线测播</sub>
    </td>
  </tr>
</table>

### 产业资讯 · 大鲵专项

<table>
  <tr>
    <td width="50%" align="center">
      <b>产业资讯 · 装备供应</b><br/>
      <img src="docs/screenshots/07-supply-equipment.png?v=20260726" width="100%" alt="装备供应"/>
      <br/><sub>苗种/饲料/渔药/装备/行情等供应信息发布与检索</sub>
    </td>
    <td width="50%" align="center">
      <b>大鲵专项 · 育种驯化统计</b><br/>
      <img src="docs/screenshots/08-domestication-stats.png?v=20260726" width="100%" alt="育种驯化"/>
      <br/><sub>库存/投放 KPI、纯稻 vs 渔稻共生经济效益对比图表</sub>
    </td>
  </tr>
</table>

> 全部截图与模块对照：[docs/SCREENSHOTS.md](docs/SCREENSHOTS.md)

---

## 核心功能一览

| 模块 | 区县端 (GOV) | 企业端 (ENT) |
|------|-------------|-------------|
| **工作台** | 待办列表、领导驾驶舱 | 生产首页、待办提醒 |
| **质量安全** | 政策/抽检/整改下发与复核 | 整改接收与回复、自检 |
| **追溯标识** | 标识审核、分发、统计查询 | 标识申请、绑定、扫码追溯 |
| **尾水监管** | 排放水域、计划备案、巡检调度 | 计划填报、巡检记录 |
| **主体 & GIS** | 主体审核、塘口审核、资源统计 | 主体自维护、塘口地图采集 |
| **养殖生产** | 渔业资源统计 | 批次、农事、出塘、休药期校验 |
| **物联视频** | 萤石云配置、摄像头划分 | 水质监测、设备告警 |
| **仓储销售** | — | 投入品、库存、订单、账本 |
| **产业资讯** | 资讯/供应/行情维护 | 浏览与对接 |
| **大鲵专项** | 驯化/检测统计 | 驯化生产记录 |

完整模块说明：[docs/FEATURES.md](docs/FEATURES.md) · 操作手册：[docs/功能使用说明.md](docs/功能使用说明.md)

---

## 快速开始

```powershell
# 1) 后端（Python 3.11+，推荐 uv）
cd backend
uv sync
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000

# 2) 前端（Node 20+，另开终端）
cd frontend/apps/admin
npm install
npm run dev
```

| 访问地址 | 说明 |
|----------|------|
| http://localhost:5173 | 管理端（登录后选 GOV/ENT 菜单） |
| http://localhost:8000/docs | Swagger API 文档 |

**Docker**（可选）：`docker compose up -d --build` → Web `8080` / API `8000`

---

## 技术栈

| 层 | 技术 |
|----|------|
| 后端 | FastAPI · SQLAlchemy 2 · JWT · Pydantic |
| 前端 | Vue 3 · Vite · Element Plus · Pinia · ECharts · OpenLayers |
| 数据库 | SQLite（开发零配置）/ PostgreSQL（生产） |

---

## 文档索引

| 文档 | 说明 |
|------|------|
| [docs/功能使用说明.md](docs/功能使用说明.md) | **功能使用说明（推荐先看）** |
| [docs/SCREENSHOTS.md](docs/SCREENSHOTS.md) | 截图索引与前后端路由对照 |
| [docs/FEATURES.md](docs/FEATURES.md) | 功能模块与页面类型 |
| [docs/API.md](docs/API.md) | 接口清单与认证 |
| [docs/DATABASE.md](docs/DATABASE.md) | 数据库表结构 |
| [docs/DEPLOY.md](docs/DEPLOY.md) | 部署与生产清单 |
| [docs/openapi.json](docs/openapi.json) | OpenAPI 3 规范 |

---

## 目录结构

```
backend/                 FastAPI 应用、模型、路由、种子与迁移
frontend/apps/admin/     Vue3 双门户管理端
scripts/                 accept_full 验收、审计、打包脚本
docs/                    文档与 screenshots/
docker-compose.yml       容器化部署
```

---

## 验收与贡献

```powershell
# 后端启动后，全菜单 API 冒烟
cd backend && uv run python ../scripts/accept_full.py
```

贡献指南见 [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md)

---

## 开源协议

[MIT License](LICENSE) — 可自由使用、修改与商用，请保留版权声明。

---

<p align="center"><sub>数智渔业平台开源版 · 2026</sub></p>
