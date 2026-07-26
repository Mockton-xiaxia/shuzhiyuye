# 数据库说明

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
uv run python ..\scripts\audit_db_schema.py
```

报告输出：`docs/reports/数据库全量检查.md`（打包时复制）

## 配置

复制 `backend/.env.example` 为 `.env`，**务必修改** `JWT_SECRET`。
