# 功能截图

> 路径：`docs/screenshots/`（真实页面截图 · PNG · GitHub 可直接预览）  
> 演示账号见 [功能使用说明.md](功能使用说明.md)：`gov_admin` / `ent_admin`，密码 `123456`

---

## 01 · 区县工作台（待办）

![区县工作台](screenshots/01-gov-workbench.png?v=20260726)

**模块**：工作台 → 待办列表  
**要点**：
- 待处理 / 全部待办统计卡片
- 标识申请审核等待办任务，支持「进入」「完成」
- 区县管理员门户首页，串联各业务模块入口

---

## 02 · 领导驾驶舱（区县大屏）

![领导驾驶舱](screenshots/02-gov-cockpit.png?v=20260726)

**模块**：工作台 → 领导驾驶舱  
**要点**：
- 区县渔业总体情况大屏（养殖主体、面积、物联设备、视频监控 KPI）
- 天地图底图 + 乡镇/社区点位下钻（杭州市西湖区演示坐标）
- 养殖品种面积排行、种苗数量、水产品产量/产值、设备类型、养殖模式等图表
- 底栏菜单：首页、生产记录（已移除演示用「数字孪生」入口）

---

## 03 · GIS 塘口信息采集

![GIS 塘口](screenshots/03-gis-pond-collect.png?v=20260726)

**模块**：主体资源 → 塘口信息采集  
**要点**：
- 已审要素 / 待审核 / 面积 / 品种统计
- OpenLayers 地图：养殖区测绘、尾水区、出水口打点、测距
- GeoJSON 导入/模板下载、图层开关、详情面板与提交审核

---

## 04 · 质量安全 · 政策管理

![政策管理](screenshots/04-quality-policy.png?v=20260726)

**模块**：质量安全 → 政策管理  
**要点**：
- 标准 CRUD 列表（查询 / 新增 / 导入 / 导出 / 批量删除）
- 政策名称、附件、发布日期维护
- 查看 / 编辑 / 删除操作

---

## 05 · 追溯标识 · 统计查询

![标识统计](screenshots/05-trace-stats.png?v=20260726)

**模块**：追溯标识 → 标识统计查询  
**要点**：
- 按追溯标签码、主体筛选
- 展示标签码、主体、品种、销售去向、生成日期、状态（BOUND 等）
- 支持导出与单条查看

---

## 06 · 视频设备 · 萤石云配置

![萤石云配置](screenshots/06-ezviz-config.png?v=20260726)

**模块**：视频设备 → 萤石云配置  
**要点**：
- 开放平台 AppKey / AppSecret 配置与连通测试
- 摄像头台账：序列号、通道、场景（WAREHOUSE / POND）、所属企业
- 资源池划分、测播、删除

---

## 07 · 产业资讯 · 装备供应

![装备供应](screenshots/07-supply-equipment.png?v=20260726)

**模块**：产业资讯 → 装备供应  
**要点**：
- 标题 / 品牌筛选，新增 / 导入 / 导出
- 供应商、联系人、区域、价格等字段
- 同类页面：苗种供应、饲料供应、渔药供应、行情采集

---

## 08 · 大鲵专项 · 育种驯化统计

![育种驯化](screenshots/08-domestication-stats.png?v=20260726)

**模块**：大鲵专项 → 育种驯化管理  
**要点**：
- 库存总量、今日投放、驯化成功率、待处理事项 KPI
- 纯稻 vs 渔稻共生经济效益对比（表格 + 柱状图）
- 稻田管理 / 渔稻生产 / 经济效益统计 Tab 切换

---

## 截图与源码对应

| 截图 | 前端路由/页面 | 后端 API（示例） |
|------|---------------|----------------|
| 工作台 | `/gov/workbench` | `/api/v1/todos` |
| 驾驶舱 | `/gov/cockpit` | `/api/v1/analytics/cockpit` |
| GIS 塘口 | `/gov/party/gis` | `/api/v1/party/gis/layers` |
| 政策管理 | CrudPage 配置页 | `/api/v1/quality/policies` |
| 标识统计 | `/gov/trace/stats` | `/api/v1/trace/codes` |
| 萤石云 | `/gov/iot/ezviz` | `/api/v1/iot/ezviz/*` |
| 装备供应 | CrudPage `supply` | `/api/v1/supply/listings` |
| 育种驯化 | `/gov/specialty/domestication` | `/api/v1/specialty/*` |

> 重新截取：`uv run python scripts/_capture_release_screenshots.py`（需前后端已启动 + Playwright）
